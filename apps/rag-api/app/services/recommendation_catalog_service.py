from __future__ import annotations

import json
import re
from pathlib import Path

import boto3
from boto3.dynamodb.conditions import Key


class RecommendationCatalogStorage:
    """Persist recommendation config in a local JSON file or DynamoDB."""

    _CONFIG_PK = "CONFIG"
    _CATALOG_PK = "CATALOG_ITEM"
    _MANUAL_DOWNLOAD_PRODUCTS = [
        (
            "futurist",
            "FF Futurist",
            "https://ff-genesis-cdn-dev.s3.us-west-2.amazonaws.com/evan-test/download/FF+Futurist.pdf",
        ),
        (
            "futurist-ultra",
            "FF Futurist Ultra",
            "https://ff-genesis-cdn-dev.s3.us-west-2.amazonaws.com/evan-test/download/FF+Futurist+Ultra.pdf",
        ),
        (
            "master",
            "FF Master",
            "https://ff-genesis-cdn-dev.s3.us-west-2.amazonaws.com/evan-test/download/FF+Master.pdf",
        ),
        (
            "aegis",
            "FF Aegis",
            "https://ff-genesis-cdn-dev.s3.us-west-2.amazonaws.com/evan-test/download/FX+Aegis.pdf",
        ),
        (
            "aegis-ultra",
            "FF Aegis Ultra",
            "https://ff-genesis-cdn-dev.s3.us-west-2.amazonaws.com/evan-test/download/FF+Aegis+Ultra.pdf",
        ),
        (
            "navi",
            "FF NAVI",
            "https://ff-genesis-cdn-dev.s3.us-west-2.amazonaws.com/evan-test/download/FF+NAVI.pdf",
        ),
    ]

    def __init__(
        self,
        config_path: Path | None = None,
        *,
        backend: str = "file",
        dynamodb_table: str = "",
        aws_region: str = "",
    ) -> None:
        self._backend = backend.strip().lower() or "file"
        self._config_path = config_path
        self._seed_cache: dict | None = None
        self._dynamodb_table_name = dynamodb_table.strip()
        self._aws_region = aws_region.strip()
        self._dynamodb_table = None

        if self._backend == "dynamodb":
            if not self._dynamodb_table_name:
                raise ValueError("RECOMMENDATIONS_DDB_TABLE is required when RECOMMENDATIONS_BACKEND=dynamodb")
            resource_kwargs = {}
            if self._aws_region:
                resource_kwargs["region_name"] = self._aws_region
            dynamodb = boto3.resource("dynamodb", **resource_kwargs)
            self._dynamodb_table = dynamodb.Table(self._dynamodb_table_name)
        else:
            if self._config_path is None:
                raise ValueError("config_path is required when RECOMMENDATIONS_BACKEND=file")
            self._config_path.parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_config(cls) -> RecommendationCatalogStorage:
        from app.core.config import AWS_REGION_NAME, RECOMMENDATIONS_BACKEND, RECOMMENDATIONS_DDB_TABLE
        from app.services.recommendation_engine import RECOMMENDATIONS_PATH

        return cls(
            RECOMMENDATIONS_PATH,
            backend=RECOMMENDATIONS_BACKEND,
            dynamodb_table=RECOMMENDATIONS_DDB_TABLE,
            aws_region=AWS_REGION_NAME,
        )

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

    @staticmethod
    def _base_config() -> dict:
        return {
            "default_product": {},
            "lead_capture": {},
            "products": [],
            "purchase_intent_keywords": {"cn": [], "en": []},
            "manual_downloads": RecommendationCatalogStorage._default_manual_downloads(),
            "catalog_items": [],
        }

    @classmethod
    def _default_manual_downloads(cls) -> list[dict[str, str]]:
        return [
            {
                "product_id": product_id,
                "label": label,
                "download_url": download_url,
            }
            for product_id, label, download_url in cls._MANUAL_DOWNLOAD_PRODUCTS
        ]

    @classmethod
    def _normalize_manual_downloads(cls, raw: object) -> list[dict[str, str]]:
        rows = raw if isinstance(raw, list) else []
        by_id: dict[str, dict] = {}
        for item in rows:
            if not isinstance(item, dict):
                continue
            product_id = str(item.get("product_id", "")).strip()
            if not product_id:
                continue
            by_id[product_id] = item

        normalized: list[dict[str, str]] = []
        for product_id, label, default_download_url in cls._MANUAL_DOWNLOAD_PRODUCTS:
            item = by_id.get(product_id, {})
            download_url = str(item.get("download_url", "")).strip() or default_download_url
            normalized.append(
                {
                    "product_id": product_id,
                    "label": label,
                    "download_url": download_url,
                }
            )
        return normalized

    def _load_seed_config(self) -> dict:
        if self._seed_cache is not None:
            return json.loads(json.dumps(self._seed_cache))

        if self._config_path and self._config_path.exists():
            with open(self._config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                self._seed_cache = data
                return json.loads(json.dumps(data))

        self._seed_cache = self._base_config()
        return json.loads(json.dumps(self._seed_cache))

    def _load_config(self) -> dict:
        if self._backend == "dynamodb":
            return self._load_config_from_dynamodb()

        if not self._config_path.exists():
            return self._base_config()

        with open(self._config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError("Recommendation config must be a JSON object")
        return data

    def _write_config(self, config: dict) -> None:
        if self._backend == "dynamodb":
            raise RuntimeError("_write_config is not used for DynamoDB backend")
        with open(self._config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
            f.write("\n")

    def _load_config_from_dynamodb(self) -> dict:
        self._ensure_dynamodb_seeded()
        assert self._dynamodb_table is not None

        seed = self._load_seed_config()
        config = self._base_config()
        config["default_product"] = dict(seed.get("default_product") or {})
        config["lead_capture"] = dict(seed.get("lead_capture") or {})
        config["products"] = list(seed.get("products") or [])
        config["purchase_intent_keywords"] = dict(seed.get("purchase_intent_keywords") or {"cn": [], "en": []})
        config["manual_downloads"] = self._normalize_manual_downloads(seed.get("manual_downloads"))

        for item in self._query_partition(self._CONFIG_PK):
            sk = item.get("sk")
            row = {k: v for k, v in item.items() if k not in {"pk", "sk"}}
            if sk == "DEFAULT_PRODUCT":
                config["default_product"] = row
            elif sk == "LEAD_CAPTURE":
                config["lead_capture"] = row
            elif sk == "PRODUCTS":
                config["products"] = row.get("items", [])
            elif sk == "PURCHASE_INTENT_KEYWORDS":
                config["purchase_intent_keywords"] = {
                    "cn": list(row.get("cn", []) or []),
                    "en": list(row.get("en", []) or []),
                }
            elif sk == "MANUAL_DOWNLOADS":
                config["manual_downloads"] = self._normalize_manual_downloads(row.get("items"))

        catalog_items = [
            {k: v for k, v in item.items() if k not in {"pk", "sk"}}
            for item in self._query_partition(self._CATALOG_PK)
            if isinstance(item, dict)
        ]
        config["catalog_items"] = catalog_items if catalog_items else list(seed.get("catalog_items") or [])
        return config

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
        response = self._dynamodb_table.scan(Limit=1, Select="COUNT")
        if response.get("Count", 0):
            return

        seed = self._load_seed_config()
        with self._dynamodb_table.batch_writer() as batch:
            default_product = seed.get("default_product")
            if isinstance(default_product, dict) and default_product:
                batch.put_item(Item={"pk": self._CONFIG_PK, "sk": "DEFAULT_PRODUCT", **default_product})

            lead_capture = seed.get("lead_capture")
            if isinstance(lead_capture, dict) and lead_capture:
                batch.put_item(Item={"pk": self._CONFIG_PK, "sk": "LEAD_CAPTURE", **lead_capture})

            products = seed.get("products")
            if isinstance(products, list) and products:
                batch.put_item(Item={"pk": self._CONFIG_PK, "sk": "PRODUCTS", "items": products})

            keywords = seed.get("purchase_intent_keywords")
            if isinstance(keywords, dict):
                batch.put_item(
                    Item={
                        "pk": self._CONFIG_PK,
                        "sk": "PURCHASE_INTENT_KEYWORDS",
                        "cn": self._normalize_keyword_list(keywords.get("cn")),
                        "en": self._normalize_keyword_list(keywords.get("en")),
                    }
                )

            manual_downloads = seed.get("manual_downloads")
            if isinstance(manual_downloads, list):
                batch.put_item(
                    Item={
                        "pk": self._CONFIG_PK,
                        "sk": "MANUAL_DOWNLOADS",
                        "items": self._normalize_manual_downloads(manual_downloads),
                    }
                )

            catalog_items = seed.get("catalog_items")
            if isinstance(catalog_items, list):
                for item in catalog_items:
                    if not isinstance(item, dict):
                        continue
                    normalized = self._normalize_item(item)
                    batch.put_item(Item={"pk": self._CATALOG_PK, "sk": normalized["id"], **normalized})

    def get_full_config(self) -> dict:
        return self._load_config()

    def list_recommendations(self) -> list[dict]:
        config = self._load_config()
        items = config.get("catalog_items", [])
        if not isinstance(items, list):
            raise ValueError("catalog_items must be a JSON array")
        return [item for item in items if isinstance(item, dict)]

    def save_or_update_recommendation(self, payload: dict) -> tuple[dict, bool]:
        if self._backend == "dynamodb":
            self._ensure_dynamodb_seeded()
            assert self._dynamodb_table is not None
            existing_ids = {
                item.get("id")
                for item in self.list_recommendations()
                if isinstance(item, dict) and item.get("id")
            }
            normalized = self._normalize_item(payload, existing_ids)
            existing = self._dynamodb_table.get_item(
                Key={"pk": self._CATALOG_PK, "sk": normalized["id"]}
            ).get("Item")
            self._dynamodb_table.put_item(
                Item={"pk": self._CATALOG_PK, "sk": normalized["id"], **normalized}
            )
            return normalized, existing is None

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

    def get_manual_download_config(self) -> dict:
        config = self._load_config()
        return {
            "manual_downloads": self._normalize_manual_downloads(config.get("manual_downloads"))
        }

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
        if self._backend == "dynamodb":
            self._ensure_dynamodb_seeded()
            assert self._dynamodb_table is not None

            current = self.get_lead_capture_triage_config()
            existing = current.get("lead_capture")
            if not isinstance(existing, dict):
                existing = {}
            merged = {**existing}
            for key, value in (lead_capture_updates or {}).items():
                if value is None:
                    continue
                if key in (
                    "trigger_conditions_cn",
                    "trigger_conditions_en",
                    "title_cn",
                    "title_en",
                    "description_cn",
                    "description_en",
                    "success_title_cn",
                    "success_title_en",
                    "success_text_cn",
                    "success_text_en",
                ):
                    merged[key] = value.strip() if isinstance(value, str) else str(value)
                else:
                    merged[key] = value

            self._dynamodb_table.put_item(Item={"pk": self._CONFIG_PK, "sk": "LEAD_CAPTURE", **merged})

            if purchase_intent_keywords is not None:
                kw = purchase_intent_keywords if isinstance(purchase_intent_keywords, dict) else {}
                self._dynamodb_table.put_item(
                    Item={
                        "pk": self._CONFIG_PK,
                        "sk": "PURCHASE_INTENT_KEYWORDS",
                        "cn": self._normalize_keyword_list(kw.get("cn")),
                        "en": self._normalize_keyword_list(kw.get("en")),
                    }
                )

            return self.get_lead_capture_triage_config()

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

    def save_manual_download_config(self, manual_downloads: list[dict] | None = None) -> dict:
        normalized = self._normalize_manual_downloads(manual_downloads)

        if self._backend == "dynamodb":
            self._ensure_dynamodb_seeded()
            assert self._dynamodb_table is not None
            self._dynamodb_table.put_item(
                Item={
                    "pk": self._CONFIG_PK,
                    "sk": "MANUAL_DOWNLOADS",
                    "items": normalized,
                }
            )
            return self.get_manual_download_config()

        config = self._load_config()
        config["manual_downloads"] = normalized
        self._write_config(config)
        return self.get_manual_download_config()

    def delete_recommendation(self, recommendation_id: str) -> dict | None:
        if self._backend == "dynamodb":
            self._ensure_dynamodb_seeded()
            assert self._dynamodb_table is not None
            target_id = recommendation_id.strip()
            if not target_id:
                raise ValueError("Recommendation id is required")
            existing = self._dynamodb_table.get_item(
                Key={"pk": self._CATALOG_PK, "sk": target_id}
            ).get("Item")
            if not existing:
                return None
            self._dynamodb_table.delete_item(Key={"pk": self._CATALOG_PK, "sk": target_id})
            return {k: v for k, v in existing.items() if k not in {"pk", "sk"}}

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
