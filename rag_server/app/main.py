"""
FastAPI entry-point for the FF Robot RAG service.

    uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from chatkit.server import StreamingResult

from app.services.chatkit_handler import create_chatkit_server
from app.services.rag_engine import rag_engine


# ── Lifespan ──────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(_app: FastAPI):
    rag_engine.initialize()
    yield


app = FastAPI(
    title="FF Robot RAG Service",
    version="2.0.0",
    lifespan=lifespan,
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


# ── Management Routes ─────────────────────────────────────────────────────


@app.post("/reindex")
async def reindex():
    """Force rebuild the vector index from current Markdown files."""
    rag_engine.reindex()
    return {"status": "ok", "message": "Index rebuilt successfully."}


@app.get("/health")
async def health():
    return {"status": "ok"}
