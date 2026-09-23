"""One atomic release manifest shared by chat and website search."""
import json
from pathlib import Path

from app.core import config


def validate_manifest(data: dict, store_id: str, required_products=()) -> dict[str, str]:
    if not isinstance(data, dict) or data.get("schema_version") != 1 or data.get("vector_store_id") != store_id:
        raise ValueError("Manuals manifest schema/store mismatch")
    releases = data.get("releases")
    if not isinstance(releases, dict) or not releases or any(
        not isinstance(k, str) or not k or not isinstance(v, str) or not v
        for k, v in releases.items()
    ):
        raise ValueError("Manuals manifest must contain product releases")
    if set(required_products) - releases.keys():
        raise ValueError("Manuals manifest is missing published products")
    return dict(releases)


def release_filter(releases: dict[str, str], product: str | None = None) -> dict:
    selected = {product: releases[product]} if product else releases
    groups = [{"type": "and", "filters": [
        {"type": "eq", "key": "product_id", "value": key},
        {"type": "eq", "key": "release_id", "value": release},
        {"type": "eq", "key": "managed_by", "value": "shared-manuals-v1"},
    ]} for key, release in sorted(selected.items())]
    return groups[0] if len(groups) == 1 else {"type": "or", "filters": groups}


def shared_snapshot() -> tuple[str, dict[str, str]] | None:
    if config.MANUALS_INDEX_MODE == "legacy":
        return None
    store_id = config.OPENAI_VECTOR_STORE_MANUALS_ID
    if not store_id:
        raise ValueError("Shared manuals store is not configured")
    # Read once per request. Atomic replacement never exposes a partial release map.
    data = json.loads(Path(config.MANUALS_RELEASE_MANIFEST).read_text())
    products = json.loads(config.SIDEBAR_PATH.read_text()).keys()
    return store_id, validate_manifest(data, store_id, products)


def matches_filter(attributes: dict, filters: dict) -> bool:
    """Fail closed locally too, if a remote response violates its search filter."""
    kind = filters["type"]
    if kind == "eq":
        return attributes.get(filters["key"]) == filters["value"]
    if kind == "and":
        return all(matches_filter(attributes, f) for f in filters["filters"])
    if kind == "or":
        return any(matches_filter(attributes, f) for f in filters["filters"])
    raise ValueError(f"Unsupported manuals filter: {kind}")
