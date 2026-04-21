from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import boto3
import httpx
from boto3.dynamodb.conditions import Key

logger = logging.getLogger(__name__)


class LeadStorage:
    """Persist and query lead data from a local JSONL file or DynamoDB."""

    _DDB_PARTITION_KEY = "LEAD"

    def __init__(
        self,
        leads_dir: Path | None = None,
        *,
        backend: str = "file",
        dynamodb_table: str = "",
        aws_region: str = "",
        forward_url: str = "",
        forward_timeout: float = 10.0,
        forward_source: str = "AI Chat",
    ) -> None:
        self._backend = backend.strip().lower() or "file"
        self._leads_dir = leads_dir
        self._dynamodb_table_name = dynamodb_table.strip()
        self._aws_region = aws_region.strip()
        self._forward_url = forward_url.strip()
        self._forward_timeout = forward_timeout
        self._forward_source = forward_source.strip() or "AI Chat"
        self._dynamodb_table = None

        if self._backend == "dynamodb":
            if not self._dynamodb_table_name:
                raise ValueError("LEADS_DDB_TABLE is required when LEADS_BACKEND=dynamodb")
            resource_kwargs = {}
            if self._aws_region:
                resource_kwargs["region_name"] = self._aws_region
            dynamodb = boto3.resource("dynamodb", **resource_kwargs)
            self._dynamodb_table = dynamodb.Table(self._dynamodb_table_name)
        else:
            if self._leads_dir is None:
                raise ValueError("leads_dir is required when LEADS_BACKEND=file")
            self._leads_dir.mkdir(parents=True, exist_ok=True)
            self._leads_file = self._leads_dir / "leads.jsonl"

    @classmethod
    def from_config(cls) -> LeadStorage:
        from app.core.config import (
            AWS_REGION_NAME,
            LEADS_BACKEND,
            LEADS_DDB_TABLE,
            LEADS_DIR,
            LEADS_FORWARD_SOURCE,
            LEADS_FORWARD_TIMEOUT,
            LEADS_FORWARD_URL,
        )

        return cls(
            LEADS_DIR,
            backend=LEADS_BACKEND,
            dynamodb_table=LEADS_DDB_TABLE,
            aws_region=AWS_REGION_NAME,
            forward_url=LEADS_FORWARD_URL,
            forward_timeout=LEADS_FORWARD_TIMEOUT,
            forward_source=LEADS_FORWARD_SOURCE,
        )

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

    def _forward_payload(self, lead: dict) -> dict:
        return {
            "firstName": lead.get("firstName", ""),
            "lastName": lead.get("lastName", ""),
            "phone": lead.get("phone", ""),
            "email": lead.get("email", ""),
            "source": self._forward_source,
            "product": lead.get("product", ""),
        }

    @staticmethod
    def _normalize_legacy_lead(row: dict) -> dict:
        if row.get("contact_name") and not row.get("firstName") and not row.get("lastName"):
            row = dict(row)
            row["firstName"] = row.get("contact_name", "")
            row["lastName"] = ""
        return row

    def _forward_lead(self, lead: dict) -> None:
        if not self._forward_url:
            return

        payload = self._forward_payload(lead)
        logger.info(
            "Lead forward request: lead_id=%s body=%s",
            lead.get("lead_id", ""),
            json.dumps(payload, ensure_ascii=False),
        )
        try:
            response = httpx.post(
                self._forward_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self._forward_timeout,
            )
            response.raise_for_status()
            logger.info(
                "Lead forward succeeded: lead_id=%s url=%s status=%s",
                lead.get("lead_id", ""),
                self._forward_url,
                response.status_code,
            )
        except httpx.HTTPError as exc:
            reason = str(exc)
            if isinstance(exc, httpx.HTTPStatusError):
                response_text = exc.response.text.strip()
                if response_text:
                    reason = f"{reason} response={response_text[:300]}"
            logger.warning(
                "Lead forward failed: lead_id=%s url=%s error=%s",
                lead.get("lead_id", ""),
                self._forward_url,
                reason,
            )

    def save_lead(self, thread_id: str, payload: dict) -> dict:
        lead = {
            "lead_id": uuid4().hex,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "thread_id": thread_id,
            **self._normalize_payload(payload),
        }

        try:
            if self._backend == "dynamodb":
                assert self._dynamodb_table is not None
                self._dynamodb_table.put_item(
                    Item={
                        "pk": self._DDB_PARTITION_KEY,
                        "sk": f"{lead['timestamp']}#{lead['lead_id']}",
                        **lead,
                    }
                )
                logger.info(
                    "Lead save succeeded: backend=%s lead_id=%s thread_id=%s product=%s firstName=%s lastName=%s",
                    self._backend,
                    lead.get("lead_id", ""),
                    lead.get("thread_id", ""),
                    lead.get("product", ""),
                    lead.get("firstName", ""),
                    lead.get("lastName", ""),
                )
                self._forward_lead(lead)
                return lead

            with open(self._leads_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(lead, ensure_ascii=False) + "\n")
            logger.info(
                "Lead save succeeded: backend=%s lead_id=%s thread_id=%s product=%s firstName=%s lastName=%s",
                self._backend,
                lead.get("lead_id", ""),
                lead.get("thread_id", ""),
                lead.get("product", ""),
                lead.get("firstName", ""),
                lead.get("lastName", ""),
            )
            self._forward_lead(lead)
            return lead
        except Exception as exc:
            logger.error(
                "Lead save failed: backend=%s lead_id=%s thread_id=%s product=%s firstName=%s lastName=%s error=%s",
                self._backend,
                lead.get("lead_id", ""),
                lead.get("thread_id", ""),
                lead.get("product", ""),
                lead.get("firstName", ""),
                lead.get("lastName", ""),
                exc,
            )
            raise

    def list_leads(self) -> list[dict]:
        if self._backend == "dynamodb":
            assert self._dynamodb_table is not None
            rows: list[dict] = []
            query_kwargs = {
                "KeyConditionExpression": Key("pk").eq(self._DDB_PARTITION_KEY),
                "ScanIndexForward": False,
            }
            while True:
                response = self._dynamodb_table.query(**query_kwargs)
                for item in response.get("Items", []):
                    row = dict(item)
                    row.pop("pk", None)
                    row.pop("sk", None)
                    rows.append(self._normalize_legacy_lead(row))
                last_key = response.get("LastEvaluatedKey")
                if not last_key:
                    return rows
                query_kwargs["ExclusiveStartKey"] = last_key

        if not self._leads_file.exists():
            return []

        rows: list[dict] = []
        with open(self._leads_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(self._normalize_legacy_lead(json.loads(line)))
                except json.JSONDecodeError:
                    logger.warning("Skip invalid lead jsonl line: %r", line[:120])

        rows.reverse()
        return rows
