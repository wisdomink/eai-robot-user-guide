"""Fast answer layer for preset FAQ hits and repeated-question memory.

This module deliberately avoids external services so the Docker image can run
on AWS without Redis/Qdrant in the first iteration. It provides a narrow
interface that can later be backed by a vector database without changing the
ChatKit workflow.
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

_HEADING_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
_QA_RE = re.compile(r"^###\s+([\d.]+)\s+(.+?)\s*$", re.MULTILINE)
_PATH_RE = re.compile(r"^\*\*(?:路径|Path)：?\*\*\s*`([^`]+)`\s*$", re.MULTILINE | re.IGNORECASE)
_WELCOME_RE = re.compile(
    r"^\*\*(?:欢迎语|Welcome message)：?\*\*\s*(.+?)\s*$",
    re.MULTILINE | re.IGNORECASE,
)
_PUNCT_RE = re.compile(r"[\s\W_]+", re.UNICODE)
_CJK_RE = re.compile(r"[\u3400-\u9fff]")
_SYNONYM_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("第一次", "首次"),
    ("初次", "首次"),
    ("启动", "开机"),
    ("开不了机", "不能开机"),
    ("无法开机", "不能开机"),
    ("不能开机", "不能开机"),
    ("开不了", "不能开"),
    ("无法", "不能"),
    ("没法", "不能"),
    ("不可以", "不能"),
    ("可不可以", "能否"),
    ("可以吗", "能否"),
    ("支持吗", "能否支持"),
    ("怎么弄", "如何设置"),
    ("怎么样", "如何"),
    ("怎么", "如何"),
    ("怎样", "如何"),
    ("咋", "如何"),
    ("有什么", "有哪些"),
    ("啥", "什么"),
    ("现在", "目前"),
    ("哪儿", "哪里"),
    ("在哪", "在哪里"),
    ("多久", "多长时间"),
    ("多长时候", "多长时间"),
    ("充多久", "充电多长时间"),
    ("价格多少", "价格是多少"),
    ("多少钱", "价格是多少"),
    ("售价", "价格"),
    ("差别", "区别"),
    ("不同", "区别"),
    ("跟", "和"),
    ("产品线", "产品"),
    ("预定", "预订"),
)
_STOPWORD_CHARS = "的了呢吗吧？?请"

_PRIVATE_OR_DYNAMIC_RE = re.compile(
    r"(订单|工单|退款状态|支付|账号|个人|联系方式|电话|邮箱|我的|剩余名额|当前名额|实时|"
    r"order|ticket|payment|account|email|phone|my\s+order|real[- ]?time)",
    re.IGNORECASE,
)
_HIGH_RISK_RE = re.compile(
    r"(电池|充电故障|维修|拆机|刹车|火灾|安全气囊|自动驾驶|儿童安全|高压|冒烟|进水|"
    r"battery|repair|brake|fire|airbag|autonomous|high voltage|smoke|water damage)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class PagePattern:
    raw: str
    host: str = ""
    path: str = ""
    wildcard: bool = False


@dataclass(frozen=True)
class PresetFAQ:
    faq_id: str
    section_title: str
    page_path: str
    welcome: str
    question: str
    answer: str
    normalized_question: str
    page_pattern: PagePattern
    language: str


@dataclass(frozen=True)
class FastAnswerMatch:
    answer: str
    answer_source: str
    score: float
    matched_question: str
    faq_id: str = ""
    section_title: str = ""


@dataclass
class AnswerMemoryRecord:
    normalized_question: str
    raw_question: str
    page_key: str
    answer: str
    answer_source: str
    thread_id: str
    created_at: str
    metadata: dict = field(default_factory=dict)


def detect_input_lang(text: str) -> str:
    return "cn" if _CJK_RE.search(text or "") else "en"


def normalize_question(text: str) -> str:
    text = (text or "").strip().lower()
    text = text.replace("？", "?").replace("，", ",").replace("。", ".")
    for source, target in _SYNONYM_REPLACEMENTS:
        text = text.replace(source, target)
    for char in _STOPWORD_CHARS:
        text = text.replace(char, "")
    return _PUNCT_RE.sub("", text)


def _char_ngrams(text: str, n: int = 2) -> set[str]:
    if not text:
        return set()
    if len(text) <= n:
        return {text}
    return {text[i : i + n] for i in range(0, len(text) - n + 1)}


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _containment(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / min(len(left), len(right))


def fuzzy_question_score(left: str, right: str) -> float:
    left_norm = normalize_question(left)
    right_norm = normalize_question(right)
    if not left_norm or not right_norm:
        return 0.0
    if left_norm == right_norm:
        return 1.0

    seq_score = SequenceMatcher(None, left_norm, right_norm).ratio()
    left_grams = _char_ngrams(left_norm)
    right_grams = _char_ngrams(right_norm)
    jaccard_score = _jaccard(left_grams, right_grams)
    containment_score = _containment(left_grams, right_grams)
    char_score = 0.0
    if min(len(left_norm), len(right_norm)) >= 5:
        left_chars = set(left_norm)
        right_chars = set(right_norm)
        char_score = (_jaccard(left_chars, right_chars) * 0.45) + (
            _containment(left_chars, right_chars) * 0.55
        )

    substring_score = 0.0
    shorter, longer = (
        (left_norm, right_norm)
        if len(left_norm) <= len(right_norm)
        else (right_norm, left_norm)
    )
    if len(shorter) >= 4 and shorter in longer:
        substring_score = min(0.96, 0.70 + (len(shorter) / len(longer)) * 0.30)

    ngram_score = (jaccard_score * 0.55) + (containment_score * 0.45)
    return max(seq_score, ngram_score, char_score, substring_score)


def _parse_page_pattern(raw: str) -> PagePattern:
    value = (raw or "*").strip()
    wildcard = value == "*" or value.endswith("/*")
    trimmed = value[:-2] if value.endswith("/*") else value

    if trimmed == "*":
        return PagePattern(raw=value, wildcard=True)

    if "://" not in trimmed and "." in trimmed.split("/", 1)[0]:
        trimmed_for_parse = f"https://{trimmed}"
    else:
        trimmed_for_parse = trimmed

    parsed = urlparse(trimmed_for_parse)
    host = (parsed.netloc or "").lower()
    path = parsed.path or "/"
    if not path.startswith("/"):
        path = f"/{path}"
    return PagePattern(raw=value, host=host, path=_normalize_path(path), wildcard=wildcard)


def _normalize_path(path: str) -> str:
    path = (path or "/").strip()
    if not path.startswith("/"):
        path = f"/{path}"
    if len(path) > 1:
        path = path.rstrip("/")
    return path.lower()


def page_key_from_url(page_url: str | None) -> str:
    if not page_url:
        return ""
    parsed = urlparse(page_url)
    host = (parsed.netloc or "").lower()
    path = _normalize_path(parsed.path or "/")
    return f"{host}{path}" if host else path


def _page_matches(pattern: PagePattern, page_url: str | None) -> bool:
    if pattern.raw == "*":
        return True
    if not page_url:
        return False

    parsed = urlparse(page_url)
    host = (parsed.netloc or "").lower()
    path = _normalize_path(parsed.path or "/")

    if pattern.wildcard:
        return path == pattern.path or path.startswith(pattern.path.rstrip("/") + "/")
    return path == pattern.path


def _page_match_rank(pattern: PagePattern) -> int:
    if pattern.raw == "*":
        return 0
    if pattern.wildcard:
        return 1
    return 2


def _extract_section_path(block: str) -> str:
    match = _PATH_RE.search(block)
    return match.group(1).strip() if match else "*"


def _extract_section_welcome(block: str) -> str:
    match = _WELCOME_RE.search(block)
    return match.group(1).strip() if match else ""


def parse_preset_faq_markdown(path: Path, *, language: str | None = None) -> list[PresetFAQ]:
    if not path.exists():
        logger.warning("Preset FAQ file not found: %s", path)
        return []

    text = path.read_text(encoding="utf-8")
    faq_language = language or detect_input_lang(text[:2000])
    headings = list(_HEADING_RE.finditer(text))
    faqs: list[PresetFAQ] = []

    for idx, heading in enumerate(headings):
        section_title = heading.group(1).strip()
        start = heading.end()
        end = headings[idx + 1].start() if idx + 1 < len(headings) else len(text)
        block = text[start:end].strip()
        if not block:
            continue

        page_path = _extract_section_path(block)
        welcome = _extract_section_welcome(block)
        qa_matches = list(_QA_RE.finditer(block))

        for q_idx, q_match in enumerate(qa_matches):
            qa_start = q_match.end()
            qa_end = qa_matches[q_idx + 1].start() if q_idx + 1 < len(qa_matches) else len(block)
            question_no = q_match.group(1).strip()
            question = q_match.group(2).strip()
            answer = block[qa_start:qa_end].strip()
            if not question or not answer:
                continue
            faqs.append(
                PresetFAQ(
                    faq_id=f"preset-{question_no}",
                    section_title=section_title,
                    page_path=page_path,
                    welcome=welcome,
                    question=question,
                    answer=answer,
                    normalized_question=normalize_question(question),
                    page_pattern=_parse_page_pattern(page_path),
                    language=faq_language,
                )
            )

    logger.info(
        "Loaded preset FAQ entries: count=%d language=%s path=%s",
        len(faqs), faq_language, path,
    )
    return faqs


def _infer_language_from_path(path: Path) -> str | None:
    name = path.name.lower()
    if "(cn)" in name or "中文" in name or "预置" in name:
        return "cn"
    if "(en)" in name or "english" in name or "preset" in name:
        return "en"
    return None


class AnswerMemoryStore:
    def __init__(
        self,
        path: Path,
        *,
        max_records: int = 2000,
        fuzzy_threshold: float = 0.90,
    ) -> None:
        self.path = path
        self.max_records = max_records
        self.fuzzy_threshold = fuzzy_threshold
        self.records: list[AnswerMemoryRecord] = []
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        loaded: list[AnswerMemoryRecord] = []
        for line in self.path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            try:
                loaded.append(AnswerMemoryRecord(**data))
            except TypeError:
                continue
        self.records = loaded[-self.max_records :]
        logger.info("Loaded answer memory records: count=%d path=%s", len(self.records), self.path)

    def find(self, raw_question: str, page_url: str | None) -> FastAnswerMatch | None:
        normalized = normalize_question(raw_question)
        if not normalized:
            return None
        page_key = page_key_from_url(page_url)

        best: tuple[float, AnswerMemoryRecord] | None = None
        for record in self.records:
            if page_key and record.page_key and record.page_key != page_key:
                continue
            if record.normalized_question == normalized:
                score = 1.0
            else:
                score = fuzzy_question_score(normalized, record.normalized_question)
            if score < self.fuzzy_threshold:
                continue
            if best is None or score > best[0]:
                best = (score, record)

        if not best:
            return None
        score, record = best
        return FastAnswerMatch(
            answer=record.answer,
            answer_source="memory_exact" if score == 1.0 else "memory_fuzzy",
            score=score,
            matched_question=record.raw_question,
        )

    def remember(
        self,
        *,
        raw_question: str,
        page_url: str | None,
        answer: str,
        answer_source: str,
        thread_id: str,
        metadata: dict | None = None,
    ) -> None:
        normalized = normalize_question(raw_question)
        answer = (answer or "").strip()
        if not normalized or not answer:
            return
        page_key = page_key_from_url(page_url)
        if not _is_cacheable_question(raw_question):
            return

        replacement = AnswerMemoryRecord(
            normalized_question=normalized,
            raw_question=raw_question.strip(),
            page_key=page_key,
            answer=answer,
            answer_source=answer_source,
            thread_id=thread_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            metadata=metadata or {},
        )

        self.records = [
            r for r in self.records
            if not (r.normalized_question == normalized and r.page_key == page_key)
        ]
        self.records.append(replacement)
        self.records = self.records[-self.max_records :]
        self._flush()

    def _flush(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = "\n".join(
            json.dumps(record.__dict__, ensure_ascii=False)
            for record in self.records[-self.max_records :]
        )
        self.path.write_text(payload + ("\n" if payload else ""), encoding="utf-8")


def _is_cacheable_question(question: str) -> bool:
    if _PRIVATE_OR_DYNAMIC_RE.search(question or ""):
        return False
    if _HIGH_RISK_RE.search(question or ""):
        return False
    return True


class FastAnswerService:
    def __init__(
        self,
        *,
        preset_faq_path: Path | None = None,
        preset_faq_paths: list[Path] | tuple[Path, ...] | None = None,
        memory_path: Path,
        enabled: bool = True,
        memory_enabled: bool = True,
        memory_max_records: int = 2000,
        preset_fuzzy_threshold: float = 0.82,
        memory_fuzzy_threshold: float = 0.90,
    ) -> None:
        self.enabled = enabled
        self.memory_enabled = memory_enabled
        self.preset_fuzzy_threshold = preset_fuzzy_threshold
        paths: list[Path] = []
        if preset_faq_paths:
            paths.extend(Path(p) for p in preset_faq_paths)
        elif preset_faq_path:
            paths.append(preset_faq_path)
        self.preset_faqs = []
        if enabled:
            for path in paths:
                self.preset_faqs.extend(
                    parse_preset_faq_markdown(
                        path,
                        language=_infer_language_from_path(path),
                    )
                )
        self.memory = (
            AnswerMemoryStore(
                memory_path,
                max_records=memory_max_records,
                fuzzy_threshold=memory_fuzzy_threshold,
            )
            if enabled and memory_enabled
            else None
        )

    def lookup(self, raw_question: str, *, page_url: str | None) -> FastAnswerMatch | None:
        if not self.enabled:
            return None
        start = time.perf_counter()
        match = self._lookup_preset(raw_question, page_url=page_url)
        if not match and self.memory:
            match = self.memory.find(raw_question, page_url=page_url)
        elapsed_ms = (time.perf_counter() - start) * 1000
        if match:
            logger.info(
                "Fast answer hit: source=%s score=%.3f faq_id=%s elapsed=%.1fms",
                match.answer_source, match.score, match.faq_id, elapsed_ms,
            )
        return match

    def remember(
        self,
        *,
        raw_question: str,
        page_url: str | None,
        answer: str,
        answer_source: str,
        thread_id: str,
        metadata: dict | None = None,
    ) -> None:
        if not self.enabled or not self.memory:
            return
        self.memory.remember(
            raw_question=raw_question,
            page_url=page_url,
            answer=answer,
            answer_source=answer_source,
            thread_id=thread_id,
            metadata=metadata,
        )

    def _lookup_preset(self, raw_question: str, *, page_url: str | None) -> FastAnswerMatch | None:
        normalized = normalize_question(raw_question)
        if not normalized:
            return None

        input_lang = detect_input_lang(raw_question)
        candidates = [
            faq
            for faq in self.preset_faqs
            if faq.language == input_lang and _page_matches(faq.page_pattern, page_url)
        ]
        if not candidates:
            candidates = [
                faq for faq in self.preset_faqs if _page_matches(faq.page_pattern, page_url)
            ]
        if not candidates:
            return None

        best: tuple[float, int, PresetFAQ] | None = None
        for faq in candidates:
            if faq.normalized_question == normalized:
                score = 1.0
            else:
                score = fuzzy_question_score(normalized, faq.normalized_question)
            if score < self.preset_fuzzy_threshold:
                continue
            language_rank = 1 if faq.language == input_lang else 0
            if best is None:
                best = (score, language_rank, faq)
                continue
            prev_score, prev_language_rank, prev_faq = best
            if score > prev_score:
                best = (score, language_rank, faq)
            elif score == prev_score and language_rank > prev_language_rank:
                best = (score, language_rank, faq)
            elif (
                score == prev_score
                and language_rank == prev_language_rank
                and _page_match_rank(faq.page_pattern) > _page_match_rank(prev_faq.page_pattern)
            ):
                best = (score, language_rank, faq)

        if not best:
            return None
        score, _, faq = best
        return FastAnswerMatch(
            answer=faq.answer,
            answer_source="preset_exact" if score == 1.0 else "preset_fuzzy",
            score=score,
            matched_question=faq.question,
            faq_id=faq.faq_id,
            section_title=faq.section_title,
        )
