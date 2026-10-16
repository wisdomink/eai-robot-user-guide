from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import urlsplit
from uuid import uuid4

from app.services.homepage_prompts_service import HomepagePromptsStorage


DEFAULT_ORDER_NOW_URL = "https://shop.ff.com/"
DEFAULT_ORDER_NOW_RULES = json.loads(Path(__file__).with_name("order_now_defaults.json").read_text(encoding="utf-8"))
_DEFAULT_RULES = {
    rule_id: {**rule, "pattern": HomepagePromptsStorage._normalize_pattern(rule["pattern"])}
    for rule_id, rule in DEFAULT_ORDER_NOW_RULES.items()
}


class OrderNowStorage:
    """Independent config in the homepage DynamoDB table, or a local JSON file."""

    # ponytail: one config item (DynamoDB's 400 KB limit); split into rule items if the catalog grows.
    _KEY = {"pk": "ORDER_NOW", "sk": "CONFIG"}

    def __init__(
        self,
        data_path: Path,
        *,
        backend: str = "file",
        dynamodb_table: str = "",
        aws_region: str = "",
    ) -> None:
        self._data_path = data_path
        self._table = None
        if backend == "dynamodb":
            if not dynamodb_table:
                raise ValueError("HOMEPAGE_PROMPTS_DDB_TABLE is required for Order Now")
            import boto3

            resource = boto3.resource("dynamodb", **({"region_name": aws_region} if aws_region else {}))
            self._table = resource.Table(dynamodb_table)
        elif backend == "file":
            self._data_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            raise ValueError("Order Now backend must be file or dynamodb")

    @classmethod
    def from_config(cls) -> OrderNowStorage:
        from app.core.config import (
            AWS_REGION_NAME,
            HOMEPAGE_PROMPTS_BACKEND,
            HOMEPAGE_PROMPTS_DDB_TABLE,
            ORDER_NOW_DATA_PATH,
        )

        return cls(
            ORDER_NOW_DATA_PATH,
            backend=HOMEPAGE_PROMPTS_BACKEND,
            dynamodb_table=HOMEPAGE_PROMPTS_DDB_TABLE,
            aws_region=AWS_REGION_NAME,
        )

    def _read_rules(self) -> dict:
        if self._table is None:
            if not self._data_path.exists():
                self._write_file(deepcopy(_DEFAULT_RULES))
            return json.loads(self._data_path.read_text(encoding="utf-8"))["rules"]

        item = self._table.get_item(Key=self._KEY, ConsistentRead=True).get("Item")
        if item is None:
            from botocore.exceptions import ClientError

            try:
                self._table.put_item(
                    Item={**self._KEY, "rules": deepcopy(_DEFAULT_RULES)},
                    ConditionExpression="attribute_not_exists(pk)",
                )
            except ClientError as exc:
                if exc.response["Error"]["Code"] != "ConditionalCheckFailedException":
                    raise
            item = self._table.get_item(Key=self._KEY, ConsistentRead=True)["Item"]
        # The config item also marks initialization, even when every rule is deleted.
        return item["rules"]

    def _write_file(self, rules: dict) -> None:
        with NamedTemporaryFile(mode="w", encoding="utf-8", dir=self._data_path.parent, delete=False) as f:
            json.dump({"rules": rules}, f, ensure_ascii=False, indent=2)
            f.write("\n")
        Path(f.name).replace(self._data_path)

    def get_config(self, *, include_disabled: bool = False) -> dict:
        rules = sorted(self._read_rules().values(), key=lambda rule: (rule["pattern"], rule["id"]))
        return {
            "default_url": DEFAULT_ORDER_NOW_URL,
            "rules": [{"button_label": "Order Now", **rule} for rule in rules if include_disabled or rule["enabled"]],
        }

    @staticmethod
    def _validate_url(value: str, field: str) -> None:
        try:
            parsed = urlsplit(value)
            valid = (
                parsed.scheme in {"http", "https"}
                and parsed.hostname
                and parsed.port != 0
                and not parsed.username
                and not parsed.password
                and not any(char.isspace() for char in value)
                and "\\" not in value
            )
        except ValueError:
            valid = False
        if not valid:
            raise ValueError(f"{field} must be an absolute HTTP(S) URL")

    def save_rule(self, payload: dict) -> tuple[dict, bool]:
        label = str(payload.get("label", "")).strip()
        pattern = str(payload.get("pattern", "")).strip()
        target_url = str(payload.get("target_url", "")).strip()
        button_label = str(payload.get("button_label", "Order Now")).strip()
        if not label:
            raise ValueError("Rule name is required")
        if not button_label or len(button_label) > 40:
            raise ValueError("Button text must contain 1 to 40 characters")
        source_url = pattern[:-2] if pattern.endswith("/*") else pattern
        if "*" in source_url:
            raise ValueError("Source patterns only support a trailing /* wildcard")
        self._validate_url(source_url, "Source pattern")
        self._validate_url(target_url, "Target URL")
        pattern = HomepagePromptsStorage._normalize_pattern(pattern)
        rules = self._read_rules()
        rule_id = str(payload.get("id", "")).strip() or uuid4().hex
        if any(rule["pattern"] == pattern and rule["id"] != rule_id for rule in rules.values()):
            raise ValueError("A rule with this source pattern already exists")
        rule = {
            "id": rule_id,
            "label": label,
            "pattern": pattern,
            "target_url": target_url,
            "button_label": button_label,
            "enabled": bool(payload.get("enabled", True)),
        }
        if self._table is not None:
            result = self._table.update_item(
                Key=self._KEY,
                UpdateExpression="SET #rules.#id = :rule",
                ExpressionAttributeNames={"#rules": "rules", "#id": rule_id},
                ExpressionAttributeValues={":rule": rule},
                ReturnValues="ALL_OLD",
            )
            created = rule_id not in result.get("Attributes", {}).get("rules", {})
        else:
            created = rule_id not in rules
            rules[rule_id] = rule
            self._write_file(rules)
        return rule, created

    def delete_rule(self, rule_id: str) -> dict | None:
        rules = self._read_rules()
        if self._table is not None:
            result = self._table.update_item(
                Key=self._KEY,
                UpdateExpression="REMOVE #rules.#id",
                ExpressionAttributeNames={"#rules": "rules", "#id": rule_id},
                ReturnValues="ALL_OLD",
            )
            return result.get("Attributes", {}).get("rules", {}).get(rule_id)
        deleted = rules.pop(rule_id, None)
        if deleted is not None:
            self._write_file(rules)
        return deleted
