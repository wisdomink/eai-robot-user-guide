"""Shared, model-free retrieval for chat and website search."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from openai import AsyncOpenAI
from app.services.manuals_index import matches_filter


@dataclass(frozen=True)
class Evidence:
    file_id: str
    filename: str
    text: str
    score: float
    attributes: dict[str, Any]
    vector_store_id: str


class RetrievalService:
    def __init__(self, client: AsyncOpenAI) -> None:
        self.client = client

    async def search(
        self, query: str, *, vector_store_id: str, limit: int = 6,
        rewrite_query: bool = False, product_key: str | None = None,
        filters: dict | None = None,
    ) -> list[Evidence]:
        if not query.strip() or not vector_store_id:
            return []
        page = await self.client.vector_stores.search(
            vector_store_id=vector_store_id, query=query.strip(),
            max_num_results=max(1, min(limit, 50)), rewrite_query=rewrite_query,
            **({"filters": filters} if filters else {}),
        )
        results = []
        seen = set()
        for hit in sorted(page.data, key=lambda h: h.score, reverse=True):
            attributes = hit.attributes or {}
            if filters and not matches_filter(attributes, filters):
                continue
            # Legacy dedicated stores may lack attributes. Reject explicit mismatches.
            if product_key and attributes.get("product_id") not in (None, "", product_key):
                continue
            text = "\n\n".join(c.text for c in hit.content if c.type == "text").strip()
            key = (hit.file_id, text)
            if not text or key in seen:
                continue
            seen.add(key)
            results.append(Evidence(hit.file_id, hit.filename, text, hit.score, attributes, vector_store_id))
        return results
