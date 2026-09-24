"""ChatKit storage. Memory for local development; DynamoDB for deployments."""
from __future__ import annotations

import asyncio
import json
import logging
import threading
import zlib
from uuid import uuid4
from collections import defaultdict
from datetime import timezone

import boto3
from boto3.dynamodb.conditions import Key
from botocore.config import Config
from pydantic import TypeAdapter
from chatkit.store import Store, NotFoundError
from chatkit.types import ThreadMetadata, ThreadItem, Attachment, Page

front_logger = logging.getLogger("front")
_ITEM = TypeAdapter(ThreadItem)

class InMemoryStore(Store[dict]):
    """Local development store; production selects DynamoDBStore."""

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
        await self.save_item(thread_id, item, context)
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
        self.agent_traces.pop(thread_id, None)
        self.thread_langs.pop(thread_id, None)

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


    async def add_trace(self, thread_id: str, trace: dict) -> None:
        self.agent_traces[thread_id].append(trace)

    async def load_traces(self, thread_id: str) -> list[dict]:
        return self.agent_traces.get(thread_id, [])

    async def get_language(self, thread_id: str) -> str:
        return self.thread_langs.get(thread_id, "en")

    async def set_language(self, thread_id: str, language: str) -> None:
        self.thread_langs[thread_id] = language

    async def history_summary(self, thread_id: str) -> dict:
        items = self.items.get(thread_id, [])
        first = next((i for i in items if i.type == "user_message"), None)
        traces = await self.load_traces(thread_id)
        return {
            "item_count": len(items),
            "first_message": " ".join(getattr(p, "text", "") for p in first.content)[:200] if first else "",
            "agents": [n["agent"] for n in traces[-1].get("nodes", [])] if traces else [],
        }


