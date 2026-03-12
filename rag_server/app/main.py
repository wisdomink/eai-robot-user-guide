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
import time
import traceback

import httpx
from fastapi import FastAPI, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI

from chatkit.server import StreamingResult

from app.core.config import (
    AGENT_BUILDER_WORKFLOW_ID,
    OPENAI_API_KEY,
    OPENAI_VECTOR_STORE_ROBOT_ALL_ID,
    SIDEBAR_PATH,
)
from app.core.logging_config import setup_logging
from app.services.chatkit_handler import create_chatkit_server

setup_logging()
logger = logging.getLogger(__name__)
api_logger = logging.getLogger("api")

_MAX_BODY_LOG = 4000

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


# ── Helpers ───────────────────────────────────────────────────────────────


def _summarize_chatkit_body(raw: bytes) -> str:
    """Extract key fields from a ChatKit protocol JSON body for logging."""
    try:
        obj = json.loads(raw)
    except Exception:
        return raw.decode("utf-8", errors="replace")[:500]
    msg_type = obj.get("type", "?")
    thread_id = obj.get("thread_id", "?")

    user_text = ""
    for item in obj.get("items", []):
        if item.get("type") == "user_message":
            parts = item.get("content", [])
            user_text = " ".join(p.get("text", "") for p in parts).strip()[:200]
            break
    if not user_text:
        content = obj.get("content", [])
        if isinstance(content, list):
            user_text = " ".join(p.get("text", "") for p in content).strip()[:200]

    parts = [f"type={msg_type}", f"thread={thread_id}"]
    if user_text:
        parts.append(f"user_msg={user_text!r}")
    return "  ".join(parts)


# ── ChatKit (backend mode) ─────────────────────────────────────────────────

chatkit_server = create_chatkit_server()


@app.post("/chatkit")
async def chatkit_endpoint(request: Request):
    """Self-hosted ChatKit protocol endpoint (used when CHAT_MODE=backend)."""
    start = time.perf_counter()
    body = await request.body()

    summary = _summarize_chatkit_body(body)
    api_logger.info(">>> POST /chatkit  %s", summary)
    api_logger.debug(">>> POST /chatkit  raw_body=%s", body.decode("utf-8", errors="replace")[:_MAX_BODY_LOG])

    try:
        result = await chatkit_server.process(body, context={})
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        api_logger.error(
            "<<< POST /chatkit  status=500  elapsed=%.1fms  error=%s\n%s",
            elapsed_ms, exc, traceback.format_exc(),
        )
        raise

    elapsed_ms = (time.perf_counter() - start) * 1000

    if isinstance(result, StreamingResult):
        api_logger.info("<<< POST /chatkit  status=200  response=SSE_STREAM  elapsed=%.1fms", elapsed_ms)
        return StreamingResponse(result, media_type="text/event-stream")

    resp_json = result.json
    api_logger.info(
        "<<< POST /chatkit  status=200  response=JSON  elapsed=%.1fms  body=%s",
        elapsed_ms, resp_json[:_MAX_BODY_LOG],
    )
    return Response(content=resp_json, media_type="application/json")


# ── ChatKit session (agent-builder mode) ───────────────────────────────────

_oai_sync = None


def _get_sync_client():
    global _oai_sync
    if _oai_sync is None:
        import httpx as _httpx_sync
        from openai import OpenAI
        _oai_sync = OpenAI(
            api_key=OPENAI_API_KEY,
            http_client=_httpx_sync.Client(
                limits=_httpx_sync.Limits(
                    max_connections=100,
                    max_keepalive_connections=20,
                    keepalive_expiry=60,
                ),
                timeout=_httpx_sync.Timeout(timeout=30.0, connect=10.0),
            ),
        )
    return _oai_sync


