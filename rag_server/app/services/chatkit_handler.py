"""
ChatKit server: OpenAI Assistants API with built-in File Search (hosted RAG).

Bridges the ChatKit protocol (threads, messages, streaming) with the
OpenAI Assistants API.  Document retrieval is handled entirely by OpenAI's
hosted file_search tool — no local vector database needed.
"""

from __future__ import annotations

import json
import logging
import re
from collections import defaultdict
from collections.abc import AsyncIterator
from datetime import datetime, timezone

from openai import AsyncOpenAI

from chatkit.server import ChatKitServer
from chatkit.store import NotFoundError, Store
from chatkit.types import (
    Annotation,
    AssistantMessageContent,
    AssistantMessageItem,
    Attachment,
    AssistantMessageContentPartAdded,
    AssistantMessageContentPartDone,
    AssistantMessageContentPartTextDelta,
    EntitySource,
    Page,
    ProgressUpdateEvent,
    ThreadItem,
    ThreadItemAddedEvent,
    ThreadItemDoneEvent,
    ThreadItemUpdatedEvent,
    ThreadMetadata,
    ThreadStreamEvent,
    UserMessageItem,
)

from app.core.config import OPENAI_API_KEY, OPENAI_ASSISTANT_ID, SIDEBAR_PATH

logger = logging.getLogger(__name__)

# ── Regex to strip OpenAI file-citation markers (e.g. 【4:1†source】) ─────

CITATION_RE = re.compile(r"【[^】]*†[^】]*】")

# ── OpenAI client ────────────────────────────────────────────────────────

oai = AsyncOpenAI(api_key=OPENAI_API_KEY)

# ── File name → slug mapping (for source navigation links) ──────────────


def _build_file_slug_map() -> dict[str, dict]:
    """Build {filename: {slug, title}} from sidebar.json."""
    try:
        with open(SIDEBAR_PATH, "r", encoding="utf-8") as f:
            sidebar = json.load(f)
    except FileNotFoundError:
        logger.warning("sidebar.json not found at %s", SIDEBAR_PATH)
        return {}

    result: dict[str, dict] = {}
    for section in sidebar.get("sections", []):
        for page in section.get("pages", []):
            result[page["file"]] = {
                "slug": page["slug"],
                "title": page["title"],
            }
    return result


FILE_SLUG_MAP = _build_file_slug_map()

# file_id → filename cache (populated lazily via OpenAI Files API)
_file_id_cache: dict[str, str] = {}


# ── In-memory Store ──────────────────────────────────────────────────────


