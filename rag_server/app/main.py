"""
FastAPI entry-point for the FF Robot ChatKit + Search service.

- ChatKit: bridges the ChatKit protocol to the Agents SDK.
- Search:  semantic search via OpenAI Vector Store Search API.

    uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

import json
import logging
import re

from fastapi import FastAPI, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI

from chatkit.server import StreamingResult

from app.core.config import (
    OPENAI_API_KEY,
    OPENAI_VECTOR_STORE_ROBOT_ALL_ID,
    SIDEBAR_PATH,
)
from app.services.chatkit_handler import create_chatkit_server

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FF Robot ChatKit Service",
    version="3.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── ChatKit ───────────────────────────────────────────────────────────────

chatkit_server = create_chatkit_server()


@app.post("/chatkit")
async def chatkit_endpoint(request: Request):
    """Single endpoint that handles all ChatKit protocol requests
    (threads, messages, streaming responses)."""
    result = await chatkit_server.process(await request.body(), context={})
    if isinstance(result, StreamingResult):
        return StreamingResponse(result, media_type="text/event-stream")
    return Response(content=result.json, media_type="application/json")


# ── Semantic Search (OpenAI Vector Store Search) ──────────────────────────

_oai = AsyncOpenAI(api_key=OPENAI_API_KEY)


def _to_anchor(heading: str) -> str:
    """Must match the frontend toAnchor() in chunks.ts / MarkdownRenderer."""
    result = heading.lower()
    result = re.sub(r"[^a-z0-9\s-]", "", result)
    result = re.sub(r"\s+", "-", result)
    result = re.sub(r"^-|-$", "", result)
    return result


def _build_file_info_map() -> dict[str, dict]:
    """Build {filename: {slug, title, sectionId}} from sidebar.json."""
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
                info = {
                    "slug": page["slug"],
                    "title": page["title"],
                    "sectionId": section["id"],
                }
                result[page["file"]] = info
                basename = page["file"].rsplit("/", 1)[-1]
                result[basename] = info
    return result


_FILE_INFO_MAP = _build_file_info_map()


def _extract_heading(text: str) -> tuple[str, str]:
    """Try to extract the first ## heading from a content chunk.
    Returns (sectionTitle, headingAnchor)."""
    match = re.search(r"^##\s+(.+)$", text, re.MULTILINE)
    if match:
        title = match.group(1).strip()
        return title, _to_anchor(title)
    return "", ""


@app.get("/search")
async def search_endpoint(
    q: str = Query("", description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Max results"),
):
    """Semantic search via OpenAI Vector Store Search API."""
    if not q.strip():
        return {"results": []}

    if not OPENAI_VECTOR_STORE_ROBOT_ALL_ID:
        return {"results": [], "error": "OPENAI_VECTOR_STORE_ROBOT_ALL_ID not configured"}

    try:
        page = await _oai.vector_stores.search(
            vector_store_id=OPENAI_VECTOR_STORE_ROBOT_ALL_ID,
            query=q.strip(),
            max_num_results=limit,
            rewrite_query=True,
        )
    except Exception as exc:
        logger.error("Vector Store Search failed: %s", exc)
        return {"results": [], "error": str(exc)}

    results = []
    for item in page.data:
        file_info = _FILE_INFO_MAP.get(item.filename)
        if not file_info:
            logger.warning("No mapping for filename=%r (score=%.4f). Available keys sample: %s",
                           item.filename, item.score, list(_FILE_INFO_MAP.keys())[:5])
            continue

        full_text = " ".join(c.text for c in item.content if c.type == "text")
        section_title, heading_anchor = _extract_heading(full_text)

        # Clean markdown syntax for the preview
        preview = re.sub(r"^#{1,6}\s+", "", full_text, flags=re.MULTILINE)
        preview = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", preview)
        preview = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", preview)
        preview = re.sub(r"\s+", " ", preview).strip()[:200]

        results.append({
            "pageSlug": file_info["slug"],
            "pageTitle": file_info["title"],
            "sectionTitle": section_title or file_info["title"],
            "sectionId": file_info["sectionId"],
            "headingAnchor": heading_anchor,
            "textPreview": preview,
            "similarity": round(item.score, 4),
        })

    response = {"results": results}
    logger.info("Search q=%r → %d results: %s", q, len(results), json.dumps(response, ensure_ascii=False, indent=2))
    return response


# ── Health ────────────────────────────────────────────────────────────────


@app.get("/health")
async def health():
    return {"status": "ok"}
