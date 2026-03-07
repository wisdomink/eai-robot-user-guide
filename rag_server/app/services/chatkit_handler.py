"""
ChatKit server: OpenAI Agents SDK with built-in File Search (方案 B).

Agent definition exported from AgentBuilder (translated from TS to Python).
Uses a custom ResponseStreamConverter to map file_citation → EntitySource,
enabling SPA navigation via the frontend entities.onClick handler.
"""

from __future__ import annotations

import json
import logging
import re
from collections import defaultdict
from collections.abc import AsyncIterator

from agents import Agent, FileSearchTool, ModelSettings, Runner
from openai.types.shared import Reasoning

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

from app.core.config import LLM_MODEL, OPENAI_VECTOR_STORE_ID, PUBLIC_BASE_URL, SIDEBAR_PATH

logger = logging.getLogger(__name__)

# ── Image URL rewriting (ChatKit iframe can't resolve relative paths) ─

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

            # Text delta — accumulate original text, rewrite the delta
            if hasattr(update, "delta") and isinstance(update.delta, str):
                item_id = event.item_id
                ci = getattr(update, "content_index", 0)
                key = (item_id, ci)
                self._text_buf.setdefault(key, "")
                self._text_buf[key] += update.delta
                update.delta = _rewrite_image_urls(update.delta)

            # content_part.done — rewrite complete text
            if hasattr(update, "content") and hasattr(update.content, "text"):
                update.content.text = _rewrite_image_urls(update.content.text)

            # Annotation added — shift index by accumulated URL expansion
            if hasattr(update, "annotation"):
                ann = update.annotation
                if ann is not None and ann.index is not None:
                    item_id = event.item_id
                    ci = getattr(update, "content_index", 0)
                    key = (item_id, ci)
                    original = self._text_buf.get(key, "")
                    ann.index += _compute_rewrite_offset(original, ann.index)

        return event


# ── Agent Instructions (from AgentBuilder export) ────────────────────

INSTRUCTIONS = """\
你是一名专业的技术支持工程师，专门负责 FF Master 系列机器人（FF Master / FF Master Edu / FF Master Ultra Edition）的用户支持。

## 你的知识来源

你的全部知识来自上传到 Vector Store 的用户手册文档（Markdown 文件）。这些文档涵盖：

| 分类 | 内容 |
|------|------|
| 安全须知 | 安全指南、安全注意事项、维护管理指南 |
| 产品介绍 | 装箱清单、产品概述（三个版本对比）、产品结构图、计算单元、电池指示灯、传感器视野、关节名称与限位、坐标系、规格参数 |
| 操作指南 | 安全预防措施、开机指南、关机指南、充电流程、遥控器使用指南、机器人交互流程、FF Robotic APP 手册、其他操作 |
| 运动平台 | 运动与操控平台手册 |
| 联系方式 | 联系信息 |

## 文档文件名 → 页面路径映射

当你引用文档内容时，以下映射关系用于前端页面导航。请在回答末尾标注所引用的文档来源文件名：

```
safety-instructions.md    → /safety-instructions
safety-guidelines.md      → /safety-guidelines
maintenance.md            → /maintenance-guidelines
packing-list.md           → /packing-list
product-overview.md       → /product-overview
computational-unit.md     → /computational-unit
battery-indicator.md      → /battery-indicator-lights
sensor-fov.md             → /sensor-fov
joint-limits.md           → /joint-limits
coordinate-systems.md     → /coordinate-systems
specifications.md         → /specifications
safety-precautions.md     → /safety-precautions
startup-guide.md          → /startup-guide
shutdown-guide.md         → /shutdown-guide
charging-procedure.md     → /charging-procedure
remote-control.md         → /remote-control
robot-interaction.md      → /robot-interaction
ff-robotic-app.md         → /ff-robotic-app
others.md                 → /others
locomotion-platform.md    → /locomotion-platform
contact-information.md    → /contact-information
```

## 回答规则

1. 收到用户问题后，判断问题语言是中文还是英文，如果是中文则首先将问题翻译成英文，然后再调用系统，系统会自动搜索相关文档（file_search）。仅根据搜索结果回答，**不要使用任何外部知识**。
2. 如果文档中未找到相关信息，直接回答："抱歉，说明书中未找到相关信息。"
3. 使用**问题语言**回答，保持简洁、专业、结构化（适当使用列表、表格）。
4. 如果文档中包含图片引用（如 `![alt](/images/docx/xxx.png)`），在回答中**保留完整的 Markdown 图片语法**。
5. **不要**在回答中手动附加引用标记或来源链接，系统会自动处理引用显示。
"""

# ── Agent Definition (translated from AgentBuilder TS export) ────────

assistant_agent = Agent(
    name="FF Master Support",
    instructions=INSTRUCTIONS,
    model=LLM_MODEL,
    tools=[FileSearchTool(vector_store_ids=[OPENAI_VECTOR_STORE_ID])],
    model_settings=ModelSettings(
        reasoning=Reasoning(effort="medium", summary="auto"),
        store=True,
    ),
)

# ── File name → slug mapping (for source navigation links) ──────────


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


# ── Custom ResponseStreamConverter ───────────────────────────────────


class FFRobotConverter(ResponseStreamConverter):
    """Override file_citation_to_annotation to produce EntitySource
    instead of the default FileSource, enabling SPA navigation via
    the frontend entities.onClick handler."""

    async def file_citation_to_annotation(self, file_citation) -> Annotation | None:
        filename = file_citation.filename
        if not filename:
            return None

        page_info = FILE_SLUG_MAP.get(filename)
        if not page_info:
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


# ── In-memory Store ──────────────────────────────────────────────────


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


# ── ChatKit Server ───────────────────────────────────────────────────


class FFRobotChatKitServer(ChatKitServer[dict]):
    """Bridges ChatKit protocol to the OpenAI Agents SDK.

    Uses Runner.run_streamed() to execute the Agent, and
    stream_agent_response() with a custom FFRobotConverter to
    automatically handle streaming events and file citation mapping.
    """

    async def respond(
        self,
        thread: ThreadMetadata,
        input_user_message: UserMessageItem | None,
        context: dict,
    ) -> AsyncIterator[ThreadStreamEvent]:
        # Load conversation history
        items_page = await self.store.load_thread_items(
            thread.id, after=None, limit=20, order="desc", context=context
        )
        items = list(reversed(items_page.data))

        # Convert to Agent SDK input format
        input_items = await simple_to_agent_input(items)

        # Build AgentContext (bridges ChatKit store ↔ Agents SDK)
        agent_context = AgentContext(
            thread=thread,
            store=self.store,
            request_context=context,
        )

        # Run the Agent (streaming)
        result = Runner.run_streamed(
            assistant_agent,
            input_items,
            context=agent_context,
        )

        # stream_agent_response handles all event conversion automatically;
        # FFRobotConverter ensures file_citation → EntitySource (not FileSource).
        # _EventStreamRewriter rewrites image URLs while keeping annotation
        # indices in sync so citations never split an expanded URL.
        rewriter = _EventStreamRewriter()
        async for event in stream_agent_response(
            agent_context, result, converter=FFRobotConverter()
        ):
            yield rewriter.process(event)


def create_chatkit_server() -> FFRobotChatKitServer:
    return FFRobotChatKitServer(store=InMemoryStore())
