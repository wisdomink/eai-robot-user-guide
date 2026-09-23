#!/usr/bin/env python3
"""Stage immutable product releases in a shared store; activation is explicit.

Never detaches associations or deletes Files. Old releases remain available for rollback.
"""
import argparse
import fcntl
import hashlib
import json
import os
import time
from pathlib import Path

from sync_product_rag import ROOT, load_pages, atomic_save
from app.services.manuals_index import validate_manifest, release_filter, matches_filter

MANAGER = "shared-manuals-v1"


def build_release(content_dir, product, language="en", base_url=""):
    pages = load_pages(content_dir, product, base_url)
    sidebar = json.loads((content_dir / "sidebar.json").read_text())
    slugs = {p["file"]: p["slug"] for s in sidebar[product]["sections"] for p in s["pages"]}
    identity = [(path, page["sha256"], slugs[path], language) for path, page in sorted(pages.items())]
    release = hashlib.sha256(json.dumps(identity, ensure_ascii=False).encode()).hexdigest()
    for path, page in pages.items():
        page["attributes"] = {"managed_by": MANAGER, "product_id": product,
                              "source_path": path, "page_slug": slugs[path], "language": language,
                              "content_hash": page["sha256"], "release_id": release}
        if any(len(str(v)) > 512 for v in page["attributes"].values()):
            raise ValueError(f"Metadata value exceeds 512 characters: {path}")
        page["name"] = f"{product}-{hashlib.sha256(path.encode()).hexdigest()[:12]}-{release[:12]}.md"
    return release, pages


def inspect_release(client, store_id, product, release, pages):
    """Reject conflicting/failed/duplicate documents instead of deleting anything."""
    present = {}
    for item in client.vector_stores.files.list(vector_store_id=store_id):
        attrs = item.attributes or {}
        if attrs.get("product_id") != product or attrs.get("release_id") != release:
            continue
        path = attrs.get("source_path")
        if path not in pages or attrs != pages[path]["attributes"] or path in present:
            raise ValueError(f"Conflicting release metadata for {product}: {item.id}")
        if item.status != "completed":
            raise ValueError(f"Release file is not completed: {item.id} ({item.status})")
        present[path] = item.id
    return present


def stage_release(client, store_id, product, release, pages, report, save):
    present = inspect_release(client, store_id, product, release, pages)
    for path, page in pages.items():
        if path in present:
            continue
        uploaded = client.files.create(file=(page["name"], page["payload"], "text/markdown"), purpose="assistants")
        # Journal the Files ID before attaching. Interrupted/orphan uploads are never deleted automatically.
        report["uploads"].append({"file_id": uploaded.id, "product_id": product, "source_path": path})
        save()
        client.vector_stores.files.create(vector_store_id=store_id, file_id=uploaded.id, attributes=page["attributes"])
        deadline = time.monotonic() + 600
        while True:
            attached = client.vector_stores.files.retrieve(uploaded.id, vector_store_id=store_id)
            if attached.status == "completed":
                break
            if attached.status in {"failed", "cancelled"} or time.monotonic() >= deadline:
                raise RuntimeError(f"Ingestion failed/timed out: {uploaded.id}; old manifest retained")
            time.sleep(2)
    for attempt in range(6):
        present = inspect_release(client, store_id, product, release, pages)
        if set(present) == set(pages):
            return
        if attempt < 5:
            time.sleep(2)
    raise RuntimeError(f"Incomplete release: {product}")


def verify_search(client, store_id, product, release):
    filters = release_filter({product: release})
    for attempt in range(6):
        result = client.vector_stores.search(vector_store_id=store_id, query=f"{product} manual", filters=filters, max_num_results=1)
        if result.data and all(matches_filter(hit.attributes or {}, filters) for hit in result.data):
            return
        if attempt < 5:
            time.sleep(2)
    raise RuntimeError(f"Release is not searchable: {product}")


