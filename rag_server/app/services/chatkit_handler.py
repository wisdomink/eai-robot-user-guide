"""
ChatKit server: OpenAI Agents SDK + RAG retrieval via ChromaDB.

Handles the ChatKit protocol (threads, messages, streaming) through a
single /chatkit FastAPI endpoint.
"""

from __future__ import annotations

import asyncio
import os
from collections import defaultdict
from collections.abc import AsyncIterator

from agents import Agent, Runner, RunContextWrapper, function_tool
from chatkit.agents import AgentContext, simple_to_agent_input, stream_agent_response
from chatkit.server import ChatKitServer
from chatkit.store import NotFoundError, Store
from chatkit.types import (
    Annotation,
    AssistantMessageItem,
    Attachment,
    EntitySource,
    Page,
    ThreadItem,
    ThreadItemDoneEvent,
    ThreadMetadata,
    ThreadStreamEvent,
    UserMessageItem,
)

from app.services.rag_engine import rag_engine

# ── RAG Tool ──────────────────────────────────────────────────────────────


@function_tool()
async def search_manual(
    ctx: RunContextWrapper[AgentContext], query: str
) -> str:
    """Search the FF Master robot user manual for relevant documentation.
    Always use this tool before answering any user question about the robot.
    """
    context_text, sources = await asyncio.to_thread(
        rag_engine.retrieve, query
    )
    # Store sources in the shared request context for annotation later
    ctx.context.request_context.setdefault("_sources", []).extend(sources)
    return context_text


# ── Agent ─────────────────────────────────────────────────────────────────

AGENT_INSTRUCTIONS = """\
你是一名专业的技术支持工程师，专门负责 FF Master Ultra Edition 机器人的用户支持。

规则：
1. 收到用户问题后，必须先使用 search_manual 工具搜索相关文档。
2. 仅根据搜索结果回答用户问题，不要使用任何外部知识。
3. 如果搜索结果中未提及相关信息，请直接回答："抱歉，说明书中未找到相关信息。"
4. 保持回答简洁、专业、结构化，使用中文回答。
5. 如果搜索结果中包含图片链接，请在回答中保留图片的 Markdown 语法。
6. 不要在回答中附加参考来源或引用链接，系统会自动在回答末尾添加。
"""

assistant = Agent(
    name="FF Master Support",
    instructions=AGENT_INSTRUCTIONS,
    model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
    tools=[search_manual],
)


# ── In-memory Store ───────────────────────────────────────────────────────


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


# ── ChatKit Server ────────────────────────────────────────────────────────


class FFRobotChatKitServer(ChatKitServer[dict]):
    async def respond(
        self,
        thread: ThreadMetadata,
        input_user_message: UserMessageItem | None,
        context: dict,
    ) -> AsyncIterator[ThreadStreamEvent]:
        context["_sources"] = []

        items_page = await self.store.load_thread_items(
            thread.id, after=None, limit=20, order="asc", context=context,
        )
        input_items = await simple_to_agent_input(items_page.data)

        agent_context = AgentContext(
            thread=thread, store=self.store, request_context=context,
        )
        result = Runner.run_streamed(
            assistant, input_items, context=agent_context,
        )
        async for event in stream_agent_response(agent_context, result):
            if (
                isinstance(event, ThreadItemDoneEvent)
                and isinstance(event.item, AssistantMessageItem)
                and event.item.content
            ):
                self._append_source_links(event.item, context)
            yield event

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
