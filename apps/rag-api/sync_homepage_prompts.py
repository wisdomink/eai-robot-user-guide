from __future__ import annotations

import argparse
import json
import os
import ssl
import time
from pathlib import Path
from urllib import error, parse, request

from app.services.homepage_prompts_service import HomepagePromptsStorage


SYNC_MODES = ("seed-if-empty", "merge-additive", "upsert-all", "force-replace")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Sync homepage prompts from the repo JSON file to a deployed service API. "
            "Default mode 'upsert-all' overwrites every local page on the remote service "
            "without deleting any remote-only pages."
        ),
    )
    parser.add_argument(
        "--mode",
        choices=SYNC_MODES,
        default="upsert-all",
        help=(
            "Sync strategy executed against the deployed service:\n"
            "  seed-if-empty   only push when the remote has no pages\n"
            "  merge-additive  only create pages missing on remote (existing ids are skipped)\n"
            "  upsert-all      upsert every local page; do NOT delete remote-only pages (default)\n"
            "  force-replace   upsert every local page AND delete remote-only pages"
        ),
    )
    parser.add_argument(
        "--source",
        default=str(Path(__file__).resolve().parent / "data" / "homepage_prompts.json"),
        help="Source homepage prompts JSON file.",
    )
    parser.add_argument(
        "--api-base",
        required=True,
        help="Base URL of the deployed service, e.g. https://robotics-instruction-manual.ff.com",
    )
    parser.add_argument(
        "--token",
        default=os.getenv("FF_API_TOKEN", ""),
        help=(
            "Optional bearer token sent as 'Authorization: Bearer <token>'. "
            "Falls back to the FF_API_TOKEN environment variable."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only report the diff and the actions that would be taken; no write requests are sent.",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help=(
            "Skip TLS certificate verification. Useful on macOS when Python cannot find system CA "
            "certs. Prefer running '/Applications/Python 3.x/Install Certificates.command' or "
            "'pip install certifi' instead; only use this flag as a last resort."
        ),
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="HTTP request timeout in seconds.",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=5,
        help="Retry count when the deployed service is not ready yet.",
    )
    parser.add_argument(
        "--retry-delay",
        type=float,
        default=3.0,
        help="Delay between retries in seconds.",
    )
    return parser


def make_source_storage(source_path: Path) -> HomepagePromptsStorage:
    return HomepagePromptsStorage(source_path, backend="file")


def _build_ssl_context(insecure: bool) -> ssl.SSLContext | None:
    if insecure:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    try:
        import certifi  # Optional dependency; if available we'll use its CA bundle.

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

    raise RuntimeError(f"Failed to sync homepage prompts via API: {last_error}")


def fetch_remote_pages(
    *,
    api_base: str,
    timeout: float,
    retries: int,
    retry_delay: float,
    token: str = "",
    ssl_context: ssl.SSLContext | None = None,
) -> list[dict]:
    params = parse.urlencode({"all": "true"})
    data = _request_json(
        method="GET",
        url=f"{api_base.rstrip('/')}/api/get-homepage-prompts?{params}",
        payload=None,
        timeout=timeout,
        retries=retries,
        retry_delay=retry_delay,
        token=token,
        ssl_context=ssl_context,
    )
    pages = data.get("pages", [])
    return pages if isinstance(pages, list) else []


def save_remote_page(
    *,
    api_base: str,
    page: dict,
    timeout: float,
    retries: int,
    retry_delay: float,
    token: str = "",
    ssl_context: ssl.SSLContext | None = None,
) -> dict:
    return _request_json(
        method="POST",
        url=f"{api_base.rstrip('/')}/api/save-homepage-page",
        payload=page,
        timeout=timeout,
        retries=retries,
        retry_delay=retry_delay,
        token=token,
        ssl_context=ssl_context,
    )


