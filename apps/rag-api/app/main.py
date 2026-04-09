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

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from chatkit.server import StreamingResult

from app.core.config import (
    LOG_DIR,
    OPENAI_API_KEY,
    OPENAI_VECTOR_STORE_ROBOT_ALL_ID,
    SIDEBAR_PATH,
)
from app.core.logging_config import setup_logging
from app.core.openai_http import configure_agents_default_openai_client, create_async_openai_client
from app.services.chatkit_handler import create_chatkit_server
from app.services.homepage_prompts_service import HomepagePromptsStorage
from app.services.lead_service import LeadStorage
from app.services.recommendation_catalog_service import RecommendationCatalogStorage

setup_logging()
configure_agents_default_openai_client()
logger = logging.getLogger(__name__)
front_logger = logging.getLogger("front")
sys_logger = logging.getLogger("system")

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

lead_storage = LeadStorage.from_config()
recommendation_storage = RecommendationCatalogStorage.from_config()
homepage_prompts_storage = HomepagePromptsStorage.from_config()
chatkit_server = create_chatkit_server(
    lead_storage=lead_storage,
    recommendation_storage=recommendation_storage,
)


class LeadCreateRequest(BaseModel):
    product: str = Field("", description="Product ID")
    contact_name: str = Field("", description="User contact name")
    email: str = Field("", description="User email")
    phone: str = Field("", description="User phone number")
    thread_id: str = Field("", description="Optional chat thread ID")


class RecommendationCatalogItemRequest(BaseModel):
    id: str = Field("", description="Recommendation ID (auto-generated if omitted)")
    enabled: bool = Field(True, description="Whether this recommendation is enabled")
    product_name: str = Field("", description="Product name")
    trigger_scene: str = Field("", description="Trigger scene")
    recommendation_content_cn: str = Field("", description="Chinese recommendation content")
    recommendation_content_en: str = Field("", description="English recommendation content")


class HomepagePromptRequest(BaseModel):
    id: str = Field("", description="Prompt ID (auto-generated if omitted)")
    enabled: bool = Field(True, description="Whether this prompt is visible on the homepage")
    label: str = Field("", description="Button label shown on the homepage")
    prompt: str = Field("", description="Full prompt text sent to ChatKit on click")
    sort_order: int = Field(0, description="Sort weight (lower = higher in list)")


class HomepageSettingsRequest(BaseModel):
    greeting: str | None = Field(None, description="Welcome title shown above prompt buttons")
    placeholder: str | None = Field(None, description="Placeholder text for the input box")
    info_text: str | None = Field(None, description="Informational text shown below prompt buttons")


class LeadCaptureTriageConfigPayload(BaseModel):
    """Merge into recommendations.json: lead_capture fields + optional keyword lists for triage."""

    lead_capture: dict = Field(default_factory=dict)
    purchase_intent_keywords: dict | None = Field(
        None,
        description="If set, replaces purchase_intent_keywords.cn / .en arrays",
    )


@app.post("/api/chatkit")
async def chatkit_endpoint(request: Request):
    """Self-hosted ChatKit protocol endpoint (used when CHAT_MODE=backend)."""
    start = time.perf_counter()
    body = await request.body()

    summary = _summarize_chatkit_body(body)
    front_logger.info(">>> POST /api/chatkit  %s", summary)
    front_logger.debug(">>> POST /api/chatkit  raw_body=%s", body.decode("utf-8", errors="replace")[:_MAX_BODY_LOG])

    try:
        result = await chatkit_server.process(body, context={})
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        front_logger.error(
            "<<< POST /api/chatkit  status=500  elapsed=%.1fms  error=%s\n%s",
            elapsed_ms, exc, traceback.format_exc(),
        )
        raise

    elapsed_ms = (time.perf_counter() - start) * 1000

    if isinstance(result, StreamingResult):
        front_logger.info("<<< POST /api/chatkit  status=200  response=SSE_STREAM  elapsed=%.1fms", elapsed_ms)
        return StreamingResponse(result, media_type="text/event-stream")

    resp_json = result.json
    front_logger.info(
        "<<< POST /api/chatkit  status=200  response=JSON  elapsed=%.1fms  body=%s",
        elapsed_ms, resp_json[:_MAX_BODY_LOG],
    )
    return Response(content=resp_json, media_type="application/json")


