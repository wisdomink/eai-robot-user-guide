"""
FastAPI entry-point for the FF Robot RAG service.

    uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

import json
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.rag_engine import rag_engine


# ── Lifespan ──────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(_app: FastAPI):
    rag_engine.initialize()
    yield


app = FastAPI(
    title="FF Robot RAG Service",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Schemas ───────────────────────────────────────────────────────────────


class ChatRequest(BaseModel):
    query: str


class SourceItem(BaseModel):
    title: str
    section: str
    header_path: str
    url_path: str
    file_path: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceItem]


# ── Routes ────────────────────────────────────────────────────────────────


@app.post("/chat")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint (SSE).

    Event types:
      - {"type": "token",   "content": "..."}   incremental answer token
      - {"type": "sources", "sources": [...]}    deduplicated reference list
      - {"type": "done"}                         stream finished
    """

    async def event_stream():
        async for event in rag_engine.query_stream(request.query):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/chat/sync", response_model=ChatResponse)
async def chat_sync(request: ChatRequest):
    """Non-streaming chat — returns the full answer in one JSON response."""
    result = await rag_engine.query(request.query)
    return result


@app.post("/reindex")
async def reindex():
    """Force rebuild the vector index from current Markdown files."""
    rag_engine.reindex()
    return {"status": "ok", "message": "Index rebuilt successfully."}


@app.get("/health")
async def health():
    return {"status": "ok"}
