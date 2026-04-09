from __future__ import annotations

import json
import re
from pathlib import Path

import boto3
from boto3.dynamodb.conditions import Key


_DEFAULT_PROMPTS = [
    {
        "id": "ff_master",
        "enabled": True,
        "label": "FF Master",
        "prompt": "Tell me about FF Master. What are its key features, specs, and how do I get started?",
        "sort_order": 0,
    },
    {
        "id": "ff_futurist",
        "enabled": True,
        "label": "FF Futurist",
        "prompt": "Tell me about FF Futurist. What are its key features, specs, and how do I get started?",
        "sort_order": 1,
    },
    {
        "id": "ff_futurist_ultra",
        "enabled": True,
        "label": "FF Futurist Ultra",
        "prompt": "Tell me about FF Futurist Ultra. What are its key features, specs, and how do I get started?",
        "sort_order": 2,
    },
    {
        "id": "ff_aegis",
        "enabled": True,
        "label": "FF Aegis",
        "prompt": "Tell me about FF Aegis. What are its key features, specs, and how do I get started?",
        "sort_order": 3,
    },
    {
        "id": "ff_aegis_ultra",
        "enabled": True,
        "label": "FF Aegis Ultra",
        "prompt": "Tell me about FF Aegis Ultra. What are its key features, specs, and how do I get started?",
        "sort_order": 4,
    },
    {
        "id": "ff_91_2_0",
        "enabled": True,
        "label": "FF 91 2.0",
        "prompt": "Tell me about the FF 91 2.0. What are its key features, specs, and how do I get started?",
        "sort_order": 5,
    },
]

_DEFAULT_GREETING = "Hi! I can help you with any of our products. Pick one to get started."
_DEFAULT_PLACEHOLDER = "Ask a question…"
_DEFAULT_INFO_TEXT = ""


