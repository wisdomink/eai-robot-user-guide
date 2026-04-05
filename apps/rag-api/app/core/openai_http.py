"""Shared OpenAI AsyncOpenAI + httpx settings for ChatKit (Agents SDK) and HTTP APIs."""

from __future__ import annotations

import httpx
from openai import AsyncOpenAI

from app.core.config import (
    OPENAI_API_KEY,
    OPENAI_HTTP_CONNECT_TIMEOUT,
    OPENAI_HTTP_READ_TIMEOUT,
)


def create_async_openai_client(
    *,
    read_timeout: float | None = None,
    connect_timeout: float | None = None,
) -> AsyncOpenAI:
    """AsyncOpenAI with explicit httpx timeouts (SDK default connect=5s often causes ConnectTimeout)."""
    read = OPENAI_HTTP_READ_TIMEOUT if read_timeout is None else read_timeout
    connect = OPENAI_HTTP_CONNECT_TIMEOUT if connect_timeout is None else connect_timeout
    return AsyncOpenAI(
        api_key=OPENAI_API_KEY,
        http_client=httpx.AsyncClient(
            limits=httpx.Limits(
                max_connections=100,
                max_keepalive_connections=20,
                keepalive_expiry=60,
            ),
            timeout=httpx.Timeout(timeout=read, connect=connect),
        ),
    )


_agents_client: AsyncOpenAI | None = None


def configure_agents_default_openai_client() -> AsyncOpenAI:
    """Register a single long-timeout client for OpenAI Agents SDK (Runner.run / ChatKit)."""
    global _agents_client
    if _agents_client is None:
        from agents import set_default_openai_client

        _agents_client = create_async_openai_client()
        set_default_openai_client(_agents_client, use_for_tracing=True)
    return _agents_client
