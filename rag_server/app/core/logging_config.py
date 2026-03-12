"""
Centralized logging configuration with rotating file handlers and smart alerting.

Log files are stored in LOG_DIR (default: rag_server/logs/) with automatic
rotation to prevent unbounded growth:
  - app.log    — general application log (INFO+)
  - chat.log   — chat conversation log (user queries, triage results, responses)
  - error.log  — errors only (WARNING+), useful for quick triage

Each file rotates at LOG_MAX_BYTES (default 10 MB) and keeps LOG_BACKUP_COUNT
(default 5) compressed backups, giving ~60 MB total per log stream.

When ALERT_ENABLED=true, a SmartAlertHandler sends email notifications for
ERROR/CRITICAL logs with surrounding context, deduplication, and rate limiting.
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler

from app.core.config import (
    ALERT_ENABLED,
    ALERT_LEVEL,
    ALERT_SMTP_HOST,
    ALERT_TO_EMAILS,
    LOG_BACKUP_COUNT,
    LOG_DIR,
    LOG_LEVEL,
    LOG_MAX_BYTES,
)

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
_LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

CHAT_LOGGER_NAME = "chat"
API_LOGGER_NAME = "api"


def _make_rotating_handler(
    filename: str,
    level: int = logging.DEBUG,
) -> RotatingFileHandler:
    handler = RotatingFileHandler(
        LOG_DIR / filename,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_LOG_DATE_FORMAT))
    return handler


def setup_logging() -> None:
    """Call once at application startup (before any logger is used)."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(LOG_LEVEL)

    # Remove any pre-existing handlers (e.g. from basicConfig)
    root.handlers.clear()

    # Console — always enabled so Docker/supervisord can still capture stdout
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(LOG_LEVEL)
    console.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_LOG_DATE_FORMAT))
    root.addHandler(console)

    # app.log — all application messages
    root.addHandler(_make_rotating_handler("app.log", level=logging.DEBUG))

    # error.log — warnings and above for quick triage
    root.addHandler(_make_rotating_handler("error.log", level=logging.WARNING))

    # chat.log — dedicated chat conversation logger
    chat_logger = logging.getLogger(CHAT_LOGGER_NAME)
    chat_logger.propagate = True  # also appears in app.log
    chat_logger.addHandler(_make_rotating_handler("chat.log", level=logging.DEBUG))

    # api.log — request / response logger for all API endpoints
    api_logger = logging.getLogger(API_LOGGER_NAME)
    api_logger.propagate = True
    api_logger.addHandler(_make_rotating_handler("api.log", level=logging.DEBUG))

    # Email alert handler (optional, enabled via ALERT_ENABLED=true)
    if ALERT_ENABLED and ALERT_SMTP_HOST and ALERT_TO_EMAILS:
        from app.core.alert_handler import SmartAlertHandler

        alert_level = getattr(logging, ALERT_LEVEL, logging.ERROR)
        alert_handler = SmartAlertHandler(level=alert_level)
        root.addHandler(alert_handler)
        root.info(
            "Email alert handler enabled (level=%s, recipients=%s)",
            ALERT_LEVEL, ", ".join(ALERT_TO_EMAILS),
        )
    elif ALERT_ENABLED:
        root.warning(
            "ALERT_ENABLED=true but ALERT_SMTP_HOST or ALERT_TO_EMAILS not set — "
            "email alerts disabled"
        )

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