class HomepagePromptsStorage:
    """Persist homepage prompt configuration in a local JSON file or DynamoDB."""

    _PARTITION_KEY = "HOMEPAGE_PROMPT"

    def __init__(
        self,
        data_path: Path | None = None,
        *,
        backend: str = "file",
        dynamodb_table: str = "",
        aws_region: str = "",
    ) -> None:
        self._backend = backend.strip().lower() or "file"
        self._data_path = data_path
        self._dynamodb_table_name = dynamodb_table.strip()
        self._aws_region = aws_region.strip()
        self._dynamodb_table = None

        if self._backend == "dynamodb":
            if not self._dynamodb_table_name:
                raise ValueError(
                    "HOMEPAGE_PROMPTS_DDB_TABLE is required when HOMEPAGE_PROMPTS_BACKEND=dynamodb"
                )
            resource_kwargs = {}
            if self._aws_region:
                resource_kwargs["region_name"] = self._aws_region
            dynamodb = boto3.resource("dynamodb", **resource_kwargs)
            self._dynamodb_table = dynamodb.Table(self._dynamodb_table_name)
        else:
            if self._data_path is None:
                raise ValueError("data_path is required when HOMEPAGE_PROMPTS_BACKEND=file")
            self._data_path.parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_config(cls) -> HomepagePromptsStorage:
        from app.core.config import (
            AWS_REGION_NAME,
            HOMEPAGE_PROMPTS_BACKEND,
            HOMEPAGE_PROMPTS_DATA_PATH,
            HOMEPAGE_PROMPTS_DDB_TABLE,
        )

        return cls(
            HOMEPAGE_PROMPTS_DATA_PATH,
            backend=HOMEPAGE_PROMPTS_BACKEND,
            dynamodb_table=HOMEPAGE_PROMPTS_DDB_TABLE,
            aws_region=AWS_REGION_NAME,
        )

    # ── ID generation ─────────────────────────────────────────────────────

    @staticmethod
    def _to_slug(text: str) -> str:
        s = text.strip().lower()
        s = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "_", s)
        return s.strip("_") or "prompt"

    def _normalize_item(self, payload: dict, existing_ids: set[str] | None = None) -> dict:
        item: dict = {}
        item["enabled"] = bool(payload.get("enabled", True))
        item["label"] = str(payload.get("label", "")).strip()
        item["prompt"] = str(payload.get("prompt", "")).strip()
        item["sort_order"] = int(payload.get("sort_order", 0))

        explicit_id = str(payload.get("id", "")).strip()
        if explicit_id:
            item["id"] = explicit_id
        else:
            base = self._to_slug(item["label"]) if item["label"] else "prompt"
            candidate = base
            counter = 1
            ids = existing_ids or set()
            while candidate in ids:
                counter += 1
                candidate = f"{base}_{counter}"
            item["id"] = candidate

        return item

    # ── File backend helpers ──────────────────────────────────────────────

    def _load_data(self) -> dict:
        if self._backend == "dynamodb":
            return self._load_data_from_dynamodb()

        if not self._data_path.exists():
            return self._default_data()

        with open(self._data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("Homepage prompts config must be a JSON object")
        return data

    def _write_data(self, data: dict) -> None:
        if self._backend == "dynamodb":
            raise RuntimeError("_write_data is not used for DynamoDB backend")
        with open(self._data_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")

    @staticmethod
    def _default_data() -> dict:
        return {
            "greeting": _DEFAULT_GREETING,
            "placeholder": _DEFAULT_PLACEHOLDER,
            "info_text": _DEFAULT_INFO_TEXT,
            "prompts": list(_DEFAULT_PROMPTS),
        }

    # ── DynamoDB helpers ──────────────────────────────────────────────────

    def _load_data_from_dynamodb(self) -> dict:
        self._ensure_dynamodb_seeded()
        assert self._dynamodb_table is not None

        items = self._query_partition(self._PARTITION_KEY)
        prompts = []
        greeting = _DEFAULT_GREETING
        placeholder = _DEFAULT_PLACEHOLDER
        info_text = _DEFAULT_INFO_TEXT
        for item in items:
            sk = item.get("sk", "")
            row = {k: v for k, v in item.items() if k not in {"pk", "sk"}}
            if sk == "_SETTINGS":
                greeting = row.get("greeting", _DEFAULT_GREETING)
                placeholder = row.get("placeholder", _DEFAULT_PLACEHOLDER)
                info_text = row.get("info_text", _DEFAULT_INFO_TEXT)
            elif sk == "_GREETING":
                if greeting == _DEFAULT_GREETING:
                    greeting = row.get("greeting", _DEFAULT_GREETING)
            else:
                prompts.append(row)
        return {"greeting": greeting, "placeholder": placeholder, "info_text": info_text, "prompts": prompts}

    def _query_partition(self, partition_key: str) -> list[dict]:
        assert self._dynamodb_table is not None
        rows: list[dict] = []
        query_kwargs = {
            "KeyConditionExpression": Key("pk").eq(partition_key),
        }
        while True:
            response = self._dynamodb_table.query(**query_kwargs)
            rows.extend(response.get("Items", []))
            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                return rows
            query_kwargs["ExclusiveStartKey"] = last_key

    def _ensure_dynamodb_seeded(self) -> None:
        assert self._dynamodb_table is not None
        response = self._dynamodb_table.scan(
            FilterExpression=Key("pk").eq(self._PARTITION_KEY),
            Limit=1,
            Select="COUNT",
        )
        if response.get("Count", 0):
            return

        with self._dynamodb_table.batch_writer() as batch:
            batch.put_item(
                Item={
                    "pk": self._PARTITION_KEY,
                    "sk": "_SETTINGS",
                    "greeting": _DEFAULT_GREETING,
                    "placeholder": _DEFAULT_PLACEHOLDER,
                    "info_text": _DEFAULT_INFO_TEXT,
                }
            )
            for p in _DEFAULT_PROMPTS:
                batch.put_item(
                    Item={"pk": self._PARTITION_KEY, "sk": p["id"], **p}
                )

    # ── Public API ────────────────────────────────────────────────────────

    def list_prompts(self, *, include_disabled: bool = False) -> list[dict]:
        data = self._load_data()
        prompts = data.get("prompts", [])
        if not isinstance(prompts, list):
            return []
        if not include_disabled:
            prompts = [p for p in prompts if p.get("enabled", True)]
        return sorted(prompts, key=lambda p: (p.get("sort_order", 0), p.get("id", "")))

    def get_settings(self) -> dict:
        data = self._load_data()
        return {
            "greeting": data.get("greeting", _DEFAULT_GREETING),
            "placeholder": data.get("placeholder", _DEFAULT_PLACEHOLDER),
            "info_text": data.get("info_text", _DEFAULT_INFO_TEXT),
        }

    def get_homepage_config(self, *, include_disabled: bool = False) -> dict:
        """Return greeting + placeholder + sorted prompts for the frontend."""
        settings = self.get_settings()
        return {
            **settings,
            "prompts": self.list_prompts(include_disabled=include_disabled),
        }

    def save_settings(
        self,
        greeting: str | None = None,
        placeholder: str | None = None,
        info_text: str | None = None,
    ) -> dict:
        """Update page-level settings (greeting, placeholder, and/or info_text)."""
        if self._backend == "dynamodb":
            return self._save_settings_dynamodb(greeting, placeholder, info_text)

        data = self._load_data()
        if greeting is not None:
            data["greeting"] = greeting.strip()
        if placeholder is not None:
            data["placeholder"] = placeholder.strip()
        if info_text is not None:
            data["info_text"] = info_text.strip()
        self._write_data(data)
        return {
            "greeting": data.get("greeting", _DEFAULT_GREETING),
            "placeholder": data.get("placeholder", _DEFAULT_PLACEHOLDER),
            "info_text": data.get("info_text", _DEFAULT_INFO_TEXT),
        }

    def _save_settings_dynamodb(
        self,
        greeting: str | None,
        placeholder: str | None,
        info_text: str | None,
    ) -> dict:
        self._ensure_dynamodb_seeded()
        assert self._dynamodb_table is not None

        current = self.get_settings()
        if greeting is not None:
            current["greeting"] = greeting.strip()
        if placeholder is not None:
            current["placeholder"] = placeholder.strip()
        if info_text is not None:
            current["info_text"] = info_text.strip()

        self._dynamodb_table.put_item(
            Item={"pk": self._PARTITION_KEY, "sk": "_SETTINGS", **current}
        )
        return current

    def save_or_update_prompt(self, payload: dict) -> tuple[dict, bool]:
        if self._backend == "dynamodb":
            return self._save_or_update_dynamodb(payload)

        data = self._load_data()
        prompts = data.get("prompts", [])
        if not isinstance(prompts, list):
            prompts = []

        existing_ids = {
            p.get("id") for p in prompts if isinstance(p, dict) and p.get("id")
        }
        normalized = self._normalize_item(payload, existing_ids)

        created = True
        for idx, p in enumerate(prompts):
            if isinstance(p, dict) and p.get("id") == normalized["id"]:
                prompts[idx] = normalized
                created = False
                break
        else:
            prompts.append(normalized)

        data["prompts"] = prompts
        self._write_data(data)
        return normalized, created

    def _save_or_update_dynamodb(self, payload: dict) -> tuple[dict, bool]:
        self._ensure_dynamodb_seeded()
        assert self._dynamodb_table is not None

        existing_ids = {
            p.get("id") for p in self.list_prompts(include_disabled=True) if p.get("id")
        }
        normalized = self._normalize_item(payload, existing_ids)
        existing = self._dynamodb_table.get_item(
            Key={"pk": self._PARTITION_KEY, "sk": normalized["id"]}
        ).get("Item")
        self._dynamodb_table.put_item(
            Item={"pk": self._PARTITION_KEY, "sk": normalized["id"], **normalized}
        )
        return normalized, existing is None

    def delete_prompt(self, prompt_id: str) -> dict | None:
        target_id = prompt_id.strip()
        if not target_id:
            raise ValueError("Prompt id is required")

        if self._backend == "dynamodb":
            return self._delete_prompt_dynamodb(target_id)

        data = self._load_data()
        prompts = data.get("prompts", [])
        if not isinstance(prompts, list):
            return None

        deleted_item: dict | None = None
        next_prompts: list[dict] = []
        for p in prompts:
            if not isinstance(p, dict):
                continue
            if p.get("id") == target_id and deleted_item is None:
                deleted_item = p
                continue
            next_prompts.append(p)

        if deleted_item is None:
            return None

        data["prompts"] = next_prompts
        self._write_data(data)
        return deleted_item

    def _delete_prompt_dynamodb(self, target_id: str) -> dict | None:
        self._ensure_dynamodb_seeded()
        assert self._dynamodb_table is not None

        existing = self._dynamodb_table.get_item(
            Key={"pk": self._PARTITION_KEY, "sk": target_id}
        ).get("Item")
        if not existing:
            return None
        self._dynamodb_table.delete_item(
            Key={"pk": self._PARTITION_KEY, "sk": target_id}
        )
        return {k: v for k, v in existing.items() if k not in {"pk", "sk"}}
