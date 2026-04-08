"""
ChatKit server: multi-agent workflow powered by OpenAI Agents SDK.

Workflow (plan → loop → output):
  1. Plan Agent   – structured analysis (language, product line, which domains to query:
                    product / price / news, intent, recommendation hints)
  2. Loop         – for each selected domain, run a dedicated retrieval Agent
                    (product manual VS, price VS, or news VS; out-of-scope has no tools)
  3. Output Agent – merges all domain retrieval results into one streamed answer
  4. Recommendation – post-answer product card / lead-capture (unchanged)

Uses a custom ResponseStreamConverter to map file_citation → EntitySource,
enabling SPA navigation via the frontend entities.onClick handler.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from collections import defaultdict
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from agents import Agent, FileSearchTool, ModelSettings, Runner, RunConfig
from agents.items import MessageOutputItem
from pydantic import BaseModel, Field

from chatkit.agents import (
    AgentContext,
    ResponseStreamConverter,
    simple_to_agent_input,
    stream_agent_response,
)
from chatkit.actions import ActionConfig
from chatkit.server import ChatKitServer, stream_widget
from chatkit.store import NotFoundError, Store
from chatkit.types import (
    Annotation,
    Attachment,
    EntitySource,
    Page,
    ProgressUpdateEvent,
    ThreadItem,
    ThreadMetadata,
    ThreadStreamEvent,
    UserMessageItem,
    WidgetItem,
)
from chatkit.widgets import Card, Caption, Input, Label, Select, Spacer, Text, Title

from app.core.config import (
    LEADS_DIR,
    LLM_MODEL,
    OPENAI_VECTOR_STORE_AEGIS_ID,
    OPENAI_VECTOR_STORE_AEGIS_ULTRA_ID,
    OPENAI_VECTOR_STORE_FF91_ID,
    OPENAI_VECTOR_STORE_FUTURIST_ID,
    OPENAI_VECTOR_STORE_FUTURIST_ULTRA_ID,
    OPENAI_VECTOR_STORE_MASTER_ID,
    OPENAI_VECTOR_STORE_NEWS_ID,
    OPENAI_VECTOR_STORE_PRICE_ID,
    PUBLIC_BASE_URL,
    DEVELOPER_SIDEBAR_PATH,
    SIDEBAR_PATH,
)
from app.core.logging_config import FRONT_LOGGER_NAME
from app.services.lead_service import LeadStorage
from app.services.recommendation_catalog_service import RecommendationCatalogStorage
from app.services.recommendation_engine import RecommendationEngine

logger = logging.getLogger(__name__)
front_logger = logging.getLogger(FRONT_LOGGER_NAME)

# ── Paths ────────────────────────────────────────────────────────────────

INSTRUCTIONS_DIR = Path(__file__).parent / "instructions"


def _load_instructions(name: str) -> str:
    return (INSTRUCTIONS_DIR / f"{name}.md").read_text(encoding="utf-8")


# ── Image URL rewriting (ChatKit iframe can't resolve relative paths) ────

_MD_IMG_RE = re.compile(r"(!\[[^\]]*\]\()(/images/[^)]+)(\))")
_HTML_IMG_RE = re.compile(r"""(<img[^>]*\ssrc=["'])(/images/[^"']+)(["'])""")


def _rewrite_image_urls(text: str) -> str:
    """Convert relative /images/… paths to absolute URLs so that images
    render correctly inside the ChatKit iframe (hosted on cdn.platform.openai.com)."""
    if not PUBLIC_BASE_URL:
        return text
    text = _MD_IMG_RE.sub(rf"\g<1>{PUBLIC_BASE_URL}\2\3", text)
    text = _HTML_IMG_RE.sub(rf"\g<1>{PUBLIC_BASE_URL}\2\3", text)
    return text


def _compute_rewrite_offset(original_text: str, position: int) -> int:
    """Calculate how many extra characters URL rewriting inserts before *position*."""
    if not PUBLIC_BASE_URL:
        return 0
    offset = 0
    prefix_len = len(PUBLIC_BASE_URL)
    for pattern in (_MD_IMG_RE, _HTML_IMG_RE):
        for m in pattern.finditer(original_text):
            if m.start(2) < position:
                offset += prefix_len
    return offset


class _EventStreamRewriter:
    """Stateful processor that rewrites image URLs in text events **and**
    adjusts annotation character-position indices by the same offset so
    citations never land inside an expanded URL."""

    def __init__(self) -> None:
        self._text_buf: dict[tuple[str, int], str] = {}

    def process(self, event: ThreadStreamEvent) -> ThreadStreamEvent:
        if not PUBLIC_BASE_URL:
            return event

        if event.type in ("thread.item.added", "thread.item.done"):
            item = event.item
            if hasattr(item, "content") and isinstance(item.content, list):
                for part in item.content:
                    if hasattr(part, "text") and isinstance(part.text, str):
                        part.text = _rewrite_image_urls(part.text)

        elif event.type == "thread.item.updated":
            update = event.update

            if hasattr(update, "delta") and isinstance(update.delta, str):
                item_id = event.item_id
                ci = getattr(update, "content_index", 0)
                key = (item_id, ci)
                self._text_buf.setdefault(key, "")
                self._text_buf[key] += update.delta
                update.delta = _rewrite_image_urls(update.delta)

            if hasattr(update, "content") and hasattr(update.content, "text"):
                update.content.text = _rewrite_image_urls(update.content.text)

            if hasattr(update, "annotation"):
                ann = update.annotation
                if ann is not None and ann.index is not None:
                    item_id = event.item_id
                    ci = getattr(update, "content_index", 0)
                    key = (item_id, ci)
                    original = self._text_buf.get(key, "")
                    ann.index += _compute_rewrite_offset(original, ann.index)

        return event


# ── Triage output schema ─────────────────────────────────────────────────


class TriageOutput(BaseModel):
    input_lang: str
    query_scope: str
    # Primary product line (recommendations / legacy); use product_types for multi-manual routing.
    query_type: str
    product_types: list[str] = Field(default_factory=list)
    needs_product: str = "yes"
    needs_price: str = "no"
    needs_news: str = "no"
    query_text: str
    purchase_intent: str = "no"
    recommendation_hit: str = "no"
    recommendation_rule_id: str = ""


# ── Loop passes (server-built from Plan Agent output) ───────────────────


@dataclass(frozen=True)
class LoopPass:
    """One domain retrieval step: product, price, news, or out-of-scope guard."""

    domain: str  # "product" | "price" | "news" | "out-of-scope"
    vector_store_ids: list[str]
    focus_label: str
    product_key: str | None = None  # set when domain == "product" (manual routing)


@dataclass(frozen=True)
class RetrievedSource:
    """A cited document hit extracted from a loop pass."""

    kind: str
    filename: str
    title: str
    slug: str | None = None
    page_url: str | None = None
    url: str | None = None
    source_host: str | None = None
    published_at: str | None = None


@dataclass(frozen=True)
class LoopPassResult:
    """Normalized loop result passed downstream to the Output Agent."""

    domain: str
    focus_label: str
    product_key: str | None
    text: str
    sources: tuple[RetrievedSource, ...] = ()


# ── Agent definitions ────────────────────────────────────────────────────

_TRIAGE_MODEL_SETTINGS = ModelSettings(
    store=True,
)

_SUPPORT_MODEL_SETTINGS = ModelSettings(
    store=True,
    tool_choice="required",
)

_NO_TOOL_MODEL_SETTINGS = ModelSettings(
    store=True,
)

_TRIAGE_INSTRUCTIONS_TEMPLATE = _load_instructions("triage")

# Prepended to each product *.md in Loop **product** passes so the model behaves as a
# retrieval tool (file_search → excerpts). Downstream Output Agent writes the user-facing reply.
_PRODUCT_LOOP_RETRIEVAL_PREFIX = """## 当前轮次身份

