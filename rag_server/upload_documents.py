#!/usr/bin/env python3
"""
Upload markdown manual pages to an OpenAI Vector Store for file_search.

Creates a new Vector Store (or updates an existing one) and uploads all
markdown files referenced in sidebar.json.

Usage:
    cd rag_server
    source venv/bin/activate

    # Create a new Vector Store and upload all documents:
    python upload_documents.py

    # Replace files in an existing Vector Store:
    python upload_documents.py --vector-store-id vs_xxx
"""

import argparse
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    timeout=120.0,
    max_retries=3,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = PROJECT_ROOT / "src" / "content"
SIDEBAR_PATH = CONTENT_DIR / "sidebar.json"
PAGES_DIR = CONTENT_DIR / "pages"


def build_file_list() -> list[Path]:
    """Collect all page markdown files referenced in sidebar.json."""
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


def upload_file_with_retry(filepath: Path, max_retries: int = 3) -> str:
    """Upload a single file to OpenAI with retry on timeout."""
    for attempt in range(1, max_retries + 1):
        try:
            with open(filepath, "rb") as f:
                file_obj = client.files.create(file=f, purpose="assistants")
            return file_obj.id
        except Exception as e:
            if attempt < max_retries:
                wait = attempt * 5
                print(f"   ⏳ Retry {attempt}/{max_retries} for {filepath.name} in {wait}s... ({e})")
                time.sleep(wait)
            else:
                raise


def main():
    parser = argparse.ArgumentParser(
        description="Upload manual pages to an OpenAI Vector Store."
    )
    parser.add_argument(
        "--vector-store-id",
        default=os.getenv("OPENAI_VECTOR_STORE_ID", ""),
        help="Existing Vector Store ID to update (creates new if omitted)",
    )
    args = parser.parse_args()

    md_files = build_file_list()
    print(f"📁 Found {len(md_files)} markdown files to upload\n")

    # 1. Create or reuse Vector Store
    if args.vector_store_id:
        vector_store_id = args.vector_store_id
        print(f"📦 Using existing Vector Store: {vector_store_id}\n")
    else:
        vector_store = client.vector_stores.create(name="FF Robot User Manual")
        vector_store_id = vector_store.id
        print(f"📦 Vector Store created: {vector_store_id}\n")

    # 2. Upload files one by one
    file_ids: list[str] = []
    for i, filepath in enumerate(md_files, 1):
        print(f"   [{i:2d}/{len(md_files)}] Uploading {filepath.name}...", end=" ", flush=True)
        fid = upload_file_with_retry(filepath)
        file_ids.append(fid)
        print("✓")

    print(f"\n✅ All {len(file_ids)} files uploaded. Attaching to Vector Store...")

    # 3. Attach files to Vector Store in batches
    batch_size = 10
    for i in range(0, len(file_ids), batch_size):
        batch_ids = file_ids[i : i + batch_size]
        batch = client.vector_stores.file_batches.create_and_poll(
            vector_store_id=vector_store_id,
            file_ids=batch_ids,
        )
        print(
            f"   Batch {i // batch_size + 1}: "
            f"{batch.file_counts.completed} indexed, "
            f"{batch.file_counts.failed} failed"
        )

    print(f"\n{'='*50}")
    print(f"✅ Documents uploaded!")
    print(f"   Vector Store: {vector_store_id}")
    print(f"   Files:        {len(file_ids)}")
    print(f"{'='*50}")

    if not args.vector_store_id:
        print(f"\n👉 Add to your .env file:")
        print(f"   OPENAI_VECTOR_STORE_ID={vector_store_id}\n")


if __name__ == "__main__":
    main()
