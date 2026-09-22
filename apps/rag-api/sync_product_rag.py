#!/usr/bin/env python3
"""Synchronize one product's published Markdown to its dedicated RAG store. Default: preview."""
import argparse
import fcntl
import hashlib
import json
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANAGER = "product-manual-sync-v1"


def load_pages(content_dir, product, base_url=""):
    sidebar = json.loads((content_dir / "sidebar.json").read_text())
    if product not in sidebar:
        raise ValueError(f"Unknown product: {product}; available: {', '.join(sidebar)}")
    pages = {}
    names = set()
    for section in sidebar[product]["sections"]:
        for page in section["pages"]:
            relative = page["file"]
            path = (content_dir / "pages" / relative).resolve()
            if not path.is_relative_to((content_dir / "pages").resolve()):
                raise ValueError(f"Invalid page path: {relative}")
            if relative in pages or path.name in names:
                raise ValueError(f"Duplicate page/filename: {relative}")
            body = path.read_text(encoding="utf-8")
            if not body.strip():
                raise ValueError(f"Empty page: {relative}")
            # Web search resolves citations using the original Markdown basename.
            if base_url:
                body = body.replace("](/", f"]({base_url.rstrip('/')}/")
            payload = (f"Product: {sidebar[product]['title']}\nProduct ID: {product}\n"
                       f"Page: {page['title']}\nSource: {base_url.rstrip('/')}{page['slug']}\n\n{body}").encode()
            pages[relative] = {"name": path.name, "payload": payload,
                               "sha256": hashlib.sha256(payload).hexdigest()}
            names.add(path.name)
    if not pages:
        raise ValueError("Refusing to synchronize an empty product")
    return pages


def plan_sync(pages, remote, product):
    keep, remove = {}, []
    for item in remote:
        attrs = item.get("attributes") or {}
        if attrs.get("product_id") not in (None, "", product):
            raise ValueError(f"Store contains another product: {item['id']}; refusing replacement")
        path = attrs.get("source_path")
        if (attrs.get("managed_by") == MANAGER and path in pages
                and attrs.get("sha256") == pages[path]["sha256"]
                and item["status"] == "completed" and path not in keep):
            keep[path] = item["id"]
        else:
            remove.append(item["id"])
    return {"upload": [path for path in pages if path not in keep], "keep": keep, "detach": remove}


def inventory(client, store_id):
    return [{"id": f.id, "attributes": f.attributes, "status": f.status,
             "name": client.files.retrieve(f.id).filename}
            for f in client.vector_stores.files.list(vector_store_id=store_id)]


def atomic_save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    temp.replace(path)


def scan_references(client, candidates):
    """A failed/incomplete scan raises; never interpret inaccessible data as no references."""
    refs = {file_id: [] for file_id in candidates}
    for store in client.vector_stores.list():
        for file in client.vector_stores.files.list(vector_store_id=store.id):
            if file.id in refs:
                refs[file.id].append(store.id)
    return refs


def clean_files(client, state, report, save):
    pending = set(state["pending_cleanup"])
    # Legacy/previous-script files have no reliable ownership evidence: retain globally.
    unknown = pending - set(state["owned"])
    for file_id in sorted(unknown):
        state["retained_legacy"][file_id] = "Ownership/other uses unknown; detached only"
        state["pending_cleanup"].remove(file_id)
    save()
    candidates = pending - unknown
    report["cleanup"] = {"retained_legacy": sorted(state["retained_legacy"]), "deleted": [], "deferred": {}}
    if not candidates:
        save()
        return
    try:
        refs = scan_references(client, candidates)
    except Exception as exc:
        report["cleanup"]["error"] = f"Reference scan failed; all global deletes skipped: {exc}"
        save()
        return
    for file_id in sorted(candidates):
        if refs[file_id]:
            report["cleanup"]["deferred"][file_id] = refs[file_id]
            continue
        try:
            client.files.delete(file_id)
        except Exception as exc:
            if getattr(exc, "status_code", None) != 404:
                report["cleanup"]["deferred"][file_id] = str(exc)
                continue
        state["pending_cleanup"].remove(file_id)
        state["owned"].pop(file_id, None)
        report["cleanup"]["deleted"].append(file_id)
        save()
    save()


