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
    AGENT_BUILDER_WORKFLOW_ID,
    CHAT_MODE,
    OPENAI_API_KEY,
    OPENAI_VECTOR_STORE_ROBOT_ALL_ID,
    SIDEBAR_PATH,
)
from app.services.chatkit_handler import create_chatkit_server

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FF Robot ChatKit Service",
    version="3.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── ChatKit (backend mode) ─────────────────────────────────────────────────

chatkit_server = create_chatkit_server()


@app.post("/chatkit")
async def chatkit_endpoint(request: Request):
    """Self-hosted ChatKit protocol endpoint (used when CHAT_MODE=backend)."""
    result = await chatkit_server.process(await request.body(), context={})
    if isinstance(result, StreamingResult):
        return StreamingResponse(result, media_type="text/event-stream")
    return Response(content=result.json, media_type="application/json")


# ── ChatKit session (agent-builder mode) ───────────────────────────────────

_oai_sync = None


def _get_sync_client():
    global _oai_sync
    if _oai_sync is None:
        from openai import OpenAI
        _oai_sync = OpenAI(api_key=OPENAI_API_KEY)
    return _oai_sync


@app.post("/api/chatkit/session")
async def create_chatkit_session(request: Request):
    """Create a ChatKit session backed by the Agent Builder workflow.
    Returns a client_secret for the frontend to connect directly to OpenAI."""
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass

    user_id = body.get("user", "anonymous")

    try:
        client = _get_sync_client()
        session = client.chatkit.sessions.create(
            workflow={"id": AGENT_BUILDER_WORKFLOW_ID},
            user=user_id,
        )
        return {"client_secret": session.client_secret}
    except Exception as exc:
        logger.error("Failed to create ChatKit session: %s", exc)
        return Response(
            content=json.dumps({"error": str(exc)}),
            status_code=500,
            media_type="application/json",
        )


@app.get("/api/chat-mode")
async def get_chat_mode():
    """Let the frontend know which chat mode the server is configured for."""
    return {"mode": CHAT_MODE}


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


@app.get("/search/debug")
async def search_debug():
    """Diagnostic endpoint: verify search-related config (no secrets exposed)."""
    sidebar_exists = SIDEBAR_PATH.exists()
    return {
        "has_vector_store_id": bool(OPENAI_VECTOR_STORE_ROBOT_ALL_ID),
        "vector_store_id_prefix": OPENAI_VECTOR_STORE_ROBOT_ALL_ID[:8] + "..." if OPENAI_VECTOR_STORE_ROBOT_ALL_ID else None,
        "sidebar_path": str(SIDEBAR_PATH),
        "sidebar_exists": sidebar_exists,
        "file_info_map_count": len(_FILE_INFO_MAP),
    }


@app.get("/search")
async def search_endpoint(
    q: str = Query("", description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Max results"),
    debug: bool = Query(False, description="Include diagnostic info"),
):
    """Semantic search via OpenAI Vector Store Search API."""
    diag: dict = {}

    if not q.strip():
        return {"results": []}

    if not OPENAI_VECTOR_STORE_ROBOT_ALL_ID:
        return {
            "results": [],
            "error": "OPENAI_VECTOR_STORE_ROBOT_ALL_ID not configured",
            "debug": {
                "stage": "config",
                "has_api_key": bool(OPENAI_API_KEY),
                "sidebar_exists": SIDEBAR_PATH.exists(),
                "file_info_map_count": len(_FILE_INFO_MAP),
            },
        }

    try:
        page = await _oai.vector_stores.search(
            vector_store_id=OPENAI_VECTOR_STORE_ROBOT_ALL_ID,
            query=q.strip(),
            max_num_results=limit,
            rewrite_query=True,
        )
    except Exception as exc:
        logger.error("Vector Store Search failed: %s", exc)
        return {
            "results": [],
            "error": str(exc),
            "debug": {
                "stage": "vector_store_search",
                "vector_store_id_prefix": OPENAI_VECTOR_STORE_ROBOT_ALL_ID[:8] + "...",
                "exception_type": type(exc).__name__,
            },
        }

    skipped = []
    results = []
    for item in page.data:
        file_info = _FILE_INFO_MAP.get(item.filename)
        if not file_info:
            skipped.append({"filename": item.filename, "score": round(item.score, 4)})
            logger.warning("No mapping for filename=%r (score=%.4f). Available keys sample: %s",
                           item.filename, item.score, list(_FILE_INFO_MAP.keys())[:5])
            continue

        full_text = " ".join(c.text for c in item.content if c.type == "text")
        section_title, heading_anchor = _extract_heading(full_text)

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

    response: dict = {"results": results}

    if debug or not results:
        response["debug"] = {
            "stage": "complete",
            "vector_store_id_prefix": OPENAI_VECTOR_STORE_ROBOT_ALL_ID[:8] + "...",
            "raw_results_count": len(page.data),
            "mapped_count": len(results),
            "skipped": skipped,
            "file_info_map_count": len(_FILE_INFO_MAP),
            "sidebar_path": str(SIDEBAR_PATH),
            "sidebar_exists": SIDEBAR_PATH.exists(),
        }

    logger.info("Search q=%r → %d results (skipped %d)", q, len(results), len(skipped))
    return response


# ── Health ────────────────────────────────────────────────────────────────


@app.get("/health")
async def health():
    return {"status": "ok", "version": app.version}
