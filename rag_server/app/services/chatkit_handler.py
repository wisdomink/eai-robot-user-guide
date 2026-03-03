"""
ChatKit server: OpenAI Assistants API + RAG retrieval via ChromaDB.

Bridges the ChatKit protocol (threads, messages, streaming) with the
OpenAI Assistants API.  The Assistant is created/managed on the OpenAI
Dashboard; this module only handles runtime execution and local tool calls.
"""

from __future__ import annotations

import asyncio
import json
import logging
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

from app.core.config import OPENAI_API_KEY, OPENAI_ASSISTANT_ID
from app.services.rag_engine import rag_engine

logger = logging.getLogger(__name__)

# ── OpenAI client ────────────────────────────────────────────────────────

oai = AsyncOpenAI(api_key=OPENAI_API_KEY)


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
    ``thread.metadata["oai_thread_id"]``.  The Assistant's instructions,
    model, and tool schema are all managed on the OpenAI Dashboard —
    the only local execution is the ``search_manual`` RAG retrieval.
    """

    async def respond(
        self,
        thread: ThreadMetadata,
        input_user_message: UserMessageItem | None,
        context: dict,
    ) -> AsyncIterator[ThreadStreamEvent]:
        context["_sources"] = []

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

        # Announce a new assistant message
        yield ThreadItemAddedEvent(
            item=AssistantMessageItem(
                thread_id=thread.id,
                id=item_id,
                created_at=now,
                content=[],
            )
        )

        # ── Stream the Assistants API run ─────────────────────────
        async for delta_text, event_type in self._run_with_tools(
            oai_thread_id, context
        ):
            if event_type == "tool_start":
                yield ProgressUpdateEvent(
                    icon="search",
                    text="正在搜索文档…",
                )
                continue

            if event_type == "delta":
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

                full_text += delta_text
                yield ThreadItemUpdatedEvent(
                    item_id=item_id,
                    update=AssistantMessageContentPartTextDelta(
                        content_index=0,
                        delta=delta_text,
                    ),
                )

        # ── Finalize ──────────────────────────────────────────────
        final_content = AssistantMessageContent(text=full_text)
        final_item = AssistantMessageItem(
            thread_id=thread.id,
            id=item_id,
            created_at=now,
            content=[final_content],
        )
        self._append_source_links(final_item, context)

        if content_part_added:
            yield ThreadItemUpdatedEvent(
                item_id=item_id,
                update=AssistantMessageContentPartDone(
                    content_index=0,
                    content=final_item.content[0],
                ),
            )

        yield ThreadItemDoneEvent(item=final_item)

    # ── Assistants API streaming with tool-call loop ─────────────

    async def _run_with_tools(
        self, thread_id: str, context: dict
    ) -> AsyncIterator[tuple[str, str]]:
        """Yield ``(text, event_type)`` tuples from an Assistants run.

        Handles the ``requires_action`` → local tool execution →
        ``submit_tool_outputs_stream`` loop transparently.

        ``event_type`` is one of ``"delta"`` or ``"tool_start"``.
        """
        requires_action = None
        run_id: str | None = None

        async with oai.beta.threads.runs.stream(
            thread_id=thread_id,
            assistant_id=OPENAI_ASSISTANT_ID,
        ) as stream:
            async for event in stream:
                ev = event.event
                if ev == "thread.message.delta":
                    for part in event.data.delta.content or []:
                        if hasattr(part, "text") and part.text:
                            yield (part.text.value, "delta")
                elif ev == "thread.run.requires_action":
                    requires_action = event.data.required_action
                    run_id = event.data.id

        while requires_action:
            yield ("", "tool_start")
            tool_outputs = await self._execute_tool_calls(
                requires_action, context
            )
            requires_action = None

            async with oai.beta.threads.runs.submit_tool_outputs_stream(
                thread_id=thread_id,
                run_id=run_id,
                tool_outputs=tool_outputs,
            ) as stream:
                async for event in stream:
                    ev = event.event
                    if ev == "thread.message.delta":
                        for part in event.data.delta.content or []:
                            if hasattr(part, "text") and part.text:
                                yield (part.text.value, "delta")
                    elif ev == "thread.run.requires_action":
                        requires_action = event.data.required_action
                        run_id = event.data.id

    # ── Local tool execution ─────────────────────────────────────

    @staticmethod
    async def _execute_tool_calls(
        required_action, context: dict
    ) -> list[dict]:
        tool_outputs: list[dict] = []
        for tc in required_action.submit_tool_outputs.tool_calls:
            if tc.function.name == "search_manual":
                args = json.loads(tc.function.arguments)
                context_text, sources = await asyncio.to_thread(
                    rag_engine.retrieve, args["query"]
                )
                context.setdefault("_sources", []).extend(sources)
                tool_outputs.append({
                    "tool_call_id": tc.id,
                    "output": context_text,
                })
            else:
                logger.warning("Unknown tool call: %s", tc.function.name)
                tool_outputs.append({
                    "tool_call_id": tc.id,
                    "output": json.dumps({"error": f"Unknown tool: {tc.function.name}"}),
                })
        return tool_outputs

    # ── Source annotations ────────────────────────────────────────

    @staticmethod
    def _append_source_links(
        item: AssistantMessageItem, context: dict
    ) -> None:
        """Attach deduplicated source references as ChatKit entity annotations.

        ChatKit renders these as clickable inline citations and a
        collapsed Sources list beneath the message.  The frontend
        ``entities.onClick`` handler performs SPA navigation.
        """
        sources = context.get("_sources", [])
        if not sources:
            return

        text = item.content[0].text or ""
        end_index = max(0, len(text) - 1)

        annotations: list[Annotation] = []
        seen_slugs: set[str] = set()
        for src in sources:
            slug = src.get("url_path", "")
            title = src.get("title", "")
            if not slug or not title or slug in seen_slugs:
                continue
            seen_slugs.add(slug)
            url = src.get("url_with_anchor", slug)
            annotations.append(
                Annotation(
                    source=EntitySource(
                        id=slug,
                        title=title,
                        interactive=True,
                        data={"slug": url},
                    ),
                    index=end_index,
                )
            )

        if annotations:
            existing = getattr(item.content[0], "annotations", None) or []
            item.content[0].annotations = list(existing) + annotations


def create_chatkit_server() -> FFRobotChatKitServer:
    return FFRobotChatKitServer(store=InMemoryStore())