def verify_store(client, store_id, product, pages, report, save, attempts=6, interval=2):
    """Allow bounded visibility lag; only read, never repair/delete while verifying."""
    history = report.setdefault("verification", [])
    for attempt in range(1, attempts + 1):
        snapshot = inventory(client, store_id)
        remaining = plan_sync(pages, snapshot, product)
        history.append({"attempt": attempt, "remaining": remaining, "remote": snapshot})
        save()
        if not remaining["upload"] and not remaining["detach"]:
            return
        print(f"Verification {attempt}/{attempts}: missing_or_changed={len(remaining['upload'])}, "
              f"extra_or_old={len(remaining['detach'])}", flush=True)
        if attempt < attempts:
            time.sleep(interval)
    raise RuntimeError(
        f"Post-sync verification failed after {attempts} checks: "
        f"missing_or_changed={remaining['upload']}, extra_or_old={remaining['detach']}; "
        "global cleanup skipped; see report.verification")


def apply_plan(client, store_id, product, pages, remote, plan, state, report, save, poll_seconds=600):
    for path in plan["upload"]:
        page = pages[path]
        report.update(stage="uploading_file", current_page=path)
        save()
        print(f"Uploading: {path} ({len(page["payload"])} bytes)", flush=True)
        uploaded = client.files.create(file=(page["name"], page["payload"], "text/markdown"), purpose="assistants")
        # Persist ownership BEFORE attachment. These files are dedicated to this workflow.
        state["owned"][uploaded.id] = {"path": path, "sha256": page["sha256"]}
        state["pending_cleanup"].append(uploaded.id)
        report.setdefault("uploaded", []).append({"path": path, "file_id": uploaded.id})
        save()
        report.update(stage="attaching_file", current_file_id=uploaded.id)
        save()
        attached = client.vector_stores.files.create(
            vector_store_id=store_id, file_id=uploaded.id,
            attributes={"managed_by": MANAGER, "product_id": product,
                        "source_path": path, "sha256": page["sha256"]})
        report["stage"] = "indexing_file"
        save()
        deadline = time.monotonic() + poll_seconds
        while attached.status == "in_progress":
            if time.monotonic() >= deadline:
                raise TimeoutError(f"Indexing timed out for {path}; old documents retained")
            time.sleep(1)
            attached = client.vector_stores.files.retrieve(uploaded.id, vector_store_id=store_id)
        if attached.status != "completed":
            raise RuntimeError(f"Indexing failed for {path}: {attached.status}")
    # Re-check current files and index status before any destructive action.
    current = inventory(client, store_id)
    final = plan_sync(pages, current, product)
    if final["upload"]:
        raise RuntimeError("Required pages not indexed; old files retained")
    expected_ids = {f["id"] for f in remote} | {f["file_id"] for f in report.get("uploaded", [])}
    if {f["id"] for f in current} != expected_ids:
        raise RuntimeError("Store changed concurrently; refusing deletion, rerun preview")
    # Exclude every retained live file from garbage collection, including resumed uploads.
    state["pending_cleanup"] = sorted((set(state["pending_cleanup"]) | set(final["detach"])) - set(final["keep"].values()))
    save()
    for file_id in final["detach"]:
        try:
            client.vector_stores.files.delete(file_id=file_id, vector_store_id=store_id)
        except Exception as exc:
            if getattr(exc, "status_code", None) != 404:
                raise
        report.setdefault("detached", []).append(file_id)
        save()
    verify_store(client, store_id, product, pages, report, save)
    report["status"] = "verified"
    save()
    clean_files(client, state, report, save)
    if state["pending_cleanup"]:
        report["status"] = "verified_cleanup_pending"
        save()


