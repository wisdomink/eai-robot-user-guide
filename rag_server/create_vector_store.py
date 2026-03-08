#!/usr/bin/env python3
"""
Create an OpenAI Vector Store and upload all manual Markdown pages.

The Vector Store is used by:
  - The Agents SDK (FileSearchTool) for AI-powered Q&A
  - The /search endpoint (Vector Store Search API) for semantic search

Usage:
    cd rag_server
    source venv/bin/activate
    python create_vector_store.py
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = PROJECT_ROOT / "src" / "content"
SIDEBAR_PATH = CONTENT_DIR / "sidebar-master-ultra.json"
PAGES_DIR = CONTENT_DIR / "pages"


def build_file_list() -> list[Path]:
    """Collect all page markdown files referenced in sidebar-master-ultra.json."""
    with open(SIDEBAR_PATH, "r", encoding="utf-8") as f:
        sidebar = json.load(f)

    files: list[Path] = []
    for section in sidebar.get("sections", []):
        for page in section.get("pages", []):
            filepath = PAGES_DIR / page["file"]
            if filepath.exists():
                files.append(filepath)
            else:
                print(f"⚠️  {page['file']} not found, skipping")
    return files


def get_existing_vector_store(store_id: str):
    """Try to retrieve an existing vector store by ID. Returns None if not found."""
    if not store_id:
        return None
    try:
        vs = client.vector_stores.retrieve(store_id)
        return vs
    except Exception:
        return None


def delete_old_files(store_id: str):
    """Delete all files from an existing vector store."""
    deleted = 0
    file_list = client.vector_stores.files.list(vector_store_id=store_id)
    for vs_file in file_list:
        client.vector_stores.files.delete(
            vector_store_id=store_id, file_id=vs_file.id
        )
        client.files.delete(vs_file.id)
        deleted += 1
    return deleted


def main():
    md_files = build_file_list()
    print(f"📁 Found {len(md_files)} markdown files to upload\n")

    existing_id = os.getenv("OPENAI_VECTOR_STORE_ID", "")
    vector_store = get_existing_vector_store(existing_id)

    if vector_store:
        print(f"📦 Existing Vector Store found: {vector_store.id}")
        deleted = delete_old_files(vector_store.id)
        print(f"🗑  Deleted {deleted} old file(s) from the store")
    else:
        vector_store = client.vector_stores.create(name="FF Robot User Manual")
        print(f"📦 New Vector Store created: {vector_store.id}")

    # Upload files in batch
    file_streams = [open(f, "rb") for f in md_files]
    try:
        batch = client.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store.id,
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

    print(f"\n{'='*50}")
    print(f"✅ Vector Store ready!")
    print(f"   ID: {vector_store.id}")
    print(f"{'='*50}")
    if vector_store.id != existing_id:
        print(f"\n👉 Add to your .env file:")
        print(f"   OPENAI_VECTOR_STORE_ID={vector_store.id}\n")


if __name__ == "__main__":
    main()
