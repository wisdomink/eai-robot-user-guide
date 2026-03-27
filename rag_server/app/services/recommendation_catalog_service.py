from __future__ import annotations

import json
import re
from pathlib import Path


class RecommendationCatalogStorage:
    """Persist recommendation catalog items in recommendations.json."""

    def __init__(self, config_path: Path) -> None:
        self._config_path = config_path
        self._config_path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _to_slug(name: str) -> str:
        s = name.strip().lower()
        s = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "_", s)
        return s.strip("_") or "item"

    def _normalize_item(self, payload: dict, existing_ids: set[str] | None = None) -> dict:
        item: dict[str, str | bool] = {}

        item["enabled"] = bool(payload.get("enabled", True))

        for key in (
            "product_name",
            "trigger_scene",
            "recommendation_content_cn",
            "recommendation_content_en",
        ):
            value = payload.get(key, "")
            item[key] = value.strip() if isinstance(value, str) else str(value)

        explicit_id = str(payload.get("id", "")).strip()
        if explicit_id:
            item["id"] = explicit_id
        else:
            base = self._to_slug(item["product_name"]) if item["product_name"] else "item"
            candidate = base
            counter = 1
            ids = existing_ids or set()
            while candidate in ids:
                counter += 1
                candidate = f"{base}_{counter}"
            item["id"] = candidate

        return item

    def _load_config(self) -> dict:
        if not self._config_path.exists():
            return {"catalog_items": []}

        with open(self._config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError("Recommendation config must be a JSON object")
        return data

    def _write_config(self, config: dict) -> None:
        with open(self._config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
            f.write("\n")

    def list_recommendations(self) -> list[dict]:
        config = self._load_config()
        items = config.get("catalog_items", [])
        if not isinstance(items, list):
            raise ValueError("catalog_items must be a JSON array")
        return [item for item in items if isinstance(item, dict)]

    def save_or_update_recommendation(self, payload: dict) -> tuple[dict, bool]:
        config = self._load_config()
        items = config.get("catalog_items", [])
        if not isinstance(items, list):
            raise ValueError("catalog_items must be a JSON array")

        existing_ids = {
            item.get("id") for item in items if isinstance(item, dict) and item.get("id")
        }
        normalized = self._normalize_item(payload, existing_ids)

        created = True
        for index, item in enumerate(items):
            if isinstance(item, dict) and item.get("id") == normalized["id"]:
                items[index] = normalized
                created = False
                break
        else:
            items.append(normalized)

        config["catalog_items"] = items
        self._write_config(config)
        return normalized, created

    def get_lead_capture_triage_config(self) -> dict:
        """Return lead_capture + purchase_intent_keywords for triage / admin UI."""
        config = self._load_config()
        lead = config.get("lead_capture")
        if not isinstance(lead, dict):
            lead = {}
        keywords = config.get("purchase_intent_keywords")
        if not isinstance(keywords, dict):
            keywords = {"cn": [], "en": []}
        return {"lead_capture": lead, "purchase_intent_keywords": keywords}

    @staticmethod
    def _normalize_keyword_list(raw: object) -> list[str]:
        if raw is None:
            return []
        if isinstance(raw, list):
            return [str(x).strip() for x in raw if str(x).strip()]
        if isinstance(raw, str):
            return [line.strip() for line in raw.splitlines() if line.strip()]
        return []

    def save_lead_capture_triage_config(
        self,
        lead_capture_updates: dict,
        purchase_intent_keywords: dict | None = None,
    ) -> dict:
        """Merge lead_capture fields and replace purchase_intent_keywords. Preserves other top-level keys."""
        config = self._load_config()
        existing = config.get("lead_capture")
        if not isinstance(existing, dict):
            existing = {}
        merged = {**existing}
        for key, value in (lead_capture_updates or {}).items():
            if value is None:
                continue
            if key in ("trigger_conditions_cn", "trigger_conditions_en", "title_cn", "title_en",
                       "description_cn", "description_en", "success_title_cn", "success_title_en",
                       "success_text_cn", "success_text_en"):
                merged[key] = value.strip() if isinstance(value, str) else str(value)
            else:
                merged[key] = value
        config["lead_capture"] = merged

        if purchase_intent_keywords is not None:
            kw = purchase_intent_keywords if isinstance(purchase_intent_keywords, dict) else {}
            cn = self._normalize_keyword_list(kw.get("cn"))
            en = self._normalize_keyword_list(kw.get("en"))
            config["purchase_intent_keywords"] = {"cn": cn, "en": en}

        self._write_config(config)
        return self.get_lead_capture_triage_config()

    def delete_recommendation(self, recommendation_id: str) -> dict | None:
        config = self._load_config()
        items = config.get("catalog_items", [])
        if not isinstance(items, list):
            raise ValueError("catalog_items must be a JSON array")

        target_id = recommendation_id.strip()
        if not target_id:
            raise ValueError("Recommendation id is required")

        deleted_item: dict | None = None
        next_items: list[dict] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            if item.get("id") == target_id and deleted_item is None:
                deleted_item = item
                continue
            next_items.append(item)

        if deleted_item is None:
            return None

        config["catalog_items"] = next_items
        self._write_config(config)
        return deleted_item