# ── Semantic Search (OpenAI Vector Store Search) ──────────────────────────

# Semantic search: shorter read timeout than Agents (ChatKit); connect uses OPENAI_HTTP_CONNECT_TIMEOUT.
_oai = create_async_openai_client(read_timeout=30.0)


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


@app.get("/api/search")
async def search_endpoint(
    q: str = Query("", description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Max results"),
):
    """Semantic search via OpenAI Vector Store Search API."""
    start = time.perf_counter()
    front_logger.info(">>> GET /api/search  q=%r  limit=%d", q, limit)

    if not q.strip():
        front_logger.info("<<< GET /api/search  status=200  q=<empty>  results=0  elapsed=%.1fms", (time.perf_counter() - start) * 1000)
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
        front_logger.error("<<< GET /api/search  status=200  error=vector_store_not_configured  elapsed=%.1fms", (time.perf_counter() - start) * 1000)
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
            front_logger.warning("GET /api/search  vector_store attempt %d failed: %s", attempt + 1, exc)
    if page is None:
        elapsed_ms = (time.perf_counter() - start) * 1000
        front_logger.error(
            "<<< GET /api/search  status=200  q=%r  error=%s(%s)  elapsed=%.1fms",
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
            front_logger.warning("GET /api/search  unmapped filename=%r score=%.4f", item.filename, item.score)
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
    front_logger.info(
        "<<< GET /api/search  status=200  q=%r  raw=%d  mapped=%d  skipped=%d  elapsed=%.1fms  response=%s",
        q, len(page.data), len(results), len(skipped), elapsed_ms,
        json.dumps(response, ensure_ascii=False)[:_MAX_BODY_LOG],
    )
    return response


# ── Homepage Prompts API ──────────────────────────────────────────────────


@app.get("/api/get-homepage-prompts")
async def get_homepage_prompts(
    all: bool = Query(False, description="Include disabled prompts (for admin)"),
):
    """Return homepage prompt buttons (enabled-only by default, all for admin)."""
    config = homepage_prompts_storage.get_homepage_config(include_disabled=all)
    front_logger.info(
        "GET /api/get-homepage-prompts  all=%s  count=%d",
        all, len(config["prompts"]),
    )
    return config


@app.post("/api/save-homepage-settings")
async def save_homepage_settings(payload: HomepageSettingsRequest):
    """Update page-level settings: greeting title and input placeholder."""
    settings = homepage_prompts_storage.save_settings(
        greeting=payload.greeting,
        placeholder=payload.placeholder,
        info_text=payload.info_text,
    )
    front_logger.info(
        "POST /api/save-homepage-settings  greeting=%r  placeholder=%r",
        settings.get("greeting", "")[:60],
        settings.get("placeholder", "")[:60],
    )
    return {"ok": True, "settings": settings}


@app.post("/api/save-homepage-prompt")
async def save_homepage_prompt(payload: HomepagePromptRequest):
    """Create or update a homepage prompt entry."""
    try:
        prompt, created = homepage_prompts_storage.save_or_update_prompt(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    front_logger.info(
        "POST /api/save-homepage-prompt  id=%s created=%s label=%s",
        prompt["id"], created, prompt.get("label", ""),
    )
    return {"ok": True, "created": created, "prompt": prompt}


@app.delete("/api/delete-homepage-prompt/{prompt_id}")
async def delete_homepage_prompt(prompt_id: str):
    """Delete one homepage prompt entry by id."""
    try:
        deleted = homepage_prompts_storage.delete_prompt(prompt_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if deleted is None:
        raise HTTPException(status_code=404, detail=f"Prompt {prompt_id} not found")

    front_logger.info(
        "DELETE /api/delete-homepage-prompt/%s  label=%s",
        prompt_id, deleted.get("label", ""),
    )
    return {"ok": True, "prompt": deleted}


# ── Chat History API ──────────────────────────────────────────────────────

_ALLOWED_LOGS = {"front.log", "back.log", "system.log"}


def _serialize_item(item) -> dict:
    """Convert a ThreadItem (Pydantic model) to a JSON-friendly dict."""
    data = item.model_dump(mode="json") if hasattr(item, "model_dump") else {}
    text_parts = []
    if hasattr(item, "content") and isinstance(item.content, list):
        for part in item.content:
            t = getattr(part, "text", None)
            if t:
                text_parts.append(t)
    if text_parts:
        data["_text"] = " ".join(text_parts)
    return data


@app.get("/api/chat-history")
async def list_threads(
    request: Request,
    limit: int = Query(50, ge=1, le=200, description="Max threads"),
    order: str = Query("desc", description="Sort order: asc or desc"),
):
    """List all conversation threads (newest first by default)."""
    base_url = str(request.base_url).rstrip("/")
    store = chatkit_server.store
    page = await store.load_threads(limit=limit, after=None, order=order, context={})
    threads = []
    for t in page.data:
        item_count = len(store.items.get(t.id, []))
        first_msg = ""
        for item in store.items.get(t.id, []):
            if getattr(item, "type", None) == "user_message":
                if hasattr(item, "content") and isinstance(item.content, list):
                    first_msg = " ".join(
                        getattr(p, "text", "") for p in item.content
                    ).strip()[:200]
                break
        traces = store.agent_traces.get(t.id, [])
        last_agents = []
        if traces:
            last_agents = [n["agent"] for n in traces[-1].get("nodes", [])]
        threads.append({
            "id": t.id,
            "detail_url": f"{base_url}/api/chat-history/{t.id}",
            "title": t.title,
            "created_at": t.created_at.isoformat(),
            "status": t.status if isinstance(t.status, str) else str(t.status),
            "item_count": item_count,
            "first_message": first_msg,
            "agents": last_agents,
        })
    return {"threads": threads, "total": len(threads), "has_more": page.has_more}


@app.post("/api/post-lead")
async def create_lead(payload: LeadCreateRequest):
    """Persist one lead row to local jsonl file."""
    lead = lead_storage.save_lead(
        thread_id=payload.thread_id,
        payload=payload.model_dump(exclude={"thread_id"}),
    )
    front_logger.info(
        "POST /api/post-lead  product=%s name=%s email=%s",
        lead.get("product", ""),
        lead.get("contact_name", ""),
        lead.get("email", ""),
    )
    return {"ok": True, "lead": lead}


@app.get("/api/get-leads")
async def list_leads():
    """Read all leads from local jsonl file (newest first)."""
    leads = lead_storage.list_leads()
    return {"leads": leads, "total": len(leads)}


@app.get("/api/get-lead-capture-config")
async def get_lead_capture_config():
    """Triage留资触发：lead_capture 文案与 purchase_intent_keywords（写入 recommendations.json）。"""
    return recommendation_storage.get_lead_capture_triage_config()


@app.post("/api/save-lead-capture-config")
async def save_lead_capture_config(payload: LeadCaptureTriageConfigPayload):
    """更新留资 Triage 配置（合并 lead_capture，可选全量替换关键词列表）。"""
    try:
        config = recommendation_storage.save_lead_capture_triage_config(
            payload.lead_capture,
            payload.purchase_intent_keywords,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    front_logger.info(
        "POST /api/save-lead-capture-config  lead_keys=%s  has_keywords=%s",
        list((payload.lead_capture or {}).keys()),
        payload.purchase_intent_keywords is not None,
    )
    return {"ok": True, "config": config}


@app.get("/api/get-recommendations")
async def list_recommendations():
    """Read all recommendation catalog items."""
    try:
        recommendations = recommendation_storage.list_recommendations()
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"recommendations": recommendations, "total": len(recommendations)}


@app.post("/api/save-recommendation")
async def save_recommendation(payload: RecommendationCatalogItemRequest):
    """Create or update a recommendation catalog item by id."""
    try:
        recommendation, created = recommendation_storage.save_or_update_recommendation(
            payload.model_dump()
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    front_logger.info(
        "POST /api/save-recommendation  id=%s created=%s enabled=%s product_name=%s",
        recommendation["id"],
        created,
        recommendation["enabled"],
        recommendation["product_name"],
    )
    return {"ok": True, "created": created, "recommendation": recommendation}


@app.delete("/api/delete-recommendation/{recommendation_id}")
async def delete_recommendation(recommendation_id: str):
    """Delete one recommendation catalog item by id."""
    try:
        deleted = recommendation_storage.delete_recommendation(recommendation_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if deleted is None:
        raise HTTPException(status_code=404, detail=f"Recommendation {recommendation_id} not found")

    front_logger.info(
        "DELETE /api/delete-recommendation/%s  product_name=%s",
        recommendation_id,
        deleted.get("product_name", ""),
    )
    return {"ok": True, "recommendation": deleted}


@app.get("/api/chat-history/{thread_id}")
async def get_thread_detail(thread_id: str):
    """Get all messages in a specific thread."""
    store = chatkit_server.store
    if thread_id not in store.threads:
        return Response(
            content=json.dumps({"error": f"Thread {thread_id} not found"}),
            status_code=404,
            media_type="application/json",
        )
    thread = store.threads[thread_id]
    items_page = await store.load_thread_items(
        thread_id, after=None, limit=500, order="asc", context={}
    )
    return {
        "thread": {
            "id": thread.id,
            "title": thread.title,
            "created_at": thread.created_at.isoformat(),
            "status": thread.status if isinstance(thread.status, str) else str(thread.status),
        },
        "agent_traces": store.agent_traces.get(thread_id, []),
        "items": [_serialize_item(item) for item in items_page.data],
    }


@app.get("/api/logs")
async def list_logs(request: Request):
    """List all available log types with links."""
    base_url = str(request.base_url).rstrip("/")
    logs = []
    for name in sorted(_ALLOWED_LOGS):
        log_path = LOG_DIR / name
        exists = log_path.exists()
        size_bytes = log_path.stat().st_size if exists else 0
        total_lines = log_path.read_text(encoding="utf-8", errors="replace").count("\n") if exists else 0
        logs.append({
            "name": name,
            "url": f"{base_url}/api/logs/{name}",
            "exists": exists,
            "size_bytes": size_bytes,
            "total_lines": total_lines,
        })
    return {"logs": logs}


@app.get("/api/logs/all")
async def read_all_logs(
    tail: int = Query(200, ge=1, le=5000, description="Number of lines per log file"),
):
    """Read the last N lines from every log file, merged and sorted by timestamp."""
    merged: list[tuple[str, str]] = []
    for name in sorted(_ALLOWED_LOGS):
        log_path = LOG_DIR / name
        if not log_path.exists():
            continue
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        for line in lines[-tail:]:
            merged.append((name, line))

    merged.sort(key=lambda x: x[1][:19])

    return {
        "lines": [{"source": src, "text": text} for src, text in merged],
        "total": len(merged),
    }


@app.get("/api/logs/{log_name}")
async def read_log(
    log_name: str,
    tail: int = Query(200, ge=1, le=5000, description="Number of lines from the end"),
):
    """Read the last N lines of a log file. Persists across container restarts."""
    if log_name not in _ALLOWED_LOGS:
        return Response(
            content=json.dumps({"error": f"Unknown log: {log_name}", "allowed": sorted(_ALLOWED_LOGS)}),
            status_code=400,
            media_type="application/json",
        )
    log_path = LOG_DIR / log_name
    if not log_path.exists():
        return {"log": log_name, "lines": [], "total_lines": 0}

    all_lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    selected = all_lines[-tail:]
    return {
        "log": log_name,
        "lines": selected,
        "total_lines": len(all_lines),
        "showing": len(selected),
    }


# ── Startup warmup ────────────────────────────────────────────────────────


@app.on_event("startup")
async def warmup():
    """Pre-warm external connections so the first real request doesn't pay
    the cold-start penalty (DNS resolution, TLS handshake, etc.)."""
    sys_logger.info("Application starting — version=%s", app.version)
    try:
        await _oai.models.list()
        sys_logger.info("Startup warmup: OpenAI connection established")
    except Exception as exc:
        sys_logger.warning("Startup warmup failed (non-fatal): %s", exc)


# ── Health ────────────────────────────────────────────────────────────────


@app.get("/health")
async def health():
    front_logger.debug("GET /health → 200")
    return {"status": "ok", "version": app.version}