@app.post("/api/chatkit/session")
async def create_chatkit_session(request: Request):
    """Create a ChatKit session backed by the Agent Builder workflow.
    Returns a client_secret for the frontend to connect directly to OpenAI."""
    start = time.perf_counter()

    body = {}
    try:
        body = await request.json()
    except Exception:
        pass

    user_id = body.get("user", "anonymous")
    api_logger.info(">>> POST /api/chatkit/session  user=%s  body=%s", user_id, json.dumps(body))

    try:
        client = _get_sync_client()
        session = client.chatkit.sessions.create(
            workflow={"id": AGENT_BUILDER_WORKFLOW_ID},
            user=user_id,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        api_logger.info(
            "<<< POST /api/chatkit/session  status=200  user=%s  elapsed=%.1fms  secret_prefix=%s…",
            user_id, elapsed_ms, session.client_secret[:12],
        )
        return {"client_secret": session.client_secret}
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        api_logger.error(
            "<<< POST /api/chatkit/session  status=500  user=%s  elapsed=%.1fms  error=%s",
            user_id, elapsed_ms, exc,
        )
        return Response(
            content=json.dumps({"error": str(exc)}),
            status_code=500,
            media_type="application/json",
        )


# ── Semantic Search (OpenAI Vector Store Search) ──────────────────────────

_oai = AsyncOpenAI(
    api_key=OPENAI_API_KEY,
    http_client=httpx.AsyncClient(
        limits=httpx.Limits(
            max_connections=100,
            max_keepalive_connections=20,
            keepalive_expiry=60,
        ),
        timeout=httpx.Timeout(timeout=30.0, connect=10.0),
    ),
)


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
    start = time.perf_counter()
    api_logger.info(">>> GET /search  q=%r  limit=%d", q, limit)

    if not q.strip():
        api_logger.info("<<< GET /search  status=200  q=<empty>  results=0  elapsed=%.1fms", (time.perf_counter() - start) * 1000)
        return {"results": []}

    if not OPENAI_VECTOR_STORE_ROBOT_ALL_ID:
        resp = {
            "results": [],
            "error": "OPENAI_VECTOR_STORE_ROBOT_ALL_ID not configured",
            "debug": {
                "stage": "config",
                "has_api_key": bool(OPENAI_API_KEY),
                "sidebar_exists": SIDEBAR_PATH.exists(),
                "file_info_map_count": len(_FILE_INFO_MAP),
            },
        }
        api_logger.error("<<< GET /search  status=200  error=vector_store_not_configured  elapsed=%.1fms", (time.perf_counter() - start) * 1000)
        return resp

    last_exc: Exception | None = None
    page = None
    for attempt in range(2):
        try:
            page = await _oai.vector_stores.search(
                vector_store_id=OPENAI_VECTOR_STORE_ROBOT_ALL_ID,
                query=q.strip(),
                max_num_results=limit,
                rewrite_query=True,
            )
            break
        except Exception as exc:
            last_exc = exc
            api_logger.warning("GET /search  vector_store attempt %d failed: %s", attempt + 1, exc)
    if page is None:
        elapsed_ms = (time.perf_counter() - start) * 1000
        api_logger.error(
            "<<< GET /search  status=200  q=%r  error=%s(%s)  elapsed=%.1fms",
            q, type(last_exc).__name__, last_exc, elapsed_ms,
        )
        return {
            "results": [],
            "error": str(last_exc),
            "debug": {
                "stage": "vector_store_search",
                "vector_store_id_prefix": OPENAI_VECTOR_STORE_ROBOT_ALL_ID[:8] + "...",
                "exception_type": type(last_exc).__name__,
            },
        }

    skipped = []
    results = []
    for item in page.data:
        file_info = _FILE_INFO_MAP.get(item.filename)
        if not file_info:
            skipped.append({"filename": item.filename, "score": round(item.score, 4)})
            api_logger.warning("GET /search  unmapped filename=%r score=%.4f", item.filename, item.score)
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

    response: dict = {
        "results": results,
        "debug": {
            "stage": "complete",
            "vector_store_id_prefix": OPENAI_VECTOR_STORE_ROBOT_ALL_ID[:8] + "...",
            "raw_results_count": len(page.data),
            "mapped_count": len(results),
            "skipped": skipped,
            "file_info_map_count": len(_FILE_INFO_MAP),
            "sidebar_path": str(SIDEBAR_PATH),
            "sidebar_exists": SIDEBAR_PATH.exists(),
        },
    }

    elapsed_ms = (time.perf_counter() - start) * 1000
    api_logger.info(
        "<<< GET /search  status=200  q=%r  raw=%d  mapped=%d  skipped=%d  elapsed=%.1fms  response=%s",
        q, len(page.data), len(results), len(skipped), elapsed_ms,
        json.dumps(response, ensure_ascii=False)[:_MAX_BODY_LOG],
    )
    return response


# ── Startup warmup ────────────────────────────────────────────────────────


@app.on_event("startup")
async def warmup():
    """Pre-warm external connections so the first real request doesn't pay
    the cold-start penalty (DNS resolution, TLS handshake, etc.)."""
    try:
        await _oai.models.list()
        logger.info("Startup warmup: OpenAI connection established")
    except Exception as exc:
        logger.warning("Startup warmup failed (non-fatal): %s", exc)


# ── Health ────────────────────────────────────────────────────────────────


@app.get("/health")
async def health():
    api_logger.debug("GET /health → 200")
    return {"status": "ok", "version": app.version}
