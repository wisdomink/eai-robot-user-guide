#!/usr/bin/env python3
"""
Sync price-focused Markdown files to the OpenAI price vector store.

This script intentionally uploads only files named `price_*.md` from
`apps/rag-api/price/` so the vector store stays focused on price retrieval
instead of mixing in the full spec sheet.

Usage:
    cd apps/rag-api
    source venv/bin/activate
    python create_price_vector_store.py
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

RAG_SERVER_ROOT = Path(__file__).resolve().parent
PRICE_DIR = RAG_SERVER_ROOT / "price"
VECTOR_STORE_ENV_KEY = "OPENAI_VECTOR_STORE_PRICE_ID"


def build_file_list() -> list[Path]:
    """Collect price-focused Markdown files only."""
    files = sorted(PRICE_DIR.glob("price_*.md"))
    return [path for path in files if path.is_file()]


def delete_all_files(store_id: str) -> int:
    """Delete every file from the vector store and return the count."""
    deleted = 0
    file_list = client.vector_stores.files.list(vector_store_id=store_id)
    for vs_file in file_list:
        client.vector_stores.files.delete(
            vector_store_id=store_id, file_id=vs_file.id
        )
        client.files.delete(vs_file.id)
        deleted += 1
    return deleted


def upload_files(store_id: str, md_files: list[Path]) -> None:
    """Batch-upload Markdown files to the vector store."""
    file_streams = [open(path, "rb") for path in md_files]
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
        for file_stream in file_streams:
            file_stream.close()


def main() -> None:
    store_id = os.getenv(VECTOR_STORE_ENV_KEY, "").strip()
    if not store_id:
        print(f"❌ {VECTOR_STORE_ENV_KEY} is not set in .env")
        sys.exit(1)

    if not os.getenv("OPENAI_API_KEY", "").strip():
        print("❌ OPENAI_API_KEY is not set in .env")
        sys.exit(1)

    try:
        vs = client.vector_stores.retrieve(store_id)
    except Exception as exc:
        print(f"❌ Cannot retrieve vector store {store_id}: {exc}")
        sys.exit(1)

    md_files = build_file_list()
    if not md_files:
        print(f"❌ No price markdown files found in {PRICE_DIR}")
        sys.exit(1)

    print(f"📦 Vector Store: {vs.name} ({vs.id})")
    print(f"📁 Found {len(md_files)} price markdown file(s):")
    for path in md_files:
        print(f"   - {path.name}")

    print("\n🗑  Deleting old files …")
    deleted = delete_all_files(store_id)
    print(f"   Deleted {deleted} file(s)\n")

    print(f"📤 Uploading {len(md_files)} file(s) …")
    upload_files(store_id, md_files)

    print(f"\n{'=' * 50}")
    print(f"✅ Price vector store sync complete! Vector Store: {vs.id}")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
