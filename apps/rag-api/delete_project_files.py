#!/usr/bin/env python3
"""List or permanently delete every OpenAI File object in the current project.

This does not delete files on disk. It only operates on OpenAI's project-scoped
Files API, using the project associated with ``OPENAI_API_KEY``.

The default is a dry run. Pass ``--execute`` to enter deletion mode. In that
mode, the script asks once for confirmation before deleting the listed files.
At most 50 files are selected in each run; run the script again for the next
batch.

Set ``OPENAI_API_KEY`` below to a temporary key for the exact OpenAI project
that you intend to clean. This script deliberately does not load ``.env`` or
read an API key from the environment, so it cannot accidentally use a
production project key.

Usage:
    cd apps/rag-api
    python delete_project_files.py
    python delete_project_files.py --execute
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from typing import Iterator

from openai import OpenAI

# Paste only a temporary, project-scoped cleanup key here. Never commit it.
BATCH_SIZE = 50
OPENAI_API_KEY = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="List or permanently delete every OpenAI File in this project."
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Permanently delete the listed files. Without this flag, only list them.",
    )
    return parser.parse_args()


def iter_project_files(client: OpenAI) -> Iterator[object]:
    """Yield all project files, following the Files API cursor."""
    after: str | None = None

    while True:
        page = client.files.list(limit=1000, order="asc", after=after)
        yield from page.data

        if not page.has_more:
            return
        if not page.last_id:
            raise RuntimeError("Files API returned has_more=true without last_id.")
        after = page.last_id


def format_created_at(timestamp: int | None) -> str:
    if timestamp is None:
        return "unknown"
    return datetime.fromtimestamp(timestamp, tz=UTC).isoformat()


def confirm_all_deletions(file_count: int) -> bool:
    """Ask once for a deliberate confirmation before bulk deletion."""
    try:
        answer = input(
            f"Permanently delete all {file_count} listed file(s)? [y/N]: "
        ).strip().lower()
    except EOFError:
        print("No confirmation received; no files were deleted.")
        return False
    return answer in {"y", "yes"}


def main() -> int:
    args = parse_args()

    if not OPENAI_API_KEY.strip():
        print(
            "ERROR: Set OPENAI_API_KEY at the top of this script before running it.",
            file=sys.stderr,
        )
        return 1

    client = OpenAI(api_key=OPENAI_API_KEY)
    try:
        all_files = list(iter_project_files(client))
    except Exception as exc:
        print(f"ERROR: Could not list OpenAI project files: {exc}", file=sys.stderr)
        return 1

    if not all_files:
        print("No OpenAI project files remain.")
        return 0

    files = all_files[:BATCH_SIZE]
    remaining_count = len(all_files) - len(files)
    action = (
        "are eligible for deletion; one confirmation is required"
        if args.execute
        else "would be deleted"
    )
    print(
        f"Showing the next batch: {len(files)} of {len(all_files)} OpenAI project "
        f"file(s) {action}:"
    )
    for file in files:
        print(
            f"- {file.id}\t{file.filename}\t{file.bytes} bytes\t"
            f"purpose={file.purpose}\tcreated={format_created_at(file.created_at)}"
        )

    if not args.execute:
        print("\nDry run only. Re-run with --execute to permanently delete this batch.")
        return 0

    if not confirm_all_deletions(len(files)):
        print("No files were deleted.")
        return 0

    print("\nDeleting files …")
    failures: list[str] = []
    for file in files:
        try:
            client.files.delete(file.id)
            print(f"Deleted {file.id} ({file.filename})")
        except Exception as exc:
            failures.append(file.id)
            print(f"ERROR deleting {file.id} ({file.filename}): {exc}", file=sys.stderr)

    if failures:
        print(f"\nCompleted with {len(failures)} failure(s): {', '.join(failures)}", file=sys.stderr)
        return 1

    print(f"\nDeleted {len(files)} OpenAI project file(s) in this batch.")
    if remaining_count:
        print(f"{remaining_count} file(s) remain for later batches.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
