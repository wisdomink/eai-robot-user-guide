#!/usr/bin/env python3
"""
Sync all manual Markdown pages to an OpenAI Vector Store.

Reads sidebar.json, collects every referenced .md file, then:
  1. Deletes ALL existing files from the target vector store
  2. Uploads the current set of .md files

The target vector store is identified by OPENAI_VECTOR_STORE_ROBOT_ALL_ID in .env.

Usage:
    cd apps/rag-api
    source venv/bin/activate
    python create_vector_store.py
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONTENT_DIR = PROJECT_ROOT / "apps" / "web" / "src" / "content"
SIDEBAR_PATH = CONTENT_DIR / "sidebar.json"
DEVELOPER_SIDEBAR_PATH = CONTENT_DIR / "developer-sidebar.json"
PAGES_DIR = CONTENT_DIR / "pages"

VECTOR_STORE_ENV_KEY = "OPENAI_VECTOR_STORE_ROBOT_ALL_ID"


def build_file_list() -> list[Path]:
    """Collect all page markdown files referenced in sidebar.json and developer-sidebar.json."""
    files: list[Path] = []

    with open(SIDEBAR_PATH, "r", encoding="utf-8") as f:
        all_sidebars: dict = json.load(f)

    for product_id, product_sidebar in all_sidebars.items():
        for section in product_sidebar.get("sections", []):
            for page in section.get("pages", []):
                filepath = PAGES_DIR / page["file"]
                if filepath.exists():
                    files.append(filepath)
                else:
                    print(f"⚠️  [{product_id}] {page['file']} not found, skipping")

    if DEVELOPER_SIDEBAR_PATH.exists():
        with open(DEVELOPER_SIDEBAR_PATH, "r", encoding="utf-8") as f:
            dev_sidebars: dict = json.load(f)
        for locale_id, product_sidebar in dev_sidebars.items():
            for section in product_sidebar.get("sections", []):
                for page in section.get("pages", []):
                    rel = page["file"]
                    filepath = CONTENT_DIR / rel
                    if filepath.exists():
                        files.append(filepath)
                    else:
                        print(f"⚠️  [dev:{locale_id}] {rel} not found, skipping")
    else:
        print(f"ℹ️  No {DEVELOPER_SIDEBAR_PATH.name} — skipping developer MDX files")

    return files


def delete_all_files(store_id: str) -> int:
    """Delete every file from the vector store, return count deleted."""
    deleted = 0
    file_list = client.vector_stores.files.list(vector_store_id=store_id)
    for vs_file in file_list:
        client.vector_stores.files.delete(
            vector_store_id=store_id, file_id=vs_file.id
        )
        client.files.delete(vs_file.id)
        deleted += 1
    return deleted


def upload_files(store_id: str, md_files: list[Path]):
    """Batch-upload markdown files to the vector store."""
    file_streams = [open(f, "rb") for f in md_files]
    try:
        batch = client.vector_stores.file_batches.upload_and_poll(
            vector_store_id=store_id,
            files=file_streams,
        )
        print(
            f"✅ Upload complete — "
            f"{batch.file_counts.completed} succeeded, "
            f"{batch.file_counts.failed} failed"
        )
    finally:
        for f in file_streams:
            f.close()


def main():
    store_id = os.getenv(VECTOR_STORE_ENV_KEY, "").strip()
    if not store_id:
        print(f"❌ {VECTOR_STORE_ENV_KEY} is not set in .env")
        sys.exit(1)

    try:
        vs = client.vector_stores.retrieve(store_id)
    except Exception as exc:
        print(f"❌ Cannot retrieve vector store {store_id}: {exc}")
        sys.exit(1)

    print(f"📦 Vector Store: {vs.name} ({vs.id})")

    md_files = build_file_list()
    print(f"📁 Found {len(md_files)} markdown files in sidebar.json\n")

    # Step 1 — purge old files
    print("🗑  Deleting old files …")
    deleted = delete_all_files(store_id)
    print(f"   Deleted {deleted} file(s)\n")

    # Step 2 — upload current files
    print(f"📤 Uploading {len(md_files)} file(s) …")
    upload_files(store_id, md_files)

    print(f"\n{'=' * 50}")
    print(f"✅ Sync complete!  Vector Store: {vs.id}")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
