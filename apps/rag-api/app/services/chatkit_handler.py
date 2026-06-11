"""
ChatKit server: multi-agent workflow powered by OpenAI Agents SDK.

Workflow (plan → loop → output → post-decision):
  1. Plan Agent        – generates an execution plan (loop_plan) with language detection,
                         product identification, domain routing, and query expansion
  2. Loop              – for each item in loop_plan, run a dedicated retrieval Agent
                         (product manual VS, price VS, news VS, or fallback)
  3. Output Agent      – merges all domain retrieval results into one streamed answer
  4. Post-Decision     – evaluates purchase intent and recommendation rule matching
  5. Recommendation    – post-answer product card / lead-capture widget

Uses a custom ResponseStreamConverter to map file_citation → EntitySource,
enabling SPA navigation via the frontend entities.onClick handler.
"""

from __future__ import annotations

import asyncio
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
    AssistantMessageContent,
    AssistantMessageItem,
    Attachment,
    EntitySource,
    Page,
    ProgressUpdateEvent,
    ThreadItemDoneEvent,
    ThreadItem,
    ThreadMetadata,
    ThreadStreamEvent,
    UserMessageItem,
    WidgetItem,
)
from chatkit.widgets import Card, Caption, Input, Label, Select, Spacer, Text, Title

from app.core.config import (
    LEADS_DIR,
    ANSWER_MEMORY_DATA_PATH,
    ANSWER_MEMORY_ENABLED,
    ANSWER_MEMORY_FUZZY_THRESHOLD,
    ANSWER_MEMORY_MAX_RECORDS,
    FAST_ANSWER_ENABLED,
    LOOP_PASS_MAX_CONCURRENCY,
    LOOP_PASS_TIMEOUT_SECONDS,
    LOOP_PROGRESS_HEARTBEAT_SECONDS,
    LLM_MODEL,
    OPENAI_VECTOR_STORE_AEGIS_ID,
    OPENAI_VECTOR_STORE_AEGIS_ULTRA_ID,
    OPENAI_VECTOR_STORE_FF91_ID,
    OPENAI_VECTOR_STORE_NAVI_ID,
    OPENAI_VECTOR_STORE_FUTURIST_ID,
    OPENAI_VECTOR_STORE_FUTURIST_ULTRA_ID,
    OPENAI_VECTOR_STORE_MASTER_ID,
    OPENAI_VECTOR_STORE_NEWS_ID,
    OPENAI_VECTOR_STORE_PRICE_ID,
    PRESET_FAQ_FUZZY_THRESHOLD,
    PRESET_FAQ_PATHS,
    PUBLIC_BASE_URL,
    SIDEBAR_PATH,
)
from app.core.logging_config import FRONT_LOGGER_NAME
from app.services.lead_service import LeadStorage
from app.services.recommendation_catalog_service import RecommendationCatalogStorage
from app.services.recommendation_engine import RecommendationEngine
from app.services.fast_answer_service import FastAnswerMatch, FastAnswerService, detect_input_lang

logger = logging.getLogger(__name__)
front_logger = logging.getLogger(FRONT_LOGGER_NAME)

# Legacy magic trigger – kept for reference only; detection now uses the x-ff-lead-capture header.
_LEAD_CAPTURE_TRIGGER_LEGACY = "\u200b\u200bFF_LEAD_CAPTURE\u200b\u200b"

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


# ── Plan output schema ───────────────────────────────────────────────────


class LoopPlanItem(BaseModel):
    """One step in the execution plan produced by the Plan Agent."""

    agent: str  # "product" | "price" | "news" | "fallback"
    product_key: str | None = None  # required when agent == "product"


class PlanOutput(BaseModel):
    input_lang: str  # "cn" | "en"
    query_text: str  # expanded retrieval query
    loop_plan: list[LoopPlanItem] = Field(default_factory=list)


class PostDecisionOutput(BaseModel):
    """Structured output from the Post-Decision Agent (after answer generation)."""

    purchase_intent: str = "no"  # "yes" | "no"
    recommendation_hit: str = "no"  # "yes" | "no"
    recommendation_rule_id: str = ""


# ── Loop passes (server-built from Plan Agent output) ───────────────────


