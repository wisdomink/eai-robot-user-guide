from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


_DEFAULT_PROMPTS = [
    {
        "id": "如何购买_ff_机器人",
        "enabled": True,
        "label": "如何购买 FF 机器人？",
        "prompt": "如何购买 FF 机器人？",
        "sort_order": 0,
    },
    {
        "id": "ff_机器人什么时候交付",
        "enabled": True,
        "label": "FF 机器人什么时候交付？",
        "prompt": "FF 机器人什么时候交付？",
        "sort_order": 1,
    },
    {
        "id": "ff_目前有哪些产品线",
        "enabled": True,
        "label": "FF 目前有哪些产品线？",
        "prompt": "FF 目前有哪些产品线？",
        "sort_order": 2,
    },
]

_DEFAULT_GREETING = "Do you want to know about FF's products?"
_DEFAULT_PLACEHOLDER = "Ask anything about FF..."
_DEFAULT_INFO_TEXT = ""
_DEFAULT_PAGE_ID = "fallback"
_DEFAULT_PAGE_LABEL = "默认"
_DEFAULT_PAGE_PATTERN = "*"
_DEFAULT_HOST = "www.ff.com"


class HomepagePromptsStorage:
    """Persist homepage prompt configuration in a local JSON file or DynamoDB."""

    _PAGE_PARTITION_KEY = "HOMEPAGE_PAGE"
    _LEGACY_PARTITION_KEY = "HOMEPAGE_PROMPT"

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
            import boto3  # Lazy import: keeps boto3 optional for file-backend callers (e.g. sync_homepage_prompts.py).

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

    @staticmethod
    def _to_slug(text: str) -> str:
        s = text.strip().lower()
        s = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "_", s)
        return s.strip("_") or "item"

    @classmethod
    def _normalize_url_value(cls, value: str | None) -> str:
        raw = (value or "").strip()
        if not raw:
            return ""
        if raw == "*":
            return raw

        if raw.startswith("/"):
            raw = f"https://{_DEFAULT_HOST}{raw}"
        elif "://" not in raw and not raw.startswith("//"):
            raw = f"https://{raw}"

        try:
            parsed = urlsplit(raw)
        except ValueError:
            return raw.rstrip("/")

        if not parsed.scheme or not parsed.netloc:
            return raw.rstrip("/")

        path = parsed.path or "/"
        if path != "/":
            path = path.rstrip("/") or "/"

        normalized = urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, "", ""))
        return normalized

    @classmethod
    def _normalize_pattern(cls, pattern: str | None) -> str:
        raw = (pattern or "").strip()
        if not raw:
            return _DEFAULT_PAGE_PATTERN
        if raw == "*":
            return raw
        if raw.endswith("/*"):
            prefix = cls._normalize_url_value(raw[:-2])
            if not prefix:
                return _DEFAULT_PAGE_PATTERN
            # _normalize_url_value may end with "/" for origin-only URLs; avoid "//*" in the result.
            return f"{prefix.rstrip('/')}/*"
        normalized = cls._normalize_url_value(raw)
        return normalized or _DEFAULT_PAGE_PATTERN

    def _normalize_prompt_item(self, payload: dict, existing_ids: set[str] | None = None) -> dict:
        item: dict = {
            "enabled": bool(payload.get("enabled", True)),
            "label": str(payload.get("label", "")).strip(),
            "prompt": str(payload.get("prompt", "")).strip(),
            "sort_order": int(payload.get("sort_order", 0)),
        }

        explicit_id = str(payload.get("id", "")).strip()
        if explicit_id:
            item["id"] = explicit_id
            return item

        base = self._to_slug(item["label"]) if item["label"] else "prompt"
        candidate = base
        ids = existing_ids or set()
        counter = 1
        while candidate in ids:
            counter += 1
            candidate = f"{base}_{counter}"
        item["id"] = candidate
        return item

    @staticmethod
    def _default_page() -> dict:
        return {
            "id": _DEFAULT_PAGE_ID,
            "pattern": _DEFAULT_PAGE_PATTERN,
            "label": _DEFAULT_PAGE_LABEL,
            "greeting": _DEFAULT_GREETING,
            "placeholder": _DEFAULT_PLACEHOLDER,
            "info_text": _DEFAULT_INFO_TEXT,
            "prompts": deepcopy(_DEFAULT_PROMPTS),
        }

    @classmethod
    def _default_data(cls) -> dict:
        return {"pages": [cls._default_page()]}

    def _normalize_page(self, payload: dict, existing_ids: set[str] | None = None) -> dict:
        if not isinstance(payload, dict):
            raise ValueError("Homepage page payload must be an object")

        pattern = self._normalize_pattern(str(payload.get("pattern", "")).strip())
        label = str(payload.get("label", "")).strip() or pattern

        explicit_id = str(payload.get("id", "")).strip()
        if explicit_id:
            page_id = explicit_id
        else:
            base = self._to_slug(pattern if pattern != "*" else "fallback")
            page_id = base or "page"
            ids = existing_ids or set()
            counter = 1
            while page_id in ids:
                counter += 1
                page_id = f"{base}_{counter}"

        prompts_payload = payload.get("prompts", [])
        prompts_payload = prompts_payload if isinstance(prompts_payload, list) else []

        prompt_ids: set[str] = set()
        normalized_prompts = []
        for index, prompt_payload in enumerate(prompts_payload):
            if not isinstance(prompt_payload, dict):
                continue
            normalized_prompt = self._normalize_prompt_item(prompt_payload, prompt_ids)
            prompt_ids.add(normalized_prompt["id"])
            if "sort_order" not in prompt_payload:
                normalized_prompt["sort_order"] = index
            normalized_prompts.append(normalized_prompt)

        return {
            "id": page_id,
            "pattern": pattern,
            "label": label,
            "greeting": str(payload.get("greeting", _DEFAULT_GREETING)).strip() or _DEFAULT_GREETING,
            "placeholder": str(payload.get("placeholder", _DEFAULT_PLACEHOLDER)).strip() or _DEFAULT_PLACEHOLDER,
            "info_text": str(payload.get("info_text", _DEFAULT_INFO_TEXT)).strip(),
            "prompts": normalized_prompts,
        }

    def _normalize_pages_payload(self, pages_payload: list[dict]) -> list[dict]:
        page_ids: set[str] = set()
        normalized_pages = []
        for payload in pages_payload:
            if not isinstance(payload, dict):
                continue
            normalized = self._normalize_page(payload, page_ids)
            page_ids.add(normalized["id"])
            normalized_pages.append(normalized)
        return normalized_pages or [self._default_page()]

    def _migrate_legacy_data(self, data: dict) -> dict:
        legacy_page = self._normalize_page(
            {
                "id": _DEFAULT_PAGE_ID,
                "pattern": _DEFAULT_PAGE_PATTERN,
                "label": _DEFAULT_PAGE_LABEL,
                "greeting": data.get("greeting", _DEFAULT_GREETING),
                "placeholder": data.get("placeholder", _DEFAULT_PLACEHOLDER),
                "info_text": data.get("info_text", _DEFAULT_INFO_TEXT),
                "prompts": data.get("prompts", []),
            }
        )
        return {"pages": [legacy_page]}

    def _normalize_data_container(self, data: dict) -> tuple[dict, bool]:
        if not isinstance(data, dict):
            raise ValueError("Homepage prompts config must be a JSON object")

        pages = data.get("pages")
        if isinstance(pages, list):
            normalized_pages = self._normalize_pages_payload(pages)
            normalized_data = {"pages": normalized_pages}
            return normalized_data, normalized_data != data

        if any(key in data for key in ("greeting", "placeholder", "info_text", "prompts")):
            return self._migrate_legacy_data(data), True

        return self._default_data(), True

    def _load_data(self) -> dict:
        if self._backend == "dynamodb":
            return self._load_data_from_dynamodb()

        if not self._data_path.exists():
            return self._default_data()

        with open(self._data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        normalized_data, changed = self._normalize_data_container(data)
        if changed:
            self._write_data(normalized_data)
        return normalized_data

    def _write_data(self, data: dict) -> None:
        if self._backend == "dynamodb":
            raise RuntimeError("_write_data is not used for DynamoDB backend")
        with open(self._data_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")

    def _query_partition(self, partition_key: str) -> list[dict]:
        assert self._dynamodb_table is not None
        from boto3.dynamodb.conditions import Key  # Lazy import, paired with lazy boto3 import above.

        rows: list[dict] = []
        query_kwargs = {"KeyConditionExpression": Key("pk").eq(partition_key)}
        while True:
            response = self._dynamodb_table.query(**query_kwargs)
            rows.extend(response.get("Items", []))
            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                return rows
            query_kwargs["ExclusiveStartKey"] = last_key

    def _load_data_from_dynamodb(self) -> dict:
        self._ensure_dynamodb_seeded()
        assert self._dynamodb_table is not None

        pages = []
        for item in self._query_partition(self._PAGE_PARTITION_KEY):
            row = {k: v for k, v in item.items() if k not in {"pk", "sk"}}
            if not isinstance(row, dict):
                continue
            pages.append(row)

        normalized_pages = self._normalize_pages_payload(pages)
        return {"pages": normalized_pages}

    def _ensure_dynamodb_seeded(self) -> None:
        assert self._dynamodb_table is not None
        page_items = self._query_partition(self._PAGE_PARTITION_KEY)
        if page_items:
            return

        legacy_items = self._query_partition(self._LEGACY_PARTITION_KEY)
        if legacy_items:
            migrated_pages = self._migrate_legacy_dynamodb_items(legacy_items)
            with self._dynamodb_table.batch_writer() as batch:
                for page in migrated_pages:
                    batch.put_item(Item={"pk": self._PAGE_PARTITION_KEY, "sk": page["id"], **page})
            return

        with self._dynamodb_table.batch_writer() as batch:
            for page in self._default_data()["pages"]:
                batch.put_item(Item={"pk": self._PAGE_PARTITION_KEY, "sk": page["id"], **page})

    def _migrate_legacy_dynamodb_items(self, items: list[dict]) -> list[dict]:
        prompts = []
        greeting = _DEFAULT_GREETING
        placeholder = _DEFAULT_PLACEHOLDER
        info_text = _DEFAULT_INFO_TEXT

        for item in items:
            sk = item.get("sk", "")
            row = {k: v for k, v in item.items() if k not in {"pk", "sk"}}
            if sk == "_SETTINGS":
                greeting = str(row.get("greeting", _DEFAULT_GREETING)).strip() or _DEFAULT_GREETING
                placeholder = str(row.get("placeholder", _DEFAULT_PLACEHOLDER)).strip() or _DEFAULT_PLACEHOLDER
                info_text = str(row.get("info_text", _DEFAULT_INFO_TEXT)).strip()
            elif sk == "_GREETING":
                if greeting == _DEFAULT_GREETING:
                    greeting = str(row.get("greeting", _DEFAULT_GREETING)).strip() or _DEFAULT_GREETING
            else:
                prompts.append(row)

        return [
            self._normalize_page(
                {
                    "id": _DEFAULT_PAGE_ID,
                    "pattern": _DEFAULT_PAGE_PATTERN,
                    "label": _DEFAULT_PAGE_LABEL,
                    "greeting": greeting,
                    "placeholder": placeholder,
                    "info_text": info_text,
                    "prompts": prompts,
                }
            )
        ]

    @staticmethod
    def _sort_prompts(prompts: list[dict]) -> list[dict]:
        return sorted(prompts, key=lambda item: (item.get("sort_order", 0), item.get("id", "")))

    def _format_page_for_response(self, page: dict, *, include_disabled: bool = False) -> dict:
        prompts = page.get("prompts", [])
        if not isinstance(prompts, list):
            prompts = []
        filtered_prompts = [
            prompt
            for prompt in prompts
            if isinstance(prompt, dict) and (include_disabled or prompt.get("enabled", True))
        ]
        return {
            "id": page.get("id", _DEFAULT_PAGE_ID),
            "pattern": page.get("pattern", _DEFAULT_PAGE_PATTERN),
            "label": page.get("label", _DEFAULT_PAGE_LABEL),
            "greeting": page.get("greeting", _DEFAULT_GREETING),
            "placeholder": page.get("placeholder", _DEFAULT_PLACEHOLDER),
            "info_text": page.get("info_text", _DEFAULT_INFO_TEXT),
            "prompts": self._sort_prompts(filtered_prompts),
        }

    def list_pages(self, *, include_disabled: bool = True) -> list[dict]:
        data = self._load_data()
        pages = data.get("pages", [])
        if not isinstance(pages, list):
            pages = []
        return [self._format_page_for_response(page, include_disabled=include_disabled) for page in pages if isinstance(page, dict)]

    def _match_rank(self, pattern: str, normalized_url: str) -> tuple[int, int] | None:
        if pattern == "*":
            return (0, 0)
        if pattern.endswith("/*"):
            prefix = pattern[:-2]
            if normalized_url == prefix or normalized_url.startswith(f"{prefix}/"):
                return (1, len(prefix))
            return None
        if pattern == normalized_url:
            return (2, len(pattern))
        return None

    def resolve_page(self, url: str | None) -> dict:
        normalized_url = self._normalize_url_value(url)
        pages = self.list_pages(include_disabled=True)
        if not pages:
            return self._default_page()

        best_page = None
        best_rank = None
        fallback_page = None
        for page in pages:
            pattern = str(page.get("pattern", _DEFAULT_PAGE_PATTERN))
            if pattern == "*":
                fallback_page = page
            rank = self._match_rank(pattern, normalized_url)
            if rank is None:
                continue
            if best_rank is None or rank > best_rank:
                best_rank = rank
                best_page = page

        return deepcopy(best_page or fallback_page or pages[0] or self._default_page())

    def get_homepage_config(self, *, url: str | None = None, include_disabled: bool = False) -> dict:
        page = self.resolve_page(url)
        return self._format_page_for_response(page, include_disabled=include_disabled)

    def upsert_page(self, payload: dict) -> tuple[dict, bool]:
        if self._backend == "dynamodb":
            return self._upsert_page_dynamodb(payload)

        data = self._load_data()
        pages = data.get("pages", [])
        pages = pages if isinstance(pages, list) else []

        existing_ids = {page.get("id") for page in pages if isinstance(page, dict) and page.get("id")}
        explicit_id = str(payload.get("id", "")).strip()
        if explicit_id:
            existing_ids.discard(explicit_id)
        normalized = self._normalize_page(payload, existing_ids)

        created = True
        for index, page in enumerate(pages):
            if isinstance(page, dict) and page.get("id") == normalized["id"]:
                pages[index] = normalized
                created = False
                break
        else:
            pages.append(normalized)

        data["pages"] = self._normalize_pages_payload(pages)
        self._write_data(data)
        return self._format_page_for_response(normalized, include_disabled=True), created

    def _upsert_page_dynamodb(self, payload: dict) -> tuple[dict, bool]:
        self._ensure_dynamodb_seeded()
        assert self._dynamodb_table is not None

        current_pages = self.list_pages(include_disabled=True)
        existing_ids = {page.get("id") for page in current_pages if page.get("id")}
        explicit_id = str(payload.get("id", "")).strip()
        if explicit_id:
            existing_ids.discard(explicit_id)
        normalized = self._normalize_page(payload, existing_ids)
        existing = self._dynamodb_table.get_item(
            Key={"pk": self._PAGE_PARTITION_KEY, "sk": normalized["id"]}
        ).get("Item")
        self._dynamodb_table.put_item(
            Item={"pk": self._PAGE_PARTITION_KEY, "sk": normalized["id"], **normalized}
        )
        return self._format_page_for_response(normalized, include_disabled=True), existing is None

    def delete_page(self, page_id: str) -> dict | None:
        target_id = page_id.strip()
        if not target_id:
            raise ValueError("Page id is required")

        if self._backend == "dynamodb":
            return self._delete_page_dynamodb(target_id)

        data = self._load_data()
        pages = data.get("pages", [])
        if not isinstance(pages, list):
            return None

        deleted_item = None
        remaining_pages = []
        for page in pages:
            if not isinstance(page, dict):
                continue
            if page.get("id") == target_id and deleted_item is None:
                deleted_item = page
                continue
            remaining_pages.append(page)

        if deleted_item is None:
            return None

        data["pages"] = self._normalize_pages_payload(remaining_pages)
        self._write_data(data)
        return self._format_page_for_response(deleted_item, include_disabled=True)

    def _delete_page_dynamodb(self, target_id: str) -> dict | None:
        self._ensure_dynamodb_seeded()
        assert self._dynamodb_table is not None

        existing = self._dynamodb_table.get_item(
            Key={"pk": self._PAGE_PARTITION_KEY, "sk": target_id}
        ).get("Item")
        if not existing:
            return None

        self._dynamodb_table.delete_item(Key={"pk": self._PAGE_PARTITION_KEY, "sk": target_id})
        row = {k: v for k, v in existing.items() if k not in {"pk", "sk"}}
        return self._format_page_for_response(row, include_disabled=True)
