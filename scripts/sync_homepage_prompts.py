#!/usr/bin/env python3
"""Sync apps/rag-api/data/homepage_prompts.json to a deployed FF Assist API.

Run from the repo root:
    python3 scripts/sync_homepage_prompts.py

Requires FF_API_BASE env var (or pass --api-base). Set it once in your shell:
    export FF_API_BASE=https://your-deploy.ff.com

Common options:
    --mode          Sync strategy (default: upsert-all):
                      seed-if-empty   only push when remote has no pages
                      merge-additive  only create pages missing on remote
                      upsert-all      overwrite every local page on remote (default)
                      force-replace   upsert all + delete remote-only pages
    --token         Bearer token, or set FF_API_TOKEN env var
    --dry-run       Show diff without making any changes
    --insecure      Skip TLS certificate verification
    --source        Override source JSON path (default: apps/rag-api/data/homepage_prompts.json)
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RAG_ROOT = REPO_ROOT / "apps" / "rag-api"
sys.path.insert(0, str(RAG_ROOT))

import argparse
import json
import os
import ssl
import time
from urllib import error, parse, request

from app.services.homepage_prompts_service import HomepagePromptsStorage


SYNC_MODES = ("seed-if-empty", "merge-additive", "upsert-all", "force-replace")
_DEFAULT_SOURCE = str(RAG_ROOT / "data" / "homepage_prompts.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Sync homepage prompts from the repo JSON to a deployed service API. "
            "Default mode 'upsert-all' overwrites every local page on the remote "
            "without deleting remote-only pages."
        ),
    )
    parser.add_argument(
        "--mode",
        choices=SYNC_MODES,
        default="upsert-all",
        help="Sync strategy (default: upsert-all)",
    )
    parser.add_argument(
        "--source",
        default=_DEFAULT_SOURCE,
        help="Source homepage prompts JSON file.",
    )
    parser.add_argument(
        "--api-base",
        default=os.getenv("FF_API_BASE", "https://robotics-instruction-manual.ff.com"),
        help="Base URL of the deployed service (default: https://robotics-instruction-manual.ff.com, or set FF_API_BASE env var)",
    )
    parser.add_argument(
        "--token",
        default=os.getenv("FF_API_TOKEN", ""),
        help="Bearer token (or set FF_API_TOKEN env var)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only report the diff; no write requests are sent.",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Skip TLS certificate verification.",
    )
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--retries", type=int, default=5)
    parser.add_argument("--retry-delay", type=float, default=3.0)
    return parser


def _build_ssl_context(insecure: bool) -> ssl.SSLContext | None:
    if insecure:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return None


def _request_json(
    *,
    method: str,
    url: str,
    payload: dict | None,
    timeout: float,
    retries: int,
    retry_delay: float,
    token: str = "",
    ssl_context: ssl.SSLContext | None = None,
) -> dict:
    headers: dict[str, str] = {}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    urlopen_kwargs: dict = {"timeout": timeout}
    if ssl_context is not None and url.lower().startswith("https://"):
        urlopen_kwargs["context"] = ssl_context

    last_error: str | None = None
    for attempt in range(max(retries, 1)):
        req = request.Request(url, data=body, headers=headers, method=method)
        try:
            with request.urlopen(req, **urlopen_kwargs) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            last_error = f"HTTP {exc.code}: {detail}"
        except error.URLError as exc:
            last_error = str(exc)
        if attempt < max(retries, 1) - 1:
            time.sleep(retry_delay)

    raise RuntimeError(f"Request failed: {last_error}")


def fetch_remote_pages(*, api_base, timeout, retries, retry_delay, token="", ssl_context=None):
    params = parse.urlencode({"all": "true"})
    data = _request_json(
        method="GET",
        url=f"{api_base.rstrip('/')}/api/get-homepage-prompts?{params}",
        payload=None,
        timeout=timeout, retries=retries, retry_delay=retry_delay,
        token=token, ssl_context=ssl_context,
    )
    pages = data.get("pages", [])
    return pages if isinstance(pages, list) else []


def save_remote_page(*, api_base, page, timeout, retries, retry_delay, token="", ssl_context=None):
    return _request_json(
        method="POST",
        url=f"{api_base.rstrip('/')}/api/save-homepage-page",
        payload=page,
        timeout=timeout, retries=retries, retry_delay=retry_delay,
        token=token, ssl_context=ssl_context,
    )


def delete_remote_page(*, api_base, page_id, timeout, retries, retry_delay, token="", ssl_context=None):
    return _request_json(
        method="DELETE",
        url=f"{api_base.rstrip('/')}/api/delete-homepage-page/{parse.quote(page_id)}",
        payload=None,
        timeout=timeout, retries=retries, retry_delay=retry_delay,
        token=token, ssl_context=ssl_context,
    )


def to_save_payload(page: dict) -> dict:
    return {
        "id": page.get("id", ""),
        "pattern": page.get("pattern", ""),
        "label": page.get("label", ""),
        "greeting": page.get("greeting", ""),
        "placeholder": page.get("placeholder", ""),
        "info_text": page.get("info_text", ""),
        "prompts": [
            {
                "id": p.get("id", ""),
                "enabled": bool(p.get("enabled", True)),
                "label": p.get("label", ""),
                "prompt": p.get("prompt", ""),
                "sort_order": int(p.get("sort_order", 0)),
            }
            for p in page.get("prompts", [])
            if isinstance(p, dict)
        ],
    }


def sync_pages(*, api_base, mode, pages, timeout, retries, retry_delay, token="", dry_run=False, ssl_context=None):
    print("Fetching remote pages ...")
    remote_pages = fetch_remote_pages(
        api_base=api_base, timeout=timeout, retries=retries, retry_delay=retry_delay,
        token=token, ssl_context=ssl_context,
    )
    print(f"  Remote: {len(remote_pages)} pages found")
    print(f"  Local:  {len(pages)} pages to sync\n")

    remote_ids = {page.get("id", "") for page in remote_pages}
    source_ids = {page.get("id", "") for page in pages}

    if mode == "seed-if-empty" and remote_pages:
        print("Remote already has pages — nothing seeded (seed-if-empty mode).")
        return {
            "mode": mode, "dry_run": dry_run,
            "created": [], "updated": [], "deleted": [],
            "skipped": [p.get("id", "") for p in remote_pages],
            "message": "Remote already has pages. Nothing seeded.",
        }

    created, updated, deleted, skipped = [], [], [], []
    dry = "[DRY-RUN] " if dry_run else ""

    for page in pages:
        page_id = page.get("id", "")
        if mode == "merge-additive" and page_id in remote_ids:
            print(f"  skip   {page_id}  (already exists, merge-additive mode)")
            skipped.append(page_id)
            continue
        action = "update" if page_id in remote_ids else "create"
        print(f"  {dry}{action}  {page_id}  ({page.get('pattern', '')})")
        if not dry_run:
            save_remote_page(
                api_base=api_base, page=to_save_payload(page),
                timeout=timeout, retries=retries, retry_delay=retry_delay,
                token=token, ssl_context=ssl_context,
            )
        (updated if page_id in remote_ids else created).append(page_id)

    if mode == "force-replace":
        for page in remote_pages:
            page_id = page.get("id", "")
            if not page_id or page_id in source_ids:
                continue
            if page.get("pattern") == "*":
                print(f"  skip   {page_id}  (wildcard fallback page, not deleted)")
                skipped.append(page_id)
                continue
            print(f"  {dry}delete {page_id}  (remote-only, force-replace mode)")
            if not dry_run:
                delete_remote_page(
                    api_base=api_base, page_id=page_id,
                    timeout=timeout, retries=retries, retry_delay=retry_delay,
                    token=token, ssl_context=ssl_context,
                )
            deleted.append(page_id)

    return {
        "mode": mode, "dry_run": dry_run,
        "created": created, "updated": updated, "deleted": deleted, "skipped": skipped,
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    source_path = Path(args.source).expanduser().resolve()
    if not source_path.exists():
        print(f"ERROR: Source file not found: {source_path}", file=sys.stderr)
        return 1

    storage = HomepagePromptsStorage(source_path, backend="file")
    pages = storage.list_pages(include_disabled=True)
    ssl_context = _build_ssl_context(args.insecure)

    print(f"Source:  {source_path}  ({len(pages)} pages)")
    print(f"Target:  {args.api_base}")
    print(f"Mode:    {args.mode}")
    if args.dry_run:
        print("         [DRY-RUN — no changes will be written]")
    if args.insecure:
        print("WARNING: TLS verification disabled.")
    print()

    summary = sync_pages(
        api_base=args.api_base,
        mode=args.mode,
        pages=pages,
        timeout=args.timeout,
        retries=args.retries,
        retry_delay=args.retry_delay,
        token=args.token.strip(),
        dry_run=args.dry_run,
        ssl_context=ssl_context,
    )

    c, u, d, s = len(summary["created"]), len(summary["updated"]), len(summary["deleted"]), len(summary["skipped"])
    print(f"\nDone.  created {c}  updated {u}  deleted {d}  skipped {s}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