@dataclass(frozen=True)
class LoopPass:
    """One domain retrieval step: product, price, news, or fallback guard."""

    domain: str  # "product" | "price" | "news" | "fallback"
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

_PLAN_MODEL_SETTINGS = ModelSettings(
    store=True,
)

_SUPPORT_MODEL_SETTINGS = ModelSettings(
    store=True,
    tool_choice="required",
)

_NO_TOOL_MODEL_SETTINGS = ModelSettings(
    store=True,
)

_PLAN_INSTRUCTIONS_TEMPLATE = _load_instructions("plan")
_PRICE_LOOP_TEMPLATE = _load_instructions("price-agent")
_NEWS_LOOP_TEMPLATE = _load_instructions("news-agent")

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
- 输出格式遵循下方产品资料模块自带的"输出格式"章节。

---

"""


def _build_plan_agent() -> Agent:
    return Agent(
        name="FF Robot Plan Agent",
        instructions=_PLAN_INSTRUCTIONS_TEMPLATE,
        model="gpt-5.4-mini",
        output_type=PlanOutput,
        model_settings=_PLAN_MODEL_SETTINGS,
    )

_SUPPORT_AGENT_CONFIGS: dict[str, dict] = {
    "master": {
        "name": "FF Master Product Agent",
        "instructions_file": "product-master",
        "vector_store_id": OPENAI_VECTOR_STORE_MASTER_ID,
    },
    "futurist": {
        "name": "FF Futurist Product Agent",
        "instructions_file": "product-futurist",
        "vector_store_id": OPENAI_VECTOR_STORE_FUTURIST_ID,
    },
    "futurist-ultra": {
        "name": "FF Futurist Ultra Product Agent",
        "instructions_file": "product-futurist-ultra",
        "vector_store_id": OPENAI_VECTOR_STORE_FUTURIST_ULTRA_ID,
    },
    "aegis": {
        "name": "FF Aegis Product Agent",
        "instructions_file": "product-aegis",
        "vector_store_id": OPENAI_VECTOR_STORE_AEGIS_ID,
    },
    "aegis-ultra": {
        "name": "FF Aegis Ultra Product Agent",
        "instructions_file": "product-aegis-ultra",
        "vector_store_id": OPENAI_VECTOR_STORE_AEGIS_ULTRA_ID,
    },
    "ff91": {
        "name": "FF 91 2.0 Product Agent",
        "instructions_file": "product-ff91",
        "vector_store_id": OPENAI_VECTOR_STORE_FF91_ID,
    },
    "navi": {
        "name": "FF NAVI Product Agent",
        "instructions_file": "product-navi",
        "vector_store_id": OPENAI_VECTOR_STORE_NAVI_ID,
    },
    "fallback": {
        "name": "Fallback Agent",
        "instructions_file": "fallback",
        "vector_store_id": "",
    },
}

# Pre-load instruction templates at module level (avoids repeated disk I/O).
_INSTRUCTION_TEMPLATES: dict[str, str] = {
    key: _load_instructions(cfg["instructions_file"])
    for key, cfg in _SUPPORT_AGENT_CONFIGS.items()
}

_VALID_PRODUCT_KEYS: frozenset[str] = frozenset(
    k for k in _SUPPORT_AGENT_CONFIGS if k not in ("fallback",)
)


_VALID_AGENT_TYPES: frozenset[str] = frozenset(("product", "price", "news", "fallback"))


def _build_loop_passes_from_plan(loop_plan: list[LoopPlanItem]) -> list[LoopPass]:
    """Map loop_plan items directly to LoopPass list with validation."""
    has_fallback = any(item.agent == "fallback" for item in loop_plan)
    has_others = any(item.agent != "fallback" for item in loop_plan)

    if has_fallback and has_others:
        logger.warning(
            "loop_plan contains fallback mixed with other agents; keeping only fallback"
        )
        return [LoopPass(domain="fallback", vector_store_ids=[], focus_label="fallback")]

    passes: list[LoopPass] = []

    for item in loop_plan:
        if item.agent not in _VALID_AGENT_TYPES:
            logger.warning("Unknown agent type in loop_plan: %r, skipping", item.agent)
            continue

        if item.agent == "product":
            pk = (item.product_key or "").strip().lower()
            if not pk or pk not in _VALID_PRODUCT_KEYS:
                logger.warning(
                    "product agent missing or invalid product_key=%r, skipping", item.product_key
                )
                continue
            cfg = _SUPPORT_AGENT_CONFIGS.get(pk)
            if not cfg:
                continue
            vs = (cfg.get("vector_store_id") or "").strip()
            if not vs:
                logger.warning(
                    "Skipping product pass: no vector_store_id configured for product key=%s", pk
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

        elif item.agent == "price":
            if OPENAI_VECTOR_STORE_PRICE_ID:
                passes.append(
                    LoopPass(
                        domain="price",
                        vector_store_ids=[OPENAI_VECTOR_STORE_PRICE_ID],
                        focus_label="price",
                    )
                )
            else:
                logger.warning("price agent requested but OPENAI_VECTOR_STORE_PRICE_ID is empty")

        elif item.agent == "news":
            if OPENAI_VECTOR_STORE_NEWS_ID:
                passes.append(
                    LoopPass(
                        domain="news",
                        vector_store_ids=[OPENAI_VECTOR_STORE_NEWS_ID],
                        focus_label="news",
                    )
                )
            else:
                logger.warning("news agent requested but OPENAI_VECTOR_STORE_NEWS_ID is empty")

        elif item.agent == "fallback":
            passes.append(
                LoopPass(domain="fallback", vector_store_ids=[], focus_label="fallback")
            )

    if not passes:
        logger.warning("loop_plan produced no valid passes; falling back to fallback")
        passes.append(
            LoopPass(domain="fallback", vector_store_ids=[], focus_label="fallback")
        )

    return passes


def _build_retrieval_focus_instructions(loop_plan: list[LoopPlanItem]) -> str:
    """Build contextual focus hints from the execution plan."""
    focus_lines: list[str] = []
    agents = {item.agent for item in loop_plan}
    if "price" in agents:
        focus_lines.append(
            "- 当前问题涉及价格、报价或商业价格信息，优先参考价格资料中的直接表述。"
        )
    if "news" in agents:
        focus_lines.append(
            "- 当前问题涉及最近动态、新闻或产品状态，优先参考新闻/更新资料中与当前产品直接匹配且时间更新近的内容。"
        )
    if not focus_lines:
        return ""

    focus_lines.append(
        "- 如果多个资料库结果冲突，优先采用与当前产品最直接匹配、表述更明确、时间更新更近的资料。"
    )
    return "\n\n## 本轮检索重点\n" + "\n".join(focus_lines)


def _build_loop_domain_agent(plan: PlanOutput, loop_pass: LoopPass) -> Agent:
    """One domain Agent: product manual, price store, news store, or fallback (no tools)."""
    domain = loop_pass.domain
    input_lang = plan.input_lang
    query_text = plan.query_text

    if domain == "fallback":
        template = _INSTRUCTION_TEMPLATES["fallback"]
        instructions = template.replace("{{input_lang}}", input_lang)
        instructions = instructions.replace("{{query_text}}", query_text)
        instructions += (
            "\n\n## 本轮任务\n"
            "你当前是**兜底结果整理模块**（非最终面向用户的回答模块）。"
            "当前轮次没有命中任何可执行的产品/价格/新闻检索域。"
            "请继续按模板要求输出结构化中间结果，不要写成长段最终客服答复。"
        )
        return Agent(
            name="Fallback Agent",
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
        instructions += _build_retrieval_focus_instructions(plan.loop_plan)
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
        instructions = _PRICE_LOOP_TEMPLATE.replace("{{input_lang}}", input_lang)
        instructions = instructions.replace("{{query_text}}", query_text)
        return Agent(
            name="FF Price Agent",
            instructions=instructions,
            model=LLM_MODEL,
            tools=[FileSearchTool(vector_store_ids=loop_pass.vector_store_ids)],
            model_settings=_SUPPORT_MODEL_SETTINGS,
        )

    if domain == "news":
        instructions = _NEWS_LOOP_TEMPLATE.replace("{{input_lang}}", input_lang)
        instructions = instructions.replace("{{query_text}}", query_text)
        return Agent(
            name="FF News Agent",
            instructions=instructions,
            model=LLM_MODEL,
            tools=[FileSearchTool(vector_store_ids=loop_pass.vector_store_ids)],
            model_settings=_SUPPORT_MODEL_SETTINGS,
        )

    raise ValueError(f"Unknown loop domain: {domain!r}")


_OUTPUT_INSTRUCTIONS_TEMPLATE = _load_instructions("output")
_POST_DECISION_INSTRUCTIONS_TEMPLATE = _load_instructions("post-decision")


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
        name="FF AI Output Agent",
        instructions=instructions,
        model=LLM_MODEL,
        tools=[],
        model_settings=_NO_TOOL_MODEL_SETTINGS,
    )


def _build_post_decision_agent(
    recommendation_rules_prompt: str,
    purchase_intent_rules_prompt: str,
    user_query: str,
    loop_plan: list[LoopPlanItem],
    retrieval_summary: str,
    answer_text: str,
) -> Agent:
    """Build the Post-Decision Agent that evaluates purchase intent and recommendation rules."""
    loop_plan_str = json.dumps([item.model_dump() for item in loop_plan], ensure_ascii=False)

    instructions = _POST_DECISION_INSTRUCTIONS_TEMPLATE.replace(
        "{{recommendation_rules}}", recommendation_rules_prompt
    ).replace(
        "{{purchase_intent_rules}}", purchase_intent_rules_prompt
    ).replace(
        "{{user_query}}", user_query
    ).replace(
        "{{loop_plan}}", loop_plan_str
    ).replace(
        "{{retrieval_summary}}", retrieval_summary[:3000]
    ).replace(
        "{{answer_text}}", answer_text[:3000]
    )

    return Agent(
        name="FF Post-Decision Agent",
        instructions=instructions,
        model="gpt-5.4-mini",
        output_type=PostDecisionOutput,
        model_settings=_PLAN_MODEL_SETTINGS,
    )


# ── File name → slug mapping (for source navigation links) ──────────────


def _build_file_slug_map() -> dict[str, dict]:
    """Build {filename: {slug, title}} from sidebar.json.

    Indexes by both the full relative path (e.g. "master-ultra/foo.md")
    and the bare filename (e.g. "foo.md") so that OpenAI file_citation
    lookups succeed regardless of which form the API returns.
    """
    try:
        with open(SIDEBAR_PATH, "r", encoding="utf-8") as f:
            all_sidebars = json.load(f)
    except FileNotFoundError:
        logger.warning("sidebar.json not found at %s", SIDEBAR_PATH)
        return {}

    result: dict[str, dict] = {}
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
    """Plan → Loop → Output → Post-Decision multi-agent workflow.

    1. **Plan Agent** (non-streamed): generates ``loop_plan`` — an ordered list of
       agent steps (product/price/news/fallback) with query expansion.
    2. **Loop**: run domain Agents per ``loop_plan`` item; each pass uses one
       vector store. Non-streamed retrieval.
    3. **Output Agent**: streams the final user-facing answer.
    4. **Post-Decision Agent** (non-streamed): evaluates purchase intent and
       recommendation rule matching based on the full context.
    5. **Recommendation**: product card or lead-capture widget.
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
        self.fast_answers = FastAnswerService(
            preset_faq_paths=PRESET_FAQ_PATHS,
            memory_path=ANSWER_MEMORY_DATA_PATH,
            enabled=FAST_ANSWER_ENABLED,
            memory_enabled=ANSWER_MEMORY_ENABLED,
            memory_max_records=ANSWER_MEMORY_MAX_RECORDS,
            preset_fuzzy_threshold=PRESET_FAQ_FUZZY_THRESHOLD,
            memory_fuzzy_threshold=ANSWER_MEMORY_FUZZY_THRESHOLD,
        )

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
                    value="名 / First Name" if is_cn else "First Name",
                    fieldName="firstName",
                ),
                Input(
                    name="firstName",
                    placeholder="请输入名" if is_cn else "Your first name",
                ),
                Spacer(size="sm"),
                Label(
                    value="姓 / Last Name" if is_cn else "Last Name",
                    fieldName="lastName",
                ),
                Input(
                    name="lastName",
                    placeholder="请输入姓" if is_cn else "Your last name",
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
            "[thread=%s] lead captured: product=%s firstName=%s lastName=%s email=%s",
            thread_id,
            payload.get("product", ""),
            payload.get("firstName", ""),
            payload.get("lastName", ""),
            payload.get("email", ""),
        )

    async def _stream_fast_answer(
        self,
        thread: ThreadMetadata,
        context: dict,
        match: FastAnswerMatch,
    ) -> AsyncIterator[ThreadStreamEvent]:
        item = AssistantMessageItem(
            id=self.store.generate_item_id("message", thread, context),
            thread_id=thread.id,
            created_at=datetime.now(),
            content=[AssistantMessageContent(text=match.answer)],
        )
        yield ThreadItemDoneEvent(item=item)

    async def _stream_fast_answer_recommendation(
        self,
        *,
        thread: ThreadMetadata,
        user_text: str,
        answer_text: str,
        input_lang: str,
        fast_match: FastAnswerMatch,
        agent_context: AgentContext,
        context: dict,
    ) -> AsyncIterator[ThreadStreamEvent]:
        """Run existing post-answer recommendation logic after a fast answer."""
        try:
            post_decision_agent = _build_post_decision_agent(
                recommendation_rules_prompt=self.reco_engine.build_triage_rules_prompt(),
                purchase_intent_rules_prompt=self.reco_engine.build_purchase_intent_prompt(),
                user_query=user_text,
                loop_plan=[],
                retrieval_summary=(
                    f"Fast answer source={fast_match.answer_source}; "
                    f"matched_question={fast_match.matched_question}"
                ),
                answer_text=answer_text,
            )
            post_decision_result = await Runner.run(
                post_decision_agent,
                [{"role": "user", "content": user_text}],
                context=agent_context,
                run_config=RunConfig(
                    trace_metadata={"__trace_source__": "agent-builder"},
                ),
            )
            post_decision: PostDecisionOutput = post_decision_result.final_output
        except Exception:
            logger.exception("Fast answer post-decision failed")
            post_decision = PostDecisionOutput()

        front_logger.info(
            "[thread=%s] fast post-decision → purchase_intent=%s, recommendation_hit=%s, "
            "recommendation_rule_id=%s",
            thread.id,
            post_decision.purchase_intent,
            post_decision.recommendation_hit,
            post_decision.recommendation_rule_id,
        )

        self.store.agent_traces[thread.id].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_message": user_text[:300],
            "workflow": "fast-answer",
            "page_url": str(context.get("page_url") or ""),
            "fast_answer": {
                "answer_source": fast_match.answer_source,
                "score": fast_match.score,
                "faq_id": fast_match.faq_id,
                "matched_question": fast_match.matched_question,
                "section_title": fast_match.section_title,
            },
            "nodes": [
                {
                    "agent": "Fast Answer Layer",
                    "model": "local",
                    "role": "fast_answer",
                    "answer_source": fast_match.answer_source,
                    "score": fast_match.score,
                },
                {
                    "agent": "FF Post-Decision Agent",
                    "model": "gpt-5.4-mini",
                    "role": "post-decision",
                    "output": post_decision.model_dump(),
                },
            ],
        })

        reco = self.reco_engine.evaluate_post_answer(
            input_lang=input_lang,
            thread_id=thread.id,
            recommendation_rule_id=post_decision.recommendation_rule_id,
            purchase_intent=post_decision.purchase_intent,
        )
        if not reco:
            return

        front_logger.info(
            "[thread=%s] fast recommendation id=%s type=%s",
            thread.id, reco.id, reco.reco_type,
        )
        if reco.reco_type == "lead_capture":
            card = self._build_lead_card(reco.title, reco.description, input_lang)
        else:
            card = self._build_reco_card(reco.title, reco.description)

        async for ev in stream_widget(thread, card):
            yield ev

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
            is_cn = lang == "cn"
            success_title, success_text = self.reco_engine.lead_success_text(lang)

            # Build a summary of submitted info so it persists in the chat history
            summary_lines: list = []

            product = str(action_payload.get("product") or "").strip()
            if product:
                product_label = self.reco_engine._product_label(product)
                summary_lines.append(
                    Text(value=f"{'产品 / Product' if is_cn else 'Product'}: {product_label}")
                )

            first_name = str(action_payload.get("firstName") or "").strip()
            last_name = str(action_payload.get("lastName") or "").strip()
            full_name = f"{first_name} {last_name}".strip()
            if full_name:
                summary_lines.append(
                    Text(value=f"{'姓名 / Name' if is_cn else 'Name'}: {full_name}")
                )

            email = str(action_payload.get("email") or "").strip()
            if email:
                summary_lines.append(Text(value=f"Email: {email}"))

            phone = str(action_payload.get("phone") or "").strip()
            if phone:
                summary_lines.append(
                    Text(value=f"{'电话 / Phone' if is_cn else 'Phone'}: {phone}")
                )

            success_card = Card(children=[
                Title(value=success_title),
                *summary_lines,
                Spacer(size="sm") if summary_lines else Text(value=""),
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
            "[thread=%s] user_message=%r  history_count=%d page_url=%r",
            thread.id, user_text[:200], len(history_items), str(context.get("page_url") or "")[:200],
        )

        agent_context = AgentContext(
            thread=thread,
            store=self.store,
            request_context=context,
        )

        page_url = str(context.get("page_url") or "")

        # ── Lead-capture shortcut (triggered by x-ff-lead-capture header from SDK) ──
        if context.get("lead_capture"):
            input_lang = self.store.thread_langs.get(thread.id, "en")
            reply_text = str(context.get("lead_reply_text") or "").strip()
            front_logger.info(
                "[thread=%s] lead_capture → reply_text=%r → streaming lead widget",
                thread.id, reply_text[:80] if reply_text else "",
            )
            # Stream optional AI reply text first (if configured and non-empty)
            if reply_text:
                text_item = AssistantMessageItem(
                    id=self.store.generate_item_id("message", thread, context),
                    thread_id=thread.id,
                    created_at=datetime.now(),
                    content=[AssistantMessageContent(text=reply_text)],
                )
                yield ThreadItemDoneEvent(item=text_item)
            reco = self.reco_engine._make_lead_capture(input_lang)
            self.reco_engine.record_shown(thread.id, "lead_capture")
            card = self._build_lead_card(reco.title, reco.description, input_lang)
            async for ev in stream_widget(thread, card):
                yield ev
            return

        fast_match = self.fast_answers.lookup(user_text, page_url=page_url)
        if fast_match:
            input_lang = detect_input_lang(user_text)
            self.store.thread_langs[thread.id] = input_lang
            yield ProgressUpdateEvent(icon="sparkle", text="Found a prepared answer.")
            async for event in self._stream_fast_answer(thread, context, fast_match):
                yield event
            async for event in self._stream_fast_answer_recommendation(
                thread=thread,
                user_text=user_text,
                answer_text=fast_match.answer,
                input_lang=input_lang,
                fast_match=fast_match,
                agent_context=agent_context,
                context=context,
            ):
                yield event
            return

        input_items = await simple_to_agent_input(history_items)

        # ── Phase 1: Plan Agent (non-streamed, structured JSON) ─────────
        yield ProgressUpdateEvent(icon="sparkle", text="Analyzing your question…")

        plan_agent = _build_plan_agent()
        logger.info("Running plan agent …")
        plan_result = await Runner.run(
            plan_agent,
            input_items,
            context=agent_context,
            run_config=RunConfig(
                trace_metadata={"__trace_source__": "agent-builder"},
            ),
        )

        plan_output: PlanOutput = plan_result.final_output
        front_logger.info(
            "[thread=%s] plan → input_lang=%s, loop_plan=%s, query_text=%s",
            thread.id,
            plan_output.input_lang,
            [item.model_dump() for item in plan_output.loop_plan],
            plan_output.query_text[:120] if plan_output.query_text else "",
        )

        self.store.thread_langs[thread.id] = plan_output.input_lang

        # ── Phase 2: Loop (domain agents) → Output ─────────────────────────

        loop_passes = _build_loop_passes_from_plan(plan_output.loop_plan)
        front_logger.info(
            "[thread=%s] loop → domain_passes=%d, details=%s",
            thread.id,
            len(loop_passes),
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
                    "content": plan_output.query_text,
                }
                break
        output_conversation = list(input_items)

        plan_trace_node = {
            "agent": plan_agent.name,
            "model": "gpt-5.4-mini",
            "role": "plan",
            "output": {
                "input_lang": plan_output.input_lang,
                "query_text": plan_output.query_text,
                "loop_plan": [item.model_dump() for item in plan_output.loop_plan],
            },
        }

        rewriter = _EventStreamRewriter()
        retrieval_results_by_idx: list[LoopPassResult | None] = [None] * len(loop_passes)
        loop_semaphore = asyncio.Semaphore(max(1, LOOP_PASS_MAX_CONCURRENCY))

        async def run_loop_pass(
            pass_idx: int,
            pass_info: LoopPass,
        ) -> tuple[int, LoopPassResult, Exception | None]:
            async with loop_semaphore:
                front_logger.info(
                    "[thread=%s] loop %d/%d → domain=%s focus=%s vector_store_ids=%s",
                    thread.id,
                    pass_idx + 1,
                    len(loop_passes),
                    pass_info.domain,
                    pass_info.focus_label,
                    pass_info.vector_store_ids,
                )
                try:
                    domain_agent = _build_loop_domain_agent(plan_output, pass_info)
                    pass_result = await asyncio.wait_for(
                        Runner.run(
                            domain_agent,
                            retrieval_conversation,
                            context=agent_context,
                            run_config=RunConfig(
                                trace_metadata={"__trace_source__": "agent-builder"},
                            ),
                        ),
                        timeout=LOOP_PASS_TIMEOUT_SECONDS,
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
                    result = LoopPassResult(
                        domain=pass_info.domain,
                        focus_label=pass_info.focus_label,
                        product_key=pass_info.product_key,
                        text=pass_text,
                        sources=pass_sources,
                    )
                    front_logger.info(
                        "[thread=%s] loop pass %d done → result_length=%d source_count=%d",
                        thread.id,
                        pass_idx + 1,
                        len(pass_text),
                        len(pass_sources),
                    )
                    return pass_idx, result, None
                except Exception as exc:
                    front_logger.warning(
                        "[thread=%s] loop pass %d degraded → domain=%s focus=%s error=%s: %s",
                        thread.id,
                        pass_idx + 1,
                        pass_info.domain,
                        pass_info.focus_label,
                        type(exc).__name__,
                        exc,
                        exc_info=True,
                    )
                    fallback_text = (
                        f"当前资料域 `{pass_info.focus_label}` 检索暂时失败，"
                        "系统已跳过该资料域并继续使用其他可用资料回答。"
                        f"错误类型：{type(exc).__name__}。"
                    )
                    return (
                        pass_idx,
                        LoopPassResult(
                            domain=pass_info.domain,
                            focus_label=pass_info.focus_label,
                            product_key=pass_info.product_key,
                            text=fallback_text,
                            sources=(),
                        ),
                        exc,
                    )

        tasks: list[asyncio.Task[tuple[int, LoopPassResult, Exception | None]]] = []
        for pass_idx, pass_info in enumerate(loop_passes):
            if pass_info.domain == "fallback":
                progress_text = "Preparing a fallback response…"
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
            tasks.append(asyncio.create_task(run_loop_pass(pass_idx, pass_info)))

        pending: set[asyncio.Task[tuple[int, LoopPassResult, Exception | None]]] = set(tasks)
        degraded_count = 0
        try:
            while pending:
                done, pending = await asyncio.wait(
                    pending,
                    timeout=LOOP_PROGRESS_HEARTBEAT_SECONDS,
                    return_when=asyncio.FIRST_COMPLETED,
                )
                if not done:
                    yield ProgressUpdateEvent(
                        icon="search",
                        text=f"Still searching {len(pending)} source(s)…",
                    )
                    continue

                for task in done:
                    pass_idx, result, exc = task.result()
                    retrieval_results_by_idx[pass_idx] = result
                    if exc is not None:
                        degraded_count += 1
                        yield ProgressUpdateEvent(
                            icon="info",
                            text=(
                                f"Skipped one unavailable source ({result.focus_label}); "
                                "continuing with available results…"
                            ),
                        )
                    else:
                        yield ProgressUpdateEvent(
                            icon="search",
                            text=f"Finished source {pass_idx + 1}/{len(loop_passes)}.",
                        )
        finally:
            for task in pending:
                task.cancel()

        retrieval_results = [result for result in retrieval_results_by_idx if result is not None]
        if degraded_count:
            front_logger.warning(
                "[thread=%s] loop completed with degraded passes=%d/%d",
                thread.id,
                degraded_count,
                len(loop_passes),
            )

        yield ProgressUpdateEvent(icon="sparkle", text="Synthesizing answer…")
        front_logger.info(
            "[thread=%s] output agent → synthesizing %d domain results",
            thread.id,
            len(retrieval_results),
        )

        output_agent = _build_output_agent(
            plan_output.input_lang,
            user_text,
            retrieval_results,
        )
        final_sources = _merge_retrieved_sources(retrieval_results)
        source_appender = _FinalSourceAppender(final_sources, plan_output.input_lang)

        output_result = Runner.run_streamed(
            output_agent,
            output_conversation,
            context=agent_context,
            run_config=RunConfig(
                trace_metadata={"__trace_source__": "agent-builder"},
            ),
        )

        answer_text_parts: list[str] = []
        async for event in stream_agent_response(
            agent_context, output_result, converter=FFRobotConverter()
        ):
            if event.type == "thread.item.updated":
                update = event.update
                if hasattr(update, "delta") and isinstance(update.delta, str):
                    answer_text_parts.append(update.delta)
            event = rewriter.process(event)
            yield source_appender.process(event)

        answer_text = "".join(answer_text_parts)
        self.fast_answers.remember(
            raw_question=user_text,
            page_url=page_url,
            answer=answer_text,
            answer_source="rag",
            thread_id=thread.id,
            metadata={
                "source_count": len(final_sources),
                "sources": [
                    {
                        "title": source.title,
                        "kind": source.kind,
                        "slug": source.slug,
                        "url": source.url or source.page_url,
                    }
                    for source in final_sources[:8]
                ],
            },
        )

        # ── Phase 3: Post-Decision Agent ─────────────────────────────────
        retrieval_summary = "\n".join(
            f"[{r.domain}/{r.focus_label}] {r.text[:500]}" for r in retrieval_results
        )

        post_decision_agent = _build_post_decision_agent(
            recommendation_rules_prompt=self.reco_engine.build_triage_rules_prompt(),
            purchase_intent_rules_prompt=self.reco_engine.build_purchase_intent_prompt(),
            user_query=user_text,
            loop_plan=plan_output.loop_plan,
            retrieval_summary=retrieval_summary,
            answer_text=answer_text,
        )
        post_decision_result = await Runner.run(
            post_decision_agent,
            [{"role": "user", "content": user_text}],
            context=agent_context,
            run_config=RunConfig(
                trace_metadata={"__trace_source__": "agent-builder"},
            ),
        )
        post_decision: PostDecisionOutput = post_decision_result.final_output
        front_logger.info(
            "[thread=%s] post-decision → purchase_intent=%s, recommendation_hit=%s, "
            "recommendation_rule_id=%s",
            thread.id,
            post_decision.purchase_intent,
            post_decision.recommendation_hit,
            post_decision.recommendation_rule_id,
        )

        self.store.agent_traces[thread.id].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_message": user_text[:300],
            "workflow": "plan-loop-output",
            "plan": {
                "loop_plan": [item.model_dump() for item in plan_output.loop_plan],
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
                    "agent": "FF AI Output Agent",
                    "model": LLM_MODEL,
                    "role": "output",
                    "source_count": len(final_sources),
                },
                {
                    "agent": "FF Post-Decision Agent",
                    "model": "gpt-5.4-mini",
                    "role": "post-decision",
                    "output": post_decision.model_dump(),
                },
            ],
        })

        # ── Phase 4: Post-answer recommendation ──────────────────────────
        reco = self.reco_engine.evaluate_post_answer(
            input_lang=plan_output.input_lang,
            thread_id=thread.id,
            recommendation_rule_id=post_decision.recommendation_rule_id,
            purchase_intent=post_decision.purchase_intent,
        )
        if reco:
            front_logger.info(
                "[thread=%s] recommendation id=%s type=%s",
                thread.id, reco.id, reco.reco_type,
            )
            if reco.reco_type == "lead_capture":
                card = self._build_lead_card(
                    reco.title, reco.description, plan_output.input_lang,
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