class DynamoDBStore(InMemoryStore):
    """One partition per conversation; sparse GSI contains only thread metadata.

    Payloads use JSON to preserve Pydantic discriminators and float values. Large
    compressed payloads use immutable chunks published before their manifest.
    Superseded chunks are retained until thread deletion so concurrent readers
    never lose a version they have already started reading.
    """

    def __init__(self, table_name: str, region: str = "", *, table=None):
        if table is None and not table_name:
            raise ValueError("CHAT_DDB_TABLE is required for DynamoDB chat storage")
        self.table = table
        self.table_name = table_name
        self.region = region
        self._local = threading.local()

    def _sync_call(self, operation, kwargs):
        # Boto3 resources are not thread-safe; each executor thread owns one.
        table = self.table
        if table is None:
            table = getattr(self._local, "table", None)
            if table is None:
                table = boto3.session.Session().resource(
                    "dynamodb", **({"region_name": self.region} if self.region else {}),
                    config=Config(connect_timeout=3, read_timeout=10,
                                  retries={"mode": "standard", "total_max_attempts": 3}),
                ).Table(self.table_name)
                self._local.table = table
        return getattr(table, operation)(**kwargs)

    async def _call(self, operation: str, **kwargs):
        try:
            return await asyncio.to_thread(self._sync_call, operation, kwargs)
        except Exception:
            front_logger.exception("Chat persistence failed: operation=%s", operation)
            raise

    @staticmethod
    def _pk(thread_id):
        return f"THREAD#{thread_id}"

    @staticmethod
    def _time(value):
        return value.astimezone(timezone.utc).isoformat(timespec="microseconds")

    async def _get(self, pk, sk):
        return (await self._call("get_item", Key={"pk": pk, "sk": sk},
                                 ConsistentRead=True)).get("Item")

    async def _put(self, pk, sk, payload, **fields):
        data = zlib.compress(json.dumps(payload, ensure_ascii=False).encode())
        row = {"pk": pk, "sk": sk, **fields}
        if len(data) <= 300_000:
            row["payload"] = data
        else:
            version = uuid4().hex
            chunks = [data[i:i + 300_000] for i in range(0, len(data), 300_000)]
            for i, chunk in enumerate(chunks):
                await self._call("put_item", Item={"pk": pk,
                    "sk": f"CHUNK#{version}#{i:06d}", "payload": chunk})
            row.update(chunk_version=version, chunk_count=len(chunks))
        # The final put publishes a complete document; failed chunk writes never
        # replace the previous readable version.
        await self._call("put_item", Item=row)

    async def _decode(self, row):
        if "chunk_version" in row:
            parts = []
            for i in range(int(row["chunk_count"])):
                chunk = await self._get(row["pk"], f"CHUNK#{row['chunk_version']}#{i:06d}")
                if chunk is None:
                    raise RuntimeError("Chat payload chunk is missing")
                parts.append(bytes(chunk["payload"]))
            data = b"".join(parts)
        else:
            data = bytes(row["payload"])
        return json.loads(zlib.decompress(data))

    async def _rows(self, pk, prefix, *, projection=None):
        condition = Key("pk").eq(pk)
        if prefix:
            condition &= Key("sk").begins_with(prefix)
        kwargs = {"KeyConditionExpression": condition, "ConsistentRead": True}
        if projection:
            kwargs["ProjectionExpression"] = projection
        rows = []
        while True:
            response = await self._call("query", **kwargs)
            rows.extend(response.get("Items", []))
            if not response.get("LastEvaluatedKey"):
                return rows
            kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]

    async def load_thread(self, thread_id, context):
        row = await self._get(self._pk(thread_id), "META")
        if row is None:
            raise NotFoundError(f"Thread {thread_id} not found")
        return ThreadMetadata.model_validate(await self._decode(row))

    async def save_thread(self, thread, context):
        await self._put(self._pk(thread.id), "META", thread.model_dump(mode="json"),
                        gpk="THREADS", gsk=f"{self._time(thread.created_at)}#{thread.id}")

    async def load_threads(self, limit, after, order, context):
        kwargs = {"IndexName": "threads-by-created", "KeyConditionExpression": Key("gpk").eq("THREADS"),
                  "ScanIndexForward": order == "asc", "Limit": limit + 1}
        if after:
            thread = await self.load_thread(after, context)
            kwargs["ExclusiveStartKey"] = {"pk": self._pk(after), "sk": "META",
                "gpk": "THREADS", "gsk": f"{self._time(thread.created_at)}#{after}"}
        rows = []
        while len(rows) < limit + 1:
            kwargs["Limit"] = limit + 1 - len(rows)
            response = await self._call("query", **kwargs)
            rows.extend(response.get("Items", []))
            if not response.get("LastEvaluatedKey"):
                break
            kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
        data = [ThreadMetadata.model_validate(await self._decode(r)) for r in rows[:limit]]
        return Page(data=data, has_more=len(rows) > limit,
                    after=data[-1].id if len(rows) > limit else None)

    async def save_item(self, thread_id, item, context):
        pk = self._pk(thread_id)
        sk = f"ITEM#{self._time(item.created_at)}#{item.id}"
        # Stable IDs make repeated delivery overwrite rather than duplicate.
        await self._call("put_item", Item={"pk": pk, "sk": f"ID#{item.id}", "item_key": sk})
        preview = " ".join(getattr(p, "text", "") for p in getattr(item, "content", []))[:200]
        await self._put(pk, sk, item.model_dump(mode="json"),
                        item_type=item.type, preview=preview)

    async def add_thread_item(self, thread_id, item, context):
        await self.save_item(thread_id, item, context)

    async def load_item(self, thread_id, item_id, context):
        pointer = await self._get(self._pk(thread_id), f"ID#{item_id}")
        row = await self._get(self._pk(thread_id), pointer["item_key"]) if pointer else None
        if row is None:
            raise NotFoundError(f"Item {item_id} not found in thread {thread_id}")
        return _ITEM.validate_python(await self._decode(row))

    async def load_thread_items(self, thread_id, after, limit, order, context):
        pk = self._pk(thread_id)
        kwargs = {"KeyConditionExpression": Key("pk").eq(pk) & Key("sk").begins_with("ITEM#"),
                  "ConsistentRead": True, "ScanIndexForward": order == "asc"}
        if after:
            pointer = await self._get(pk, f"ID#{after}")
            if pointer is None:
                raise NotFoundError(f"Item {after} not found")
            kwargs["ExclusiveStartKey"] = {"pk": pk, "sk": pointer["item_key"]}
        rows = []
        while len(rows) < limit + 1:
            kwargs["Limit"] = limit + 1 - len(rows)
            response = await self._call("query", **kwargs)
            rows.extend(response.get("Items", []))
            if not response.get("LastEvaluatedKey"):
                break
            kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
        data = [_ITEM.validate_python(await self._decode(r)) for r in rows[:limit]]
        return Page(data=data, has_more=len(rows) > limit,
                    after=data[-1].id if len(rows) > limit else None)

    async def delete_thread_item(self, thread_id, item_id, context):
        pk = self._pk(thread_id)
        pointer = await self._get(pk, f"ID#{item_id}")
        if pointer:
            await self._call("delete_item", Key={"pk": pk, "sk": pointer["item_key"]})
            await self._call("delete_item", Key={"pk": pk, "sk": f"ID#{item_id}"})

    async def delete_thread(self, thread_id, context):
        pk = self._pk(thread_id)
        rows = await self._rows(pk, "", projection="pk, sk")
        # Remove META last so interrupted deletion can be retried.
        for row in sorted(rows, key=lambda r: r["sk"] == "META"):
            await self._call("delete_item", Key={"pk": pk, "sk": row["sk"]})

    async def add_trace(self, thread_id, trace):
        await self._put(self._pk(thread_id), f"TRACE#{trace['timestamp']}#{uuid4().hex}", trace,
                        agents=[n["agent"] for n in trace.get("nodes", [])])

    async def load_traces(self, thread_id):
        return [await self._decode(row) for row in await self._rows(self._pk(thread_id), "TRACE#")]

    async def get_language(self, thread_id):
        row = await self._get(self._pk(thread_id), "LANG")
        return row["language"] if row else "en"

    async def set_language(self, thread_id, language):
        await self._call("put_item", Item={"pk": self._pk(thread_id), "sk": "LANG", "language": language})

    async def history_summary(self, thread_id):
        pk = self._pk(thread_id)
        rows = await self._rows(pk, "ITEM#", projection="sk, item_type, preview")
        first = next((r["preview"] for r in rows if r["item_type"] == "user_message"), "")
        response = await self._call("query", KeyConditionExpression=Key("pk").eq(pk) & Key("sk").begins_with("TRACE#"),
                                    ConsistentRead=True, ScanIndexForward=False, Limit=1,
                                    ProjectionExpression="agents")
        traces = response.get("Items", [])
        return {"item_count": len(rows), "first_message": first,
                "agents": traces[0]["agents"] if traces else []}


def create_chat_store():
    from app.core.config import CHAT_BACKEND, CHAT_DDB_TABLE, AWS_REGION_NAME
    if CHAT_BACKEND == "memory":
        return InMemoryStore()
    if CHAT_BACKEND == "dynamodb":
        return DynamoDBStore(CHAT_DDB_TABLE, AWS_REGION_NAME)
    raise ValueError("CHAT_BACKEND must be memory or dynamodb")
