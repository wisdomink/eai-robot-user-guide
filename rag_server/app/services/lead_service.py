from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


class LeadStorage:
    """Persist and query lead data from a local JSONL file."""

    def __init__(self, leads_dir: Path) -> None:
        self._leads_dir = leads_dir
        self._leads_dir.mkdir(parents=True, exist_ok=True)
        self._leads_file = self._leads_dir / "leads.jsonl"

    @staticmethod
    def _normalize_payload(payload: dict) -> dict:
        normalized: dict[str, str] = {}
        for key, value in payload.items():
            if value is None:
                continue
            if isinstance(value, str):
                normalized[key] = value.strip()
            else:
                normalized[key] = str(value)
        return normalized

    def save_lead(self, thread_id: str, payload: dict) -> dict:
        lead = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "thread_id": thread_id,
            **self._normalize_payload(payload),
        }
        with open(self._leads_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(lead, ensure_ascii=False) + "\n")
        return lead

    def list_leads(self) -> list[dict]:
        if not self._leads_file.exists():
            return []

        rows: list[dict] = []
        with open(self._leads_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    logger.warning("Skip invalid lead jsonl line: %r", line[:120])

        rows.reverse()
        return rows
