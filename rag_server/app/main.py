"""
FastAPI entry-point for the FF Robot ChatKit session service.

Creates ChatKit sessions backed by an Agent Builder workflow.
The OpenAI platform hosts inference; this server only mints sessions.

    uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

from app.core.config import OPENAI_API_KEY, OPENAI_WORKFLOW_ID

logger = logging.getLogger(__name__)

app = FastAPI(
    title="FF Robot ChatKit Session Service",
    version="4.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=OPENAI_API_KEY)


@app.post("/api/chatkit/session")
async def create_session():
    """Create a ChatKit session and return its client_secret.

    The frontend uses this secret to communicate directly with
    OpenAI's hosted ChatKit endpoint (no proxy needed).
    """
    try:
        session = client.beta.chatkit.sessions.create(
            user="anonymous",
            workflow={"id": OPENAI_WORKFLOW_ID},
        )
        return {"client_secret": session.client_secret}
    except Exception as e:
        logger.exception("Failed to create ChatKit session")
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "ok"}
