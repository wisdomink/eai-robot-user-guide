"""
FastAPI entry-point for the FF Robot ChatKit service.

RAG retrieval is handled by OpenAI's hosted file_search tool.
This server only bridges the ChatKit protocol to the Assistants API.

    uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from chatkit.server import StreamingResult

from app.services.chatkit_handler import create_chatkit_server


app = FastAPI(
    title="FF Robot ChatKit Service",
    version="3.0.0",
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


@app.get("/health")
async def health():
    return {"status": "ok"}