def create_product_store(client, product, report, save):
    name = f"{product} manuals"
    report["stage"] = "checking_existing_stores"
    save()
    matches = [store.id for store in client.vector_stores.list() if store.name == name]
    if matches:
        report["existing_store_candidates"] = matches
        save()
        raise ValueError(f"Existing store(s) named {name}: {matches}; configure the intended ID before retrying")
    report["stage"] = "creating_store"
    save()
    # A timeout does not prove creation failed. Do not automatically repeat this POST.
    created = client.with_options(max_retries=0).vector_stores.create(name=name)
    report.update(store_id=created.id, stage="store_created")
    save()
    return created.id


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--product", required=True)
    parser.add_argument("--request-timeout", type=float, default=600, help="Read/write timeout seconds (default: 600)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--dry-run", action="store_true", help="Default: preview, no remote writes")
    parser.add_argument("--local-only", action="store_true")
    parser.add_argument("--env-file", type=Path, default=Path(__file__).with_name(".env"))
    parser.add_argument("--content-dir", type=Path, default=ROOT / "apps/web/src/content")
    parser.add_argument("--product-store-id")
    parser.add_argument("--base-url", default="")
    parser.add_argument("--create-product-store", action="store_true")
    parser.add_argument("--state-dir", type=Path, default=ROOT / ".logs/rag-sync-state")
    parser.add_argument("--report", type=Path, default=ROOT / ".logs" / f"rag-sync-{time.time_ns()}.json")
    args = parser.parse_args()
    if args.request_timeout <= 0:
        parser.error("--request-timeout must be positive")
    if args.local_only and args.apply:
        parser.error("--local-only cannot be used with --apply")
    report = {"product": args.product, "apply": args.apply, "status": "starting"}
    try:
        pages = load_pages(args.content_dir, args.product, args.base_url)
        print(f"{args.product}: {len(pages)} validated pages")
        if args.local_only:
            return 0
        from dotenv import load_dotenv
        from openai import OpenAI
        load_dotenv(args.env_file, override=True)
        key = "OPENAI_VECTOR_STORE_" + args.product.upper().replace("-", "_") + "_ID"
        store = (args.product_store_id or os.getenv(key, "")).strip()
        if not store and not args.create_product_store:
            raise ValueError(f"Missing {key}; supply it or --create-product-store")
        # Reject known non-product or differently mapped targets, but never write to them.
        for env_key, value in os.environ.items():
            if (store and env_key.startswith("OPENAI_VECTOR_STORE_") and env_key.endswith("_ID")
                    and env_key != key and value.strip() == store):
                raise ValueError(f"Target also mapped by {env_key}; refusing non-dedicated store")
        import httpx
        client = OpenAI(timeout=httpx.Timeout(args.request_timeout, connect=30, pool=30), max_retries=2)
        atomic_save(args.report, report)  # Check report writability before remote mutations.
        if not store and args.apply:
            store = create_product_store(client, args.product, report,
                                         lambda: atomic_save(args.report, report))
            print(f"Created store: {key}={store}; save this ID before retrying")
        if store:
            client.vector_stores.retrieve(store)
        report["store_id"] = store
        state_key = hashlib.sha256(store.encode()).hexdigest() if store else "new-store-preview"
        args.state_dir.mkdir(parents=True, exist_ok=True)
        state_path = args.state_dir / f"{state_key}.json"
        if args.report.resolve() == state_path.resolve():
            raise ValueError("Report and state paths must differ")
        with (args.state_dir / f"{state_key}.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            state = json.loads(state_path.read_text()) if state_path.exists() else {
                "store_id": store, "product": args.product, "owned": {},
                "pending_cleanup": [], "retained_legacy": {}}
            if state["store_id"] != store or state["product"] != args.product:
                raise ValueError("State belongs to a different store/product")
            def save():
                if args.apply:
                    atomic_save(state_path, state)
                atomic_save(args.report, report)
            remote = inventory(client, store) if store else []
            plan = plan_sync(pages, remote, args.product)
            report.update(status="planned", plan=plan, remote_before=remote,
                          pending_cleanup=list(state["pending_cleanup"]),
                          global_delete_eligible=[f for f in plan["detach"] if f in state["owned"]],
                          legacy_detach_only=[f for f in plan["detach"] if f not in state["owned"]])
            save()
            print(json.dumps(report, ensure_ascii=False, indent=2))
            if args.apply:
                apply_plan(client, store, args.product, pages, remote, plan, state, report, save)
            print(f"Status: {report['status']}; report: {args.report}")
            return 2 if report["status"] == "verified_cleanup_pending" else 0
    except Exception as exc:
        report.update(error=str(exc), error_type=type(exc).__name__,
                      error_cause=type(exc.__cause__).__name__ if exc.__cause__ else None,
                      status="failed")
        atomic_save(args.report, report)
        print(f"FAILED: {exc}; report: {args.report}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
