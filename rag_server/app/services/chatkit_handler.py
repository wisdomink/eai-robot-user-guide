"""
ChatKit server: multi-agent workflow powered by OpenAI Agents SDK.

Workflow: Triage Agent (structured routing) → Product-specific Support Agent (streamed).
Translated from the AgentBuilder exported code to self-hosted Python.

Uses a custom ResponseStreamConverter to map file_citation → EntitySource,
enabling SPA navigation via the frontend entities.onClick handler.
"""

from __future__ import annotations

import json
import logging
import re
from collections import defaultdict
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from pathlib import Path

from agents import Agent, FileSearchTool, ModelSettings, Runner, RunConfig
from pydantic import BaseModel

from chatkit.agents import (
    AgentContext,
    ResponseStreamConverter,
    simple_to_agent_input,
    stream_agent_response,
)
from chatkit.server import ChatKitServer
from chatkit.store import NotFoundError, Store
from chatkit.types import (
    Annotation,
    Attachment,
    EntitySource,
    Page,
    ThreadItem,
    ThreadMetadata,
    ThreadStreamEvent,
    UserMessageItem,
)

from app.core.config import (
    LLM_MODEL,
    OPENAI_VECTOR_STORE_AEGIS_EDU_ID,
    OPENAI_VECTOR_STORE_AEGIS_ULTRA_ID,
    OPENAI_VECTOR_STORE_FUTURIST_ULTRA_ID,
    OPENAI_VECTOR_STORE_MASTER_ULTRA_ID,
    OPENAI_VECTOR_STORE_ROBOT_ALL_ID,
    PUBLIC_BASE_URL,
    SIDEBAR_PATH,
)
from app.core.logging_config import FRONT_LOGGER_NAME

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
    query_type: str
    query_text: str


# ── Agent definitions ────────────────────────────────────────────────────

_TRIAGE_MODEL_SETTINGS = ModelSettings(
    store=True,
)

_SUPPORT_MODEL_SETTINGS = ModelSettings(
    store=True,
    tool_choice="required",
)

triage_agent = Agent(
    name="FF Robot Triage",
    instructions=_load_instructions("triage"),
    model="gpt-4o",
    output_type=TriageOutput,
    model_settings=_TRIAGE_MODEL_SETTINGS,
)

_SUPPORT_AGENT_CONFIGS: dict[str, dict] = {
    "master-ultra": {
        "name": "Master Ultra Support",
        "instructions_file": "master-ultra",
        "vector_store_id": OPENAI_VECTOR_STORE_MASTER_ULTRA_ID,
    },
    "futurist-ultra": {
        "name": "Futurist Ultra Support",
        "instructions_file": "futurist-ultra",
        "vector_store_id": OPENAI_VECTOR_STORE_FUTURIST_ULTRA_ID,
    },
    "aegis-ultra": {
        "name": "Aegis Ultra Support",
        "instructions_file": "aegis-ultra",
        "vector_store_id": OPENAI_VECTOR_STORE_AEGIS_ULTRA_ID,
    },
    "aegis-edu": {
        "name": "Aegis EDU Support",
        "instructions_file": "aegis-edu",
        "vector_store_id": OPENAI_VECTOR_STORE_AEGIS_EDU_ID,
    },
    "general": {
        "name": "General Support",
        "instructions_file": "general",
        "vector_store_id": OPENAI_VECTOR_STORE_ROBOT_ALL_ID,
    },
}

# Pre-load instruction templates at module level (avoids repeated disk I/O).
_INSTRUCTION_TEMPLATES: dict[str, str] = {
    key: _load_instructions(cfg["instructions_file"])
    for key, cfg in _SUPPORT_AGENT_CONFIGS.items()
}


def _build_support_agent(
    query_type: str, input_lang: str, query_text: str
) -> Agent:
    """Build the appropriate support Agent with triage values interpolated
    into the instruction template."""
    cfg = _SUPPORT_AGENT_CONFIGS.get(query_type, _SUPPORT_AGENT_CONFIGS["general"])
    template = _INSTRUCTION_TEMPLATES.get(query_type, _INSTRUCTION_TEMPLATES["general"])

    instructions = template.replace("{{input_lang}}", input_lang)
    instructions = instructions.replace("{{query_text}}", query_text)

    return Agent(
        name=cfg["name"],
        instructions=instructions,
        model=LLM_MODEL,
        tools=[FileSearchTool(vector_store_ids=[cfg["vector_store_id"]])],
        model_settings=_SUPPORT_MODEL_SETTINGS,
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

        page_info = FILE_SLUG_MAP.get(filename)
        if not page_info:
            logger.warning("No slug mapping for citation filename=%r", filename)
            return None

        slug = page_info["slug"]
        return Annotation(
            source=EntitySource(
                id=slug,
                title=page_info["title"],
                interactive=True,
                data={"slug": slug},
            ),
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
    """Two-phase multi-agent workflow:

    1. **Triage** (non-streamed): detect language, identify product, expand query.
    2. **Support Agent** (streamed): run the product-specific agent with
       file_search and stream the response back to ChatKit.
    """

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

        # ── Phase 1: Triage (non-streamed, structured JSON output) ───────
        logger.info("Running triage agent …")
        triage_result = await Runner.run(
            triage_agent,
            input_items,
            context=agent_context,
            run_config=RunConfig(
                trace_metadata={"__trace_source__": "agent-builder"},
            ),
        )

        triage_output: TriageOutput = triage_result.final_output
        front_logger.info(
            "[thread=%s] triage → query_type=%s, input_lang=%s, query_text=%s",
            thread.id,
            triage_output.query_type,
            triage_output.input_lang,
            triage_output.query_text[:120] if triage_output.query_text else "",
        )

        # ── Phase 2: Route to product-specific agent (streamed) ──────────
        support_agent = _build_support_agent(
            triage_output.query_type,
            triage_output.input_lang,
            triage_output.query_text,
        )

        support_cfg = _SUPPORT_AGENT_CONFIGS.get(
            triage_output.query_type, _SUPPORT_AGENT_CONFIGS["general"]
        )
        self.store.agent_traces[thread.id].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_message": user_text[:300],
            "nodes": [
                {
                    "agent": triage_agent.name,
                    "model": LLM_MODEL,
                    "role": "triage",
                    "output": {
                        "query_type": triage_output.query_type,
                        "input_lang": triage_output.input_lang,
                        "query_text": triage_output.query_text,
                    },
                },
                {
                    "agent": support_cfg["name"],
                    "model": LLM_MODEL,
                    "role": "support",
                    "routed_by": triage_output.query_type,
                    "vector_store_id": support_cfg["vector_store_id"],
                    "tools": ["file_search"],
                },
            ],
        })

        conversation = list(input_items)
        for i in range(len(conversation) - 1, -1, -1):
            item = conversation[i]
            if isinstance(item, dict) and item.get("role") == "user":
                conversation[i] = {"role": "user", "content": triage_output.query_text}
                break

        result = Runner.run_streamed(
            support_agent,
            conversation,
            context=agent_context,
            run_config=RunConfig(
                trace_metadata={"__trace_source__": "agent-builder"},
            ),
        )

        rewriter = _EventStreamRewriter()
        async for event in stream_agent_response(
            agent_context, result, converter=FFRobotConverter()
        ):
            yield rewriter.process(event)


def create_chatkit_server() -> FFRobotChatKitServer:
    return FFRobotChatKitServer(store=InMemoryStore())