def publish(client, store_id, builds, manifest_path, report, save, activate=False):
    old = json.loads(manifest_path.read_text()) if manifest_path.exists() else None
    releases = validate_manifest(old, store_id) if old else {}
    for product, (release, pages) in builds.items():
        stage_release(client, store_id, product, release, pages, report, save)
        releases[product] = release
    # Recheck every selected release before the single atomic activation.
    for product, (release, pages) in builds.items():
        if set(inspect_release(client, store_id, product, release, pages)) != set(pages):
            raise RuntimeError(f"Release changed while publishing: {product}")
        verify_search(client, store_id, product, release)
    candidate = {"schema_version": 1, "vector_store_id": store_id, "releases": releases}
    report["candidate_manifest"] = candidate
    save()
    if activate and candidate != old:
        if old:
            atomic_save(manifest_path.with_suffix(".previous.json"), old)
        atomic_save(manifest_path, candidate)
    report["activated"] = activate
    save()
    return candidate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    selected = parser.add_mutually_exclusive_group(required=True)
    selected.add_argument("--product")
    selected.add_argument("--all", action="store_true")
    parser.add_argument("--apply", action="store_true", help="Upload and verify; default is remote read-only preview")
    parser.add_argument("--activate", action="store_true", help="Requires --apply; atomically update the effective manifest")
    parser.add_argument("--local-only", action="store_true")
    parser.add_argument("--create-store", action="store_true", help="Requires --apply; create a new manuals store")
    parser.add_argument("--store-id")
    parser.add_argument("--env-file", type=Path, default=Path(__file__).with_name(".env"))
    parser.add_argument("--content-dir", type=Path, default=ROOT / "apps/web/src/content")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--report", type=Path, default=ROOT / ".logs" / f"manuals-sync-{time.time_ns()}.json")
    parser.add_argument("--language", default="en")
    parser.add_argument("--base-url", default="")
    args = parser.parse_args()
    if (args.activate or args.create_store) and not args.apply:
        parser.error("--activate/--create-store requires --apply")
    if args.local_only and args.apply:
        parser.error("--local-only cannot be combined with --apply")
    from dotenv import load_dotenv
    load_dotenv(args.env_file, override=True)
    manifest = args.manifest or Path(os.getenv("MANUALS_RELEASE_MANIFEST", str(Path(__file__).parent / "data/manuals-releases.json")))
    products = list(json.loads((args.content_dir / "sidebar.json").read_text())) if args.all else [args.product]
    builds = {p: build_release(args.content_dir, p, args.language, args.base_url) for p in products}
    report = {"products": {p: {"release_id": r, "pages": len(pages)} for p, (r, pages) in builds.items()}, "uploads": [], "activated": False}
    save = lambda: atomic_save(args.report, report)
    save()
    if args.local_only:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    store_id = args.store_id or os.getenv("OPENAI_VECTOR_STORE_MANUALS_ID", "")
    if args.create_store and (store_id or manifest.exists()):
        parser.error("Creating a store requires no existing store ID or manifest; use recorded ID to resume")
    if not store_id and not args.create_store:
        parser.error("Set OPENAI_VECTOR_STORE_MANUALS_ID or --store-id")
    legacy_ids = {v for k, v in os.environ.items() if k.startswith("OPENAI_VECTOR_STORE_") and k.endswith("_ID") and k != "OPENAI_VECTOR_STORE_MANUALS_ID" and v}
    if store_id in legacy_ids:
        parser.error("Refusing to use a legacy/product/price/news store as shared manuals")
    from openai import OpenAI
    client = OpenAI(timeout=60, max_retries=2)
    # All publishers of this deployment must use this same manifest path/lock.
    manifest.parent.mkdir(parents=True, exist_ok=True)
    with manifest.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            if args.create_store:
                if manifest.exists():
                    raise ValueError("Manifest created concurrently; refusing new store")
                if any(s.name == "manuals" for s in client.vector_stores.list()):
                    raise ValueError("A manuals store already exists; specify its ID to resume")
                store_id = client.with_options(max_retries=0).vector_stores.create(name="manuals").id
            report["vector_store_id"] = store_id
            save()
            if args.apply:
                publish(client, store_id, builds, manifest, report, save, args.activate)
            else:
                if manifest.exists():
                    validate_manifest(json.loads(manifest.read_text()), store_id)
                report["missing"] = {p: sorted(set(pages) - inspect_release(client, store_id, p, r, pages).keys()) for p, (r, pages) in builds.items()}
                save()
        except Exception as exc:
            report["error"] = str(exc)
            save()
            print(f"Failed: {exc}; report: {args.report}")
            return 1
    print(f"{'Activated' if args.activate else 'Staged' if args.apply else 'Preview'}; store: {store_id}; report: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