def delete_remote_page(
    *,
    api_base: str,
    page_id: str,
    timeout: float,
    retries: int,
    retry_delay: float,
    token: str = "",
    ssl_context: ssl.SSLContext | None = None,
) -> dict:
    return _request_json(
        method="DELETE",
        url=f"{api_base.rstrip('/')}/api/delete-homepage-page/{parse.quote(page_id)}",
        payload=None,
        timeout=timeout,
        retries=retries,
        retry_delay=retry_delay,
        token=token,
        ssl_context=ssl_context,
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
                "id": prompt.get("id", ""),
                "enabled": bool(prompt.get("enabled", True)),
                "label": prompt.get("label", ""),
                "prompt": prompt.get("prompt", ""),
                "sort_order": int(prompt.get("sort_order", 0)),
            }
            for prompt in page.get("prompts", [])
            if isinstance(prompt, dict)
        ],
    }


def sync_via_existing_apis(
    *,
    api_base: str,
    mode: str,
    pages: list[dict],
    timeout: float,
    retries: int,
    retry_delay: float,
    token: str = "",
    dry_run: bool = False,
    ssl_context: ssl.SSLContext | None = None,
) -> dict:
    remote_pages = fetch_remote_pages(
        api_base=api_base,
        timeout=timeout,
        retries=retries,
        retry_delay=retry_delay,
        token=token,
        ssl_context=ssl_context,
    )
    remote_ids = {page.get("id", "") for page in remote_pages}
    source_ids = {page.get("id", "") for page in pages}

    if mode == "seed-if-empty" and remote_pages:
        return {
            "mode": mode,
            "dry_run": dry_run,
            "created": [],
            "updated": [],
            "deleted": [],
            "skipped": [page.get("id", "") for page in remote_pages],
            "message": "Remote service already contains homepage prompt pages. Nothing seeded.",
        }

    created: list[str] = []
    updated: list[str] = []
    deleted: list[str] = []
    skipped: list[str] = []

    for page in pages:
        page_id = page.get("id", "")
        if mode == "merge-additive" and page_id in remote_ids:
            skipped.append(page_id)
            continue

        if not dry_run:
            save_remote_page(
                api_base=api_base,
                page=to_save_payload(page),
                timeout=timeout,
                retries=retries,
                retry_delay=retry_delay,
                token=token,
                ssl_context=ssl_context,
            )

        if page_id in remote_ids:
            updated.append(page_id)
        else:
            created.append(page_id)

    if mode == "force-replace":
        for page in remote_pages:
            page_id = page.get("id", "")
            if not page_id or page_id in source_ids:
                continue
            if page.get("pattern") == "*":
                skipped.append(page_id)
                continue
            if not dry_run:
                delete_remote_page(
                    api_base=api_base,
                    page_id=page_id,
                    timeout=timeout,
                    retries=retries,
                    retry_delay=retry_delay,
                    token=token,
                    ssl_context=ssl_context,
                )
            deleted.append(page_id)

    prefix = "[DRY-RUN] " if dry_run else ""
    return {
        "mode": mode,
        "dry_run": dry_run,
        "created": created,
        "updated": updated,
        "deleted": deleted,
        "skipped": skipped,
        "message": (
            f"{prefix}Synced homepage prompts via existing APIs: created {len(created)}, "
            f"updated {len(updated)}, deleted {len(deleted)}, skipped {len(skipped)}."
        ),
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    source_path = Path(args.source).expanduser().resolve()
    if not source_path.exists():
        raise FileNotFoundError(f"Source homepage prompts file not found: {source_path}")

    source_storage = make_source_storage(source_path)
    source_pages = source_storage.list_pages(include_disabled=True)
    ssl_context = _build_ssl_context(args.insecure)
    if args.insecure:
        print("[warn] TLS verification disabled via --insecure.")
    summary = sync_via_existing_apis(
        api_base=args.api_base,
        mode=args.mode,
        pages=source_pages,
        timeout=args.timeout,
        retries=args.retries,
        retry_delay=args.retry_delay,
        token=args.token.strip(),
        dry_run=args.dry_run,
        ssl_context=ssl_context,
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
