#!/usr/bin/env python3
"""Add missing product CTA rules through the API, preserving existing admin settings."""

import argparse
import json
from pathlib import Path
from urllib.request import Request, urlopen


DEFAULTS_PATH = Path(__file__).resolve().parents[1] / "apps/rag-api/app/services/order_now_defaults.json"


def request_json(url: str, payload: dict | None = None) -> dict:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(url, data=body, headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def missing_rules(defaults: list[dict], existing: list[dict]) -> list[dict]:
    ids = {rule["id"] for rule in existing}
    patterns = {rule["pattern"].rstrip("/") for rule in existing}
    return [rule for rule in defaults if rule["id"] not in ids and rule["pattern"].rstrip("/") not in patterns]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-base", default="http://127.0.0.1:8000")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    base = args.api_base.rstrip("/")
    defaults = list(json.loads(DEFAULTS_PATH.read_text(encoding="utf-8")).values())
    existing = request_json(f"{base}/api/get-order-now-config?all=true")["rules"]
    additions = missing_rules(defaults, existing)
    for rule in additions:
        print(f"{'Would add' if args.dry_run else 'Adding'} {rule['label']} [{rule['button_label']}] {rule['pattern']}")
        if not args.dry_run:
            request_json(f"{base}/api/save-order-now-rule", rule)
    print(f"{'Planned' if args.dry_run else 'Added'} {len(additions)} rules; existing rules were preserved.")


if __name__ == "__main__":
    main()