你是当前轮次的**产品资料检索子模块**。你会调用 `file_search` 从绑定的产品资料库中取数，产出供下游 Output Agent 汇总的检索结果；你**不是**最终面向用户的回答模块。

## 当前轮次硬性要求

- 先使用 `{{query_text}}` 调用 `file_search`。
- 只基于当前命中的资料输出，不得补充外部知识。
- 输出要像“检索结果摘要 / 证据整理”，不要写成完整客服答复。
- 保留有价值的细节：参数、单位、日期、步骤、警告、限制条件、原文片段、图片 Markdown。
- 未命中时，简短说明“未检索到直接信息”并指出最接近的主题，不要输出长段道歉模板。
- 不要手动附加引用标记或来源链接，系统会处理来源展示。

## 输出结构

请严格使用下面四个标题输出，便于下游汇总：

### 结论
### 关键依据
### 细节摘录
### 缺失与不确定项

---

"""


def _build_plan_agent(
    recommendation_rules_prompt: str,
    purchase_intent_rules_prompt: str,
) -> Agent:
    instructions = _TRIAGE_INSTRUCTIONS_TEMPLATE.replace(
        "{{recommendation_rules}}", recommendation_rules_prompt
    ).replace(
        "{{purchase_intent_rules}}", purchase_intent_rules_prompt
    )
    return Agent(
        name="FF Robot Plan",
        instructions=instructions,
        model="gpt-5.4-mini",
        output_type=TriageOutput,
        model_settings=_TRIAGE_MODEL_SETTINGS,
    )

_SUPPORT_AGENT_CONFIGS: dict[str, dict] = {
    "master": {
        "name": "Master Support",
        "instructions_file": "master",
        "vector_store_id": OPENAI_VECTOR_STORE_MASTER_ID,
    },
    "futurist": {
        "name": "Futurist Support",
        "instructions_file": "futurist",
        "vector_store_id": OPENAI_VECTOR_STORE_FUTURIST_ID,
    },
    "futurist-ultra": {
        "name": "Futurist Ultra Support",
        "instructions_file": "futurist-ultra",
        "vector_store_id": OPENAI_VECTOR_STORE_FUTURIST_ULTRA_ID,
    },
    "aegis": {
        "name": "Aegis Support",
        "instructions_file": "aegis",
        "vector_store_id": OPENAI_VECTOR_STORE_AEGIS_ID,
    },
    "aegis-ultra": {
        "name": "Aegis Ultra Support",
        "instructions_file": "aegis-ultra",
        "vector_store_id": OPENAI_VECTOR_STORE_AEGIS_ULTRA_ID,
    },
    "ff91": {
        "name": "FF 91 2.0 Support",
        "instructions_file": "ff91",
        "vector_store_id": OPENAI_VECTOR_STORE_FF91_ID,
    },
    "out-of-scope": {
        "name": "Official Website Scope Guard",
        "instructions_file": "out-of-scope",
        "vector_store_id": "",
    },
}

# Pre-load instruction templates at module level (avoids repeated disk I/O).
_INSTRUCTION_TEMPLATES: dict[str, str] = {
    key: _load_instructions(cfg["instructions_file"])
    for key, cfg in _SUPPORT_AGENT_CONFIGS.items()
}

_VALID_PRODUCT_KEYS: frozenset[str] = frozenset(
    k for k in _SUPPORT_AGENT_CONFIGS if k not in ("out-of-scope",)
)


def _resolve_product_types(plan: TriageOutput) -> list[str]:
    """Ordered, deduped manual routes. No all-products vector — one store per product key."""
    ordered: list[str] = []
    seen: set[str] = set()
    for raw in plan.product_types:
        k = (raw or "").strip().lower()
        if k in _VALID_PRODUCT_KEYS and k not in seen:
            seen.add(k)
            ordered.append(k)
    if ordered:
        return ordered
    qt = (plan.query_type or "").strip().lower()
    if qt in _VALID_PRODUCT_KEYS:
        return [qt]
    if qt == "general":
        logger.warning(
            "Deprecated query_type=general (no all-products store); using master for manuals"
        )
        return ["master"]
    return []


def _plan_loop_passes(plan: TriageOutput) -> list[LoopPass]:
    """Build ordered domain passes: each product key → own pass; then price; then news."""
    if plan.query_scope == "out-of-scope" or plan.query_type == "out-of-scope":
        return [
            LoopPass(
                domain="out-of-scope",
                vector_store_ids=[],
                focus_label="out-of-scope",
            )
        ]

    passes: list[LoopPass] = []
    product_keys = _resolve_product_types(plan)

    if plan.needs_product == "yes":
        for pk in product_keys:
            cfg = _SUPPORT_AGENT_CONFIGS.get(pk)
            if not cfg:
                continue
            vs = (cfg.get("vector_store_id") or "").strip()
            if not vs:
                logger.warning(
                    "Skipping product pass: no vector_store_id configured for product key=%s",
                    pk,
                )
                continue
            passes.append(
                LoopPass(
                    domain="product",
                    vector_store_ids=[vs],
                    focus_label=f"product ({cfg['name']})",
                    product_key=pk,
                )
            )
        if not passes and plan.needs_product == "yes" and product_keys:
            logger.warning(
                "needs_product=yes but no product loop passes (check vector store env for keys=%s)",
                product_keys,
            )

    if plan.needs_price == "yes" and OPENAI_VECTOR_STORE_PRICE_ID:
        passes.append(
            LoopPass(
                domain="price",
                vector_store_ids=[OPENAI_VECTOR_STORE_PRICE_ID],
                focus_label="price",
            )
        )
    elif plan.needs_price == "yes" and not OPENAI_VECTOR_STORE_PRICE_ID:
        logger.warning("needs_price=yes but OPENAI_VECTOR_STORE_PRICE_ID is empty")

    if plan.needs_news == "yes" and OPENAI_VECTOR_STORE_NEWS_ID:
        passes.append(
            LoopPass(
                domain="news",
                vector_store_ids=[OPENAI_VECTOR_STORE_NEWS_ID],
                focus_label="news",
            )
        )
    elif plan.needs_news == "yes" and not OPENAI_VECTOR_STORE_NEWS_ID:
        logger.warning("needs_news=yes but OPENAI_VECTOR_STORE_NEWS_ID is empty")

    if not passes:
        for pk in product_keys:
            cfg = _SUPPORT_AGENT_CONFIGS.get(pk)
            if not cfg:
                continue
            vs = (cfg.get("vector_store_id") or "").strip()
            if vs:
                passes.append(
                    LoopPass(
                        domain="product",
                        vector_store_ids=[vs],
                        focus_label=f"product ({cfg['name']})",
                        product_key=pk,
                    )
                )
                break

    return passes


def _build_retrieval_focus_instructions(
    needs_price: str = "no",
    needs_news: str = "no",
) -> str:
    focus_lines: list[str] = []
    if needs_price == "yes":
        focus_lines.append(
            "- 当前问题涉及价格、报价或商业价格信息，优先参考价格资料中的直接表述。"
        )
    if needs_news == "yes":
        focus_lines.append(
            "- 当前问题涉及最近动态、新闻或产品状态，优先参考新闻/更新资料中与当前产品直接匹配且时间更新近的内容。"
        )
    if not focus_lines:
        return ""

    focus_lines.append(
        "- 如果多个资料库结果冲突，优先采用与当前产品最直接匹配、表述更明确、时间更新更近的资料。"
    )
    return "\n\n## 本轮检索重点\n" + "\n".join(focus_lines)


def _build_loop_domain_agent(plan: TriageOutput, loop_pass: LoopPass) -> Agent:
    """One domain Agent: product manual, price store, news store, or out-of-scope (no tools)."""
    domain = loop_pass.domain
    input_lang = plan.input_lang
    query_text = plan.query_text

    if domain == "out-of-scope":
        template = _INSTRUCTION_TEMPLATES["out-of-scope"]
        instructions = template.replace("{{input_lang}}", input_lang)
        instructions = instructions.replace("{{query_text}}", query_text)
        instructions += (
            "\n\n## 本轮任务\n"
            "你当前是**范围判定模块**（非最终面向用户的回答模块）。"
            "请继续按模板要求输出结构化中间结果，不要写成长段最终客服答复。"
        )
        return Agent(
            name="Official Website Scope Guard",
            instructions=instructions,
            model=LLM_MODEL,
            tools=[],
            model_settings=_NO_TOOL_MODEL_SETTINGS,
        )

    if domain == "product":
        pk = loop_pass.product_key
        if not pk or pk not in _VALID_PRODUCT_KEYS:
            raise ValueError(f"Invalid product_key on LoopPass: {pk!r}")
        cfg = _SUPPORT_AGENT_CONFIGS[pk]
        template = _INSTRUCTION_TEMPLATES[pk]
        instructions = (
            _PRODUCT_LOOP_RETRIEVAL_PREFIX.replace("{{input_lang}}", input_lang).replace(
                "{{query_text}}", query_text
            )
            + template.replace("{{input_lang}}", input_lang).replace("{{query_text}}", query_text)
        )
        instructions += _build_retrieval_focus_instructions(
            needs_price=plan.needs_price,
            needs_news=plan.needs_news,
        )
        instructions += (
            "\n\n## 本轮检索任务\n"
            "本次你作为**产品手册**检索模块运行（非最终回答模块）。"
            "请尽可能详细地提取与用户问题相关的信息，包括具体数据、参数、日期等细节。"
            "不需要格式化为最终回答，只需完整呈现检索到的相关内容。\n"
            f"检索焦点：{loop_pass.focus_label}"
        )
        return Agent(
            name=f"{cfg['name']} (product)",
            instructions=instructions,
            model=LLM_MODEL,
            tools=[FileSearchTool(vector_store_ids=loop_pass.vector_store_ids)],
            model_settings=_SUPPORT_MODEL_SETTINGS,
        )

    if domain == "price":
        instructions = (
            f"用户语言：{input_lang}（cn=中文，en=英文）。\n"
            f"检索查询（已扩写）：{query_text}\n\n"
            "## 本轮检索任务\n"
            "你是**价格资料**检索模块（非最终回答模块）。请从向量库中提取与价格、报价、费用、"
            "采购、commercial offer 相关的具体表述，包括数字、币种、条款、日期等。"
            "不需要格式化为最终用户回答。\n"
            f"检索焦点：{loop_pass.focus_label}\n\n"
            "## 输出结构\n"
            "请严格按以下四个标题输出：\n"
            "### 结论\n"
            "### 关键依据\n"
            "### 细节摘录\n"
            "### 缺失与不确定项"
        )
        return Agent(
            name="Price Agent",
            instructions=instructions,
            model=LLM_MODEL,
            tools=[FileSearchTool(vector_store_ids=loop_pass.vector_store_ids)],
            model_settings=_SUPPORT_MODEL_SETTINGS,
        )

    if domain == "news":
        instructions = (
            f"用户语言：{input_lang}。\n"
            f"检索查询（已扩写）：{query_text}\n\n"
            "## 本轮检索任务\n"
            "你是**新闻/动态**检索模块（非最终回答模块）。请提取与问题相关的公告、更新、"
            "发布进展、时间线、最近状态等。不需要格式化为最终用户回答。\n"
            f"检索焦点：{loop_pass.focus_label}\n\n"
            "如果命中的新闻内容包含头部元数据（如 `source:`、`title:`、`published:`、`scraped_at:`），"
            "请务必把这些信息原样整理到输出里，尤其是外部新闻链接 `source`。\n\n"
            "## 输出结构\n"
            "请严格按以下四个标题输出：\n"
            "### 结论\n"
            "### 关键依据\n"
            "### 细节摘录\n"
            "### 缺失与不确定项\n\n"
            "在末尾追加 `### 来源信息` 小节，并严格输出下面的结构化块，便于系统抽取新闻来源：\n"
            "SOURCE_JSON_START\n"
            "[\n"
            '  {"title": "<新闻标题>", "url": "<新闻原始 URL>", "published_at": "<published 或 scraped_at>"}\n'
            "]\n"
            "SOURCE_JSON_END\n\n"
            "如果没有命中任何新闻来源，则输出空数组 `[]`。"
        )
        return Agent(
            name="News Agent",
            instructions=instructions,
            model=LLM_MODEL,
            tools=[FileSearchTool(vector_store_ids=loop_pass.vector_store_ids)],
            model_settings=_SUPPORT_MODEL_SETTINGS,
        )

    raise ValueError(f"Unknown loop domain: {domain!r}")


_OUTPUT_INSTRUCTIONS_TEMPLATE = _load_instructions("output")


def _build_output_agent(
    input_lang: str,
    user_query: str,
    retrieval_results: list[LoopPassResult],
) -> Agent:
    """Build the streamed output/synthesis agent that merges multi-pass results."""
    results_block = _render_loop_results_for_output(retrieval_results)
    source_catalog = _render_source_catalog(retrieval_results)

    instructions = _OUTPUT_INSTRUCTIONS_TEMPLATE.replace("{{input_lang}}", input_lang)
    instructions = instructions.replace("{{query_text}}", user_query)
    instructions = instructions.replace("{{retrieval_results}}", results_block)
    instructions = instructions.replace("{{source_catalog}}", source_catalog)

    return Agent(
        name="Output Synthesizer",
        instructions=instructions,
        model=LLM_MODEL,
        tools=[],
        model_settings=_NO_TOOL_MODEL_SETTINGS,
    )


# ── File name → slug mapping (for source navigation links) ──────────────


def _merge_sidebar_pages_into_map(
    all_sidebars: dict, result: dict[str, dict]
) -> None:
    for product_sidebar in all_sidebars.values():
        for section in product_sidebar.get("sections", []):
            for page in section.get("pages", []):
                entry = {
                    "slug": page["slug"],
                    "title": page["title"],
                }
                rel_path = page["file"]
                result[rel_path] = entry
                basename = rel_path.rsplit("/", 1)[-1]
                if basename != rel_path:
                    result.setdefault(basename, entry)


def _build_file_slug_map() -> dict[str, dict]:
    """Build {filename: {slug, title}} from sidebar.json and developer-sidebar.json.

    Indexes by both the full relative path (e.g. "master-ultra/foo.md")
    and the bare filename (e.g. "foo.md") so that OpenAI file_citation
    lookups succeed regardless of which form the API returns.
    """
    result: dict[str, dict] = {}

    try:
        with open(SIDEBAR_PATH, "r", encoding="utf-8") as f:
            _merge_sidebar_pages_into_map(json.load(f), result)
    except FileNotFoundError:
        logger.warning("sidebar.json not found at %s", SIDEBAR_PATH)

    try:
        with open(DEVELOPER_SIDEBAR_PATH, "r", encoding="utf-8") as f:
            _merge_sidebar_pages_into_map(json.load(f), result)
    except FileNotFoundError:
        logger.warning("developer-sidebar.json not found at %s", DEVELOPER_SIDEBAR_PATH)

    return result


FILE_SLUG_MAP = _build_file_slug_map()


def _lookup_page_info(filename: str) -> dict | None:
    """Resolve either a full relative path or bare filename to sidebar metadata."""
    page_info = FILE_SLUG_MAP.get(filename)
    if page_info:
        return page_info
    basename = filename.rsplit("/", 1)[-1]
    return FILE_SLUG_MAP.get(basename)


def _build_page_url(slug: str | None) -> str | None:
    if not slug:
        return None
    if not PUBLIC_BASE_URL:
        return slug
    return f"{PUBLIC_BASE_URL}{slug}"


def _extract_source_host(url: str | None) -> str | None:
    if not url:
        return None
    try:
        host = urlparse(url).netloc.strip().lower()
    except ValueError:
        return None
    return host or None


def _build_manual_source(filename: str, title: str, slug: str | None) -> RetrievedSource:
    return RetrievedSource(
        kind="manual",
        filename=filename,
        title=title,
        slug=slug,
        page_url=_build_page_url(slug),
    )


def _build_news_source(
    *,
    url: str,
    title: str,
    published_at: str | None = None,
) -> RetrievedSource:
    normalized_url = url.strip()
    return RetrievedSource(
        kind="news",
        filename=normalized_url,
        title=(title or normalized_url).strip(),
        url=normalized_url,
        source_host=_extract_source_host(normalized_url),
        published_at=(published_at or "").strip() or None,
    )


def _walk_json_like(value: Any):
    if isinstance(value, BaseModel):
        value = value.model_dump(exclude_unset=True)
    if isinstance(value, dict):
        yield value
        for nested in value.values():
            yield from _walk_json_like(nested)
        return
    if isinstance(value, list):
        for nested in value:
            yield from _walk_json_like(nested)


_LIKELY_MANUAL_KEYS = (
    "filename",
    "file_name",
    "file",
    "filepath",
    "path",
    "document",
    "document_name",
)
_LIKELY_TITLE_KEYS = ("title", "filename", "file_name", "document_name", "name")


def _extract_manual_sources_from_raw_item(raw_item: Any) -> tuple[RetrievedSource, ...]:
    """Best-effort fallback for FileSearch results when file_citation annotations are absent."""
    parsed: list[RetrievedSource] = []
    seen: set[tuple[str | None, str]] = set()

    for node in _walk_json_like(raw_item):
        if not isinstance(node, dict):
            continue

        title_hint = next(
            (
                str(node.get(key)).strip()
                for key in _LIKELY_TITLE_KEYS
                if isinstance(node.get(key), str) and str(node.get(key)).strip()
            ),
            "",
        )

        for key in _LIKELY_MANUAL_KEYS:
            value = node.get(key)
            if not isinstance(value, str):
                continue
            filename = value.strip()
            if not filename.endswith(".md"):
                continue
            page_info = _lookup_page_info(filename)
            if not page_info:
                continue
            slug = page_info.get("slug")
            title = page_info.get("title") or title_hint or filename.rsplit("/", 1)[-1]
            dedupe_key = (slug, filename)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            parsed.append(_build_manual_source(filename=filename, title=title, slug=slug))

    return tuple(parsed)


def _build_entity_annotation(
    *,
    title: str,
    slug: str | None,
    page_url: str | None,
    index: int,
) -> Annotation | None:
    if not slug:
        return None
    return Annotation(
        source=EntitySource(
            id=slug,
            title=title,
            interactive=True,
            data={
                "slug": slug,
                "pageUrl": page_url,
                "sourceType": "manual",
            },
        ),
        index=index,
    )


def _extract_retrieved_sources(run_result) -> tuple[RetrievedSource, ...]:
    """Pull deduped manual citations from a non-streamed loop run."""
    ordered: list[RetrievedSource] = []
    seen: set[tuple[str | None, str]] = set()

    def add_source(source: RetrievedSource) -> None:
        key = (source.slug, source.filename)
        if key in seen:
            return
        seen.add(key)
        ordered.append(source)

    for item in run_result.new_items:
        if not isinstance(item, MessageOutputItem):
            for source in _extract_manual_sources_from_raw_item(getattr(item, "raw_item", None)):
                add_source(source)
            continue

        for content in getattr(item.raw_item, "content", []):
            if getattr(content, "type", None) != "output_text":
                continue
            for annotation in getattr(content, "annotations", []):
                if getattr(annotation, "type", None) != "file_citation":
                    continue
                filename = (getattr(annotation, "filename", "") or "").strip()
                if not filename:
                    continue
                page_info = _lookup_page_info(filename)
                slug = page_info["slug"] if page_info else None
                title = page_info["title"] if page_info else filename.rsplit("/", 1)[-1]
                add_source(_build_manual_source(filename=filename, title=title, slug=slug))

        for source in _extract_manual_sources_from_raw_item(getattr(item, "raw_item", None)):
            add_source(source)

    return tuple(ordered)


_NEWS_SOURCE_LINE_RE = re.compile(
    r'^\s*[-*]?\s*(title|source|url|published|date|scraped_at)\s*:\s*(.+?)\s*$',
    re.IGNORECASE,
)
_NEWS_SOURCE_JSON_RE = re.compile(
    r"SOURCE_JSON_START\s*(?P<payload>\[.*?\]|\{.*?\})\s*SOURCE_JSON_END",
    re.DOTALL,
)


def _extract_news_sources_from_json_block(text: str) -> tuple[RetrievedSource, ...]:
    parsed: list[RetrievedSource] = []
    seen: set[str] = set()

    for match in _NEWS_SOURCE_JSON_RE.finditer(text):
        payload = match.group("payload").strip()
        try:
            records = json.loads(payload)
        except json.JSONDecodeError:
            logger.warning("Failed to parse SOURCE_JSON block in news result")
            continue
        if isinstance(records, dict):
            records = [records]
        if not isinstance(records, list):
            continue
        for record in records:
            if not isinstance(record, dict):
                continue
            url = str(record.get("url") or record.get("source") or "").strip()
            if not url or url in seen:
                continue
            seen.add(url)
            parsed.append(
                _build_news_source(
                    url=url,
                    title=str(record.get("title") or url).strip(),
                    published_at=str(
                        record.get("published_at")
                        or record.get("published")
                        or record.get("date")
                        or record.get("scraped_at")
                        or ""
                    ).strip()
                    or None,
                )
            )
    return tuple(parsed)


def _extract_news_sources_from_lines(text: str) -> tuple[RetrievedSource, ...]:
    """Parse line-oriented news metadata blocks emitted by the news loop agent."""
    records: list[dict[str, str]] = []
    current: dict[str, str] = {}

    def flush() -> None:
        nonlocal current
        if current.get("url"):
            records.append(current)
        current = {}

    for raw_line in text.splitlines():
        m = _NEWS_SOURCE_LINE_RE.match(raw_line)
        if not m:
            continue
        key = m.group(1).lower()
        value = m.group(2).strip().strip('"')
        if key == "title":
            if current.get("url") or current.get("title"):
                flush()
            current["title"] = value
        elif key in ("source", "url"):
            current["url"] = value
        elif key in ("published", "date", "scraped_at"):
            current["published_at"] = value
    flush()

    parsed: list[RetrievedSource] = []
    seen: set[str] = set()
    for record in records:
        url = (record.get("url") or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        parsed.append(
            _build_news_source(
                url=url,
                title=(record.get("title") or url).strip(),
                published_at=(record.get("published_at") or "").strip() or None,
            )
        )
    return tuple(parsed)


def _extract_news_sources_from_text(text: str) -> tuple[RetrievedSource, ...]:
    """Parse structured news source metadata from the news loop agent output."""
    return _merge_source_lists(
        _extract_news_sources_from_json_block(text),
        _extract_news_sources_from_lines(text),
    )


def _merge_source_lists(
    *source_groups: tuple[RetrievedSource, ...],
) -> tuple[RetrievedSource, ...]:
    merged: list[RetrievedSource] = []
    seen: set[tuple[str, str | None, str, str | None, str | None]] = set()
    for group in source_groups:
        for source in group:
            key = (source.kind, source.slug, source.filename, source.url, source.page_url)
            if key in seen:
                continue
            seen.add(key)
            merged.append(source)
    return tuple(merged)


def _merge_retrieved_sources(results: list[LoopPassResult]) -> tuple[RetrievedSource, ...]:
    """Flatten loop-pass sources into one ordered, deduped list."""
    return _merge_source_lists(*(result.sources for result in results))


def _format_sources_for_prompt(sources: tuple[RetrievedSource, ...]) -> str:
    if not sources:
        return "- 无明确文件来源"
    lines: list[str] = []
    for source in sources:
        if source.url:
            suffix = f" | published={source.published_at}" if source.published_at else ""
            host = f" | source={source.source_host}" if source.source_host else ""
            lines.append(f"- {source.title} | url={source.url}{host}{suffix}")
        elif source.page_url:
            lines.append(f"- {source.title} | page_url={source.page_url} | file={source.filename}")
        elif source.slug:
            lines.append(f"- {source.title} | slug={source.slug} | file={source.filename}")
        else:
            lines.append(f"- {source.title} ({source.filename}, 无页面映射)")
    return "\n".join(lines)


def _render_loop_results_for_output(results: list[LoopPassResult]) -> str:
    if not results:
        return "无检索结果。"
    blocks: list[str] = []
    for i, result in enumerate(results, start=1):
        product_key = result.product_key or "-"
        blocks.append(
            "\n".join(
                [
                    f"### 检索轮次 {i}",
                    f"- domain: {result.domain}",
                    f"- focus: {result.focus_label}",
                    f"- product_key: {product_key}",
                    "- sources:",
                    _format_sources_for_prompt(result.sources),
                    "",
                    result.text,
                ]
            )
        )
    return "\n\n".join(blocks)


def _render_source_catalog(results: list[LoopPassResult]) -> str:
    sources = _merge_retrieved_sources(results)
    if not sources:
        return "- 无可用来源"
    lines: list[str] = []
    for source in sources:
        extra = []
        extra.append(f"kind={source.kind}")
        if source.slug:
            extra.append(f"slug={source.slug}")
        if source.page_url:
            extra.append(f"page_url={source.page_url}")
        if source.url:
            extra.append(f"url={source.url}")
        if source.source_host:
            extra.append(f"source_host={source.source_host}")
        if source.published_at:
            extra.append(f"published={source.published_at}")
        extra_text = " | ".join(extra) if extra else "no-link"
        lines.append(f"- {source.title} | filename={source.filename} | {extra_text}")
    return "\n".join(lines)


def _is_displayable_source(source: RetrievedSource) -> bool:
    if source.url:
        return bool(source.title.strip() and source.url.strip())
    page_url = source.page_url or source.slug
    return bool(source.title.strip() and page_url and str(page_url).strip())


class _FinalSourceAppender:
    """Append one canonical source list to the final assistant message."""

    def __init__(self, sources: tuple[RetrievedSource, ...], input_lang: str) -> None:
        self._sources = tuple(source for source in sources if _is_displayable_source(source))
        self._input_lang = input_lang
        self._done = False

    def process(self, event: ThreadStreamEvent) -> ThreadStreamEvent:
        if self._done or not self._sources:
            return event
        if event.type != "thread.item.done":
            return event
        item = event.item
        if getattr(item, "type", None) != "assistant_message":
            return event

        text_part = next(
            (
                part
                for part in getattr(item, "content", [])
                if getattr(part, "type", None) == "output_text"
                and isinstance(getattr(part, "text", None), str)
            ),
            None,
        )
        if text_part is None:
            return event

        base_text = text_part.text.rstrip()
        header = "## 参考来源" if self._input_lang == "cn" else "## Sources"
        new_text = f"{base_text}\n\n{header}\n"
        annotations = list(getattr(text_part, "annotations", []) or [])

        for source in self._sources:
            if source.url:
                line = f"- [{source.title}]({source.url})"
                if source.source_host:
                    label = "来源" if self._input_lang == "cn" else "Source"
                    line += f" | {label}: {source.source_host}"
                if source.published_at:
                    label = "发布时间" if self._input_lang == "cn" else "Published"
                    line += f" | {label}: {source.published_at}"
                new_text += f"{line}\n"
                continue

            line_prefix = "- "
            title_index = len(new_text) + len(line_prefix)
            line = f"{line_prefix}{source.title}"
            page_url = source.page_url or source.slug
            if page_url:
                line += f" <{page_url}>"
            new_text += f"{line}\n"
            ann = _build_entity_annotation(
                title=source.title,
                slug=source.slug,
                page_url=source.page_url,
                index=title_index,
            )
            if ann is not None:
                annotations.append(ann)

        text_part.text = new_text.rstrip()
        text_part.annotations = annotations
        self._done = True
        return event


# ── Custom ResponseStreamConverter ───────────────────────────────────────


class FFRobotConverter(ResponseStreamConverter):
    """Override file_citation_to_annotation to produce EntitySource
    instead of the default FileSource, enabling SPA navigation via
    the frontend entities.onClick handler."""

    async def file_citation_to_annotation(self, file_citation) -> Annotation | None:
        filename = file_citation.filename
        logger.debug("file_citation filename=%r, index=%s", filename, file_citation.index)
        if not filename:
            return None

        page_info = _lookup_page_info(filename)
        if not page_info:
            logger.warning("No slug mapping for citation filename=%r", filename)
            return None

        return _build_entity_annotation(
            title=page_info["title"],
            slug=page_info["slug"],
            page_url=_build_page_url(page_info["slug"]),
            index=file_citation.index,
        )


# ── In-memory Store ──────────────────────────────────────────────────────


class InMemoryStore(Store[dict]):
    """Minimal in-memory store for development. Replace with a
    database-backed store (Postgres, MySQL, etc.) for production.
    """

    def __init__(self) -> None:
        self.threads: dict[str, ThreadMetadata] = {}
        self.items: dict[str, list[ThreadItem]] = defaultdict(list)
        self.agent_traces: dict[str, list[dict]] = defaultdict(list)
        self.thread_langs: dict[str, str] = {}

    async def load_thread(self, thread_id: str, context: dict) -> ThreadMetadata:
        if thread_id not in self.threads:
            raise NotFoundError(f"Thread {thread_id} not found")
        return self.threads[thread_id]

    async def save_thread(self, thread: ThreadMetadata, context: dict) -> None:
        is_new = thread.id not in self.threads
        self.threads[thread.id] = thread
        if is_new:
            front_logger.info("[thread=%s] new thread created", thread.id)

    async def load_threads(
        self, limit: int, after: str | None, order: str, context: dict
    ) -> Page[ThreadMetadata]:
        return self._paginate(
            list(self.threads.values()),
            after, limit, order,
            sort_key=lambda t: t.created_at,
            cursor_key=lambda t: t.id,
        )

    async def load_thread_items(
        self, thread_id: str, after: str | None, limit: int, order: str, context: dict
    ) -> Page[ThreadItem]:
        return self._paginate(
            self.items.get(thread_id, []),
            after, limit, order,
            sort_key=lambda i: i.created_at,
            cursor_key=lambda i: i.id,
        )

    async def add_thread_item(
        self, thread_id: str, item: ThreadItem, context: dict
    ) -> None:
        self.items[thread_id].append(item)
        item_type = type(item).__name__
        preview = ""
        if hasattr(item, "content") and isinstance(item.content, list):
            preview = " ".join(
                getattr(part, "text", "")[:80] for part in item.content[:2]
            ).strip()
        front_logger.debug(
            "[thread=%s] +item type=%s id=%s preview=%r",
            thread_id, item_type, getattr(item, "id", "?"), preview[:150],
        )

    async def save_item(
        self, thread_id: str, item: ThreadItem, context: dict
    ) -> None:
        items = self.items[thread_id]
        for idx, existing in enumerate(items):
            if existing.id == item.id:
                items[idx] = item
                return
        items.append(item)

    async def load_item(
        self, thread_id: str, item_id: str, context: dict
    ) -> ThreadItem:
        for item in self.items.get(thread_id, []):
            if item.id == item_id:
                return item
        raise NotFoundError(f"Item {item_id} not found in thread {thread_id}")

    async def delete_thread(self, thread_id: str, context: dict) -> None:
        self.threads.pop(thread_id, None)
        self.items.pop(thread_id, None)

    async def delete_thread_item(
        self, thread_id: str, item_id: str, context: dict
    ) -> None:
        self.items[thread_id] = [
            item for item in self.items.get(thread_id, []) if item.id != item_id
        ]

    def _paginate(
        self, rows: list, after: str | None, limit: int, order: str,
        sort_key, cursor_key,
    ):
        sorted_rows = sorted(rows, key=sort_key, reverse=order == "desc")
        start = 0
        if after:
            for idx, row in enumerate(sorted_rows):
                if cursor_key(row) == after:
                    start = idx + 1
                    break
        data = sorted_rows[start : start + limit]
        has_more = start + limit < len(sorted_rows)
        next_after = cursor_key(data[-1]) if has_more and data else None
        return Page(data=data, has_more=has_more, after=next_after)

    async def save_attachment(self, attachment: Attachment, context: dict) -> None:
        raise NotImplementedError()

    async def load_attachment(self, attachment_id: str, context: dict) -> Attachment:
        raise NotImplementedError()

    async def delete_attachment(self, attachment_id: str, context: dict) -> None:
        raise NotImplementedError()


# ── ChatKit Server ───────────────────────────────────────────────────────


class FFRobotChatKitServer(ChatKitServer[dict]):
    """Plan → Loop → Output multi-agent workflow with post-answer recommendations.

    1. **Plan Agent** (non-streamed): language, product line, domain flags
       (`needs_product` / `needs_price` / `needs_news`), query expansion.
    2. **Loop**: run **Product / Price / News** domain Agents (and out-of-scope
       guard when applicable); each pass uses one vector store. Non-streamed
       retrieval, then **Output Agent** streams the final answer.
    3. **Recommendation** (post-answer): product card or lead-capture widget.
    """

    def __init__(
        self,
        store: InMemoryStore,
        *,
        lead_storage: LeadStorage | None = None,
        recommendation_storage: RecommendationCatalogStorage | None = None,
    ) -> None:
        super().__init__(store=store)
        self._recommendation_storage = recommendation_storage or RecommendationCatalogStorage.from_config()
        self.reco_engine = RecommendationEngine(self._recommendation_storage)
        self._lead_storage = lead_storage or LeadStorage.from_config()

    # ── Widget builders ───────────────────────────────────────────────────

    @staticmethod
    def _build_reco_card(title: str, description: str) -> Card:
        return Card(children=[
            Title(value=title),
            Text(value=description),
        ])

    def _build_lead_card(self, title: str, description: str, lang: str) -> Card:
        is_cn = lang == "cn"
        return Card(
            asForm=True,
            children=[
                Title(value=title),
                Caption(value=description),
                Spacer(size="sm"),
                Label(
                    value="产品 / Product" if is_cn else "Product",
                    fieldName="product",
                ),
                Select(
                    name="product",
                    options=self.reco_engine.product_options,
                    defaultValue="aegis-ultra",
                ),
                Spacer(size="sm"),
                Label(
                    value="姓名 / Name" if is_cn else "Name",
                    fieldName="contact_name",
                ),
                Input(
                    name="contact_name",
                    placeholder="请输入姓名" if is_cn else "Your name",
                ),
                Spacer(size="sm"),
                Label(
                    value="邮箱 / Email" if is_cn else "Email",
                    fieldName="email",
                ),
                Input(
                    name="email",
                    placeholder="请输入邮箱" if is_cn else "Your email",
                ),
                Spacer(size="sm"),
                Label(
                    value="电话 / Phone" if is_cn else "Phone",
                    fieldName="phone",
                ),
                Input(
                    name="phone",
                    placeholder="请输入电话" if is_cn else "Your phone number",
                ),
            ],
            confirm={
                "label": "提交" if is_cn else "Submit",
                "action": ActionConfig(
                    type="submit_lead",
                    handler="server",
                    streaming=True,
                ),
            },
        )

    # ── Lead persistence ──────────────────────────────────────────────────

    def _save_lead(self, thread_id: str, payload: dict) -> None:
        self._lead_storage.save_lead(thread_id, payload)
        front_logger.info(
            "[thread=%s] lead captured: product=%s name=%s email=%s",
            thread_id,
            payload.get("product", ""),
            payload.get("contact_name", ""),
            payload.get("email", ""),
        )

    # ── Action handler (form submissions) ─────────────────────────────────

    async def action(
        self,
        thread: ThreadMetadata,
        action_obj: object,
        sender: WidgetItem | None,
        context: dict,
    ) -> AsyncIterator[ThreadStreamEvent]:
        action_type = getattr(action_obj, "type", "")
        action_payload = getattr(action_obj, "payload", {}) or {}

        if action_type == "submit_lead":
            self._save_lead(thread.id, action_payload)

            lang = self.store.thread_langs.get(thread.id, "en")
            success_title, success_text = self.reco_engine.lead_success_text(lang)

            success_card = Card(children=[
                Title(value=success_title),
                Text(value=success_text),
            ])
            async for ev in stream_widget(thread, success_card):
                yield ev
        else:
            logger.warning("Unknown action type=%r on thread=%s", action_type, thread.id)

    # ── Main respond flow ─────────────────────────────────────────────────

    async def respond(
        self,
        thread: ThreadMetadata,
        input_user_message: UserMessageItem | None,
        context: dict,
    ) -> AsyncIterator[ThreadStreamEvent]:
        history_page = await self.store.load_thread_items(
            thread.id, after=None, limit=100, order="asc", context=context
        )
        history_items: list[ThreadItem] = list(history_page.data)

        if input_user_message:
            already_in_history = any(
                item.id == input_user_message.id for item in history_items
            )
            if not already_in_history:
                history_items.append(input_user_message)

        user_text = ""
        if input_user_message and hasattr(input_user_message, "content"):
            user_text = " ".join(
                getattr(part, "text", "") for part in input_user_message.content
            ).strip()

        front_logger.info(
            "[thread=%s] user_message=%r  history_count=%d",
            thread.id, user_text[:200], len(history_items),
        )

        input_items = await simple_to_agent_input(history_items)

        agent_context = AgentContext(
            thread=thread,
            store=self.store,
            request_context=context,
        )

        # ── Phase 1: Plan Agent (non-streamed, structured JSON) ─────────
        yield ProgressUpdateEvent(icon="sparkle", text="Analyzing your question…")

        plan_agent = _build_plan_agent(
            self.reco_engine.build_triage_rules_prompt(),
            self.reco_engine.build_purchase_intent_prompt(),
        )
        logger.info("Running plan agent …")
        triage_result = await Runner.run(
            plan_agent,
            input_items,
            context=agent_context,
            run_config=RunConfig(
                trace_metadata={"__trace_source__": "agent-builder"},
            ),
        )

        triage_output: TriageOutput = triage_result.final_output
        front_logger.info(
            "[thread=%s] plan → query_scope=%s, query_type=%s, product_types=%s, "
            "input_lang=%s, needs_product=%s, needs_price=%s, needs_news=%s, purchase_intent=%s, "
            "recommendation_hit=%s, recommendation_rule_id=%s, query_text=%s",
            thread.id,
            triage_output.query_scope,
            triage_output.query_type,
            triage_output.product_types,
            triage_output.input_lang,
            triage_output.needs_product,
            triage_output.needs_price,
            triage_output.needs_news,
            triage_output.purchase_intent,
            triage_output.recommendation_hit,
            triage_output.recommendation_rule_id,
            triage_output.query_text[:120] if triage_output.query_text else "",
        )

        self.store.thread_langs[thread.id] = triage_output.input_lang

        # ── Phase 2: Loop (domain agents) → Output ─────────────────────────

        loop_passes = _plan_loop_passes(triage_output)
        front_logger.info(
            "[thread=%s] loop → domain_passes=%d, resolved_product_keys=%s, details=%s",
            thread.id,
            len(loop_passes),
            _resolve_product_types(triage_output),
            [
                (p.domain, p.focus_label, p.product_key, p.vector_store_ids)
                for p in loop_passes
            ],
        )

        retrieval_conversation = list(input_items)
        for i in range(len(retrieval_conversation) - 1, -1, -1):
            item = retrieval_conversation[i]
            if isinstance(item, dict) and item.get("role") == "user":
                retrieval_conversation[i] = {
                    "role": "user",
                    "content": triage_output.query_text,
                }
                break
        output_conversation = list(input_items)

        plan_trace_node = {
            "agent": plan_agent.name,
            "model": "gpt-5.4-mini",
            "role": "plan",
            "output": {
                "query_scope": triage_output.query_scope,
                "query_type": triage_output.query_type,
                "product_types": triage_output.product_types,
                "input_lang": triage_output.input_lang,
                "needs_product": triage_output.needs_product,
                "needs_price": triage_output.needs_price,
                "needs_news": triage_output.needs_news,
                "purchase_intent": triage_output.purchase_intent,
                "recommendation_hit": triage_output.recommendation_hit,
                "recommendation_rule_id": triage_output.recommendation_rule_id,
                "query_text": triage_output.query_text,
            },
        }

        rewriter = _EventStreamRewriter()
        retrieval_results: list[LoopPassResult] = []

        for pass_idx, pass_info in enumerate(loop_passes):
            if pass_info.domain == "out-of-scope":
                progress_text = "Preparing a scoped response…"
            elif pass_info.domain == "product":
                progress_text = f"Searching product manual ({pass_info.focus_label})…"
            elif pass_info.domain == "price":
                progress_text = "Searching price catalog…"
            else:
                progress_text = "Searching news & updates…"

            yield ProgressUpdateEvent(
                icon="search",
                text=f"({pass_idx + 1}/{len(loop_passes)}) {progress_text}",
            )
            front_logger.info(
                "[thread=%s] loop %d/%d → domain=%s focus=%s vector_store_ids=%s",
                thread.id,
                pass_idx + 1,
                len(loop_passes),
                pass_info.domain,
                pass_info.focus_label,
                pass_info.vector_store_ids,
            )

            domain_agent = _build_loop_domain_agent(triage_output, pass_info)
            pass_result = await Runner.run(
                domain_agent,
                retrieval_conversation,
                context=agent_context,
                run_config=RunConfig(
                    trace_metadata={"__trace_source__": "agent-builder"},
                ),
            )

            pass_text = pass_result.final_output
            if not isinstance(pass_text, str):
                pass_text = str(pass_text)

            pass_sources = _extract_retrieved_sources(pass_result)
            if pass_info.domain == "news":
                pass_sources = _merge_source_lists(
                    pass_sources,
                    _extract_news_sources_from_text(pass_text),
                )
            retrieval_results.append(
                LoopPassResult(
                    domain=pass_info.domain,
                    focus_label=pass_info.focus_label,
                    product_key=pass_info.product_key,
                    text=pass_text,
                    sources=pass_sources,
                )
            )
            front_logger.info(
                "[thread=%s] loop pass %d done → result_length=%d source_count=%d",
                thread.id,
                pass_idx + 1,
                len(pass_text),
                len(pass_sources),
            )

        yield ProgressUpdateEvent(icon="sparkle", text="Synthesizing answer…")
        front_logger.info(
            "[thread=%s] output agent → synthesizing %d domain results",
            thread.id,
            len(retrieval_results),
        )

        output_agent = _build_output_agent(
            triage_output.input_lang,
            user_text,
            retrieval_results,
        )
        final_sources = _merge_retrieved_sources(retrieval_results)
        source_appender = _FinalSourceAppender(final_sources, triage_output.input_lang)

        output_result = Runner.run_streamed(
            output_agent,
            output_conversation,
            context=agent_context,
            run_config=RunConfig(
                trace_metadata={"__trace_source__": "agent-builder"},
            ),
        )

        async for event in stream_agent_response(
            agent_context, output_result, converter=FFRobotConverter()
        ):
            event = rewriter.process(event)
            yield source_appender.process(event)

        self.store.agent_traces[thread.id].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_message": user_text[:300],
            "workflow": "plan-loop-output",
            "plan": {
                "domains": [p.domain for p in loop_passes],
                "details": [
                    (p.domain, p.focus_label, p.product_key, p.vector_store_ids)
                    for p in loop_passes
                ],
            },
            "nodes": [
                plan_trace_node,
                *[
                    {
                        "agent": result.focus_label,
                        "model": LLM_MODEL,
                        "role": "domain_retrieval",
                        "domain": result.domain,
                        "product_key": result.product_key,
                        "result_length": len(result.text),
                        "source_count": len(result.sources),
                        "sources": [source.title for source in result.sources],
                    }
                    for result in retrieval_results
                ],
                {
                    "agent": "Output Synthesizer",
                    "model": LLM_MODEL,
                    "role": "output",
                    "source_count": len(final_sources),
                },
            ],
        })

        # ── Phase 3: Post-answer recommendation ──────────────────────────
        reco = self.reco_engine.evaluate_post_answer(
            input_lang=triage_output.input_lang,
            thread_id=thread.id,
            recommendation_rule_id=triage_output.recommendation_rule_id,
            purchase_intent=triage_output.purchase_intent,
        )
        if reco:
            front_logger.info(
                "[thread=%s] recommendation id=%s type=%s",
                thread.id, reco.id, reco.reco_type,
            )
            if reco.reco_type == "lead_capture":
                card = self._build_lead_card(
                    reco.title, reco.description, triage_output.input_lang,
                )
            else:
                card = self._build_reco_card(reco.title, reco.description)

            async for ev in stream_widget(thread, card):
                yield ev


def create_chatkit_server(
    *,
    lead_storage: LeadStorage | None = None,
    recommendation_storage: RecommendationCatalogStorage | None = None,
) -> FFRobotChatKitServer:
    return FFRobotChatKitServer(
        store=InMemoryStore(),
        lead_storage=lead_storage,
        recommendation_storage=recommendation_storage,
    )