class InMemoryStore(Store[dict]):
    """Minimal in-memory store for development. Replace with a
    database-backed store (Postgres, MySQL, etc.) for production.
    """

    def __init__(self) -> None:
        self.threads: dict[str, ThreadMetadata] = {}
        self.items: dict[str, list[ThreadItem]] = defaultdict(list)

    async def load_thread(self, thread_id: str, context: dict) -> ThreadMetadata:
        if thread_id not in self.threads:
            raise NotFoundError(f"Thread {thread_id} not found")
        return self.threads[thread_id]

    async def save_thread(self, thread: ThreadMetadata, context: dict) -> None:
        self.threads[thread.id] = thread

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
    """Bridges ChatKit protocol to the OpenAI Assistants API.

    Each ChatKit thread is mapped to an Assistants API thread via
    ``thread.metadata["oai_thread_id"]``.  The assistant uses OpenAI's
    hosted file_search tool for RAG — no local tool execution needed.
    """

    async def respond(
        self,
        thread: ThreadMetadata,
        input_user_message: UserMessageItem | None,
        context: dict,
    ) -> AsyncIterator[ThreadStreamEvent]:
        context["_file_citations"] = []

        # ── Map ChatKit thread → Assistants API thread ────────────
        oai_thread_id = (thread.metadata or {}).get("oai_thread_id")
        if not oai_thread_id:
            oai_thread = await oai.beta.threads.create()
            oai_thread_id = oai_thread.id
            if thread.metadata is None:
                thread.metadata = {}
            thread.metadata["oai_thread_id"] = oai_thread_id
            await self.store.save_thread(thread, context)

        # ── Forward user message to the Assistants thread ─────────
        if input_user_message and input_user_message.content:
            user_text = input_user_message.content[0].text
            await oai.beta.threads.messages.create(
                thread_id=oai_thread_id,
                role="user",
                content=user_text,
            )

        # ── Prepare ChatKit streaming events ──────────────────────
        item_id = self.store.generate_item_id("message", thread, context)
        now = datetime.now(timezone.utc)
        full_text = ""
        content_part_added = False

        yield ThreadItemAddedEvent(
            item=AssistantMessageItem(
                thread_id=thread.id,
                id=item_id,
                created_at=now,
                content=[],
            )
        )

        # ── Stream the Assistants API run (file_search is server-side) ──
        async for delta_text, event_type in self._stream_run(
            oai_thread_id, context
        ):
            if event_type == "search_start":
                yield ProgressUpdateEvent(
                    icon="search",
                    text="正在搜索文档…",
                )
                continue

            if event_type == "delta":
                cleaned = CITATION_RE.sub("", delta_text)
                if not cleaned:
                    continue

                if not content_part_added:
                    yield ProgressUpdateEvent(text="")
                    yield ThreadItemUpdatedEvent(
                        item_id=item_id,
                        update=AssistantMessageContentPartAdded(
                            content_index=0,
                            content=AssistantMessageContent(text=""),
                        ),
                    )
                    content_part_added = True

                full_text += cleaned
                yield ThreadItemUpdatedEvent(
                    item_id=item_id,
                    update=AssistantMessageContentPartTextDelta(
                        content_index=0,
                        delta=cleaned,
                    ),
                )

        # ── Finalize ──────────────────────────────────────────────
        clean_text = CITATION_RE.sub("", full_text).strip()
        final_content = AssistantMessageContent(text=clean_text)
        final_item = AssistantMessageItem(
            thread_id=thread.id,
            id=item_id,
            created_at=now,
            content=[final_content],
        )
        await self._append_source_links(final_item, context)

        if content_part_added:
            yield ThreadItemUpdatedEvent(
                item_id=item_id,
                update=AssistantMessageContentPartDone(
                    content_index=0,
                    content=final_item.content[0],
                ),
            )

        yield ThreadItemDoneEvent(item=final_item)

    # ── Assistants API streaming (no local tool loop) ─────────────

    async def _stream_run(
        self, thread_id: str, context: dict
    ) -> AsyncIterator[tuple[str, str]]:
        """Yield ``(text, event_type)`` tuples from an Assistants run.

        With file_search, retrieval runs entirely on OpenAI's side.
        No ``requires_action`` / ``submit_tool_outputs`` loop is needed.
        """
        async with oai.beta.threads.runs.stream(
            thread_id=thread_id,
            assistant_id=OPENAI_ASSISTANT_ID,
        ) as stream:
            async for event in stream:
                ev = event.event

                if ev == "thread.run.step.created":
                    if event.data.type == "tool_calls":
                        yield ("", "search_start")

                elif ev == "thread.message.delta":
                    for part in event.data.delta.content or []:
                        if hasattr(part, "text") and part.text:
                            yield (part.text.value or "", "delta")

                elif ev == "thread.message.completed":
                    # Collect file citations for source link annotations
                    for content in event.data.content:
                        if content.type == "text":
                            for ann in (content.text.annotations or []):
                                if ann.type == "file_citation":
                                    context["_file_citations"].append(
                                        ann.file_citation.file_id
                                    )

    # ── Source annotations (file_citation → ChatKit EntitySource) ─

    async def _resolve_filename(self, file_id: str) -> str:
        """Resolve an OpenAI file_id to its original filename (cached)."""
        if file_id in _file_id_cache:
            return _file_id_cache[file_id]
        try:
            file_obj = await oai.files.retrieve(file_id)
            _file_id_cache[file_id] = file_obj.filename
            return file_obj.filename
        except Exception:
            logger.warning("Failed to resolve file_id %s", file_id)
            return ""

    async def _append_source_links(
        self, item: AssistantMessageItem, context: dict
    ) -> None:
        """Map OpenAI file citations to ChatKit entity annotations.

        Resolves file_id → filename → sidebar slug so the frontend
        ``entities.onClick`` handler can perform SPA navigation.
        """
        file_ids = list(set(context.get("_file_citations", [])))
        if not file_ids:
            return

        text = item.content[0].text or ""
        end_index = max(0, len(text) - 1)

        annotations: list[Annotation] = []
        seen_slugs: set[str] = set()

        for fid in file_ids:
            filename = await self._resolve_filename(fid)
            page_info = FILE_SLUG_MAP.get(filename)
            if not page_info:
                continue

            slug = page_info["slug"]
            if slug in seen_slugs:
                continue
            seen_slugs.add(slug)

            annotations.append(
                Annotation(
                    source=EntitySource(
                        id=slug,
                        title=page_info["title"],
                        interactive=True,
                        data={"slug": slug},
                    ),
                    index=end_index,
                )
            )

        if annotations:
            existing = getattr(item.content[0], "annotations", None) or []
            item.content[0].annotations = list(existing) + annotations


def create_chatkit_server() -> FFRobotChatKitServer:
    return FFRobotChatKitServer(store=InMemoryStore())
