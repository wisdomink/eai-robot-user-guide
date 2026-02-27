"""
Load sidebar.json → match Markdown files → split by headers → produce Documents.

Key guarantees:
- Image markdown syntax (![alt](url)) is preserved in every chunk.
- Each chunk carries metadata: file_path, page_title, section_title, url_path, header_path.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from llama_index.core.schema import Document

from app.core.config import PAGES_DIR, SIDEBAR_PATH


# ── sidebar.json parsing ─────────────────────────────────────────────────


def parse_sidebar(sidebar_path: Path = SIDEBAR_PATH) -> list[dict]:
    """Recursively extract every page entry from sidebar.json."""
    with open(sidebar_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    pages: list[dict] = []
    for section in data.get("sections", []):
        section_title = section.get("title", "")
        for page in section.get("pages", []):
            pages.append(
                {
                    "section_title": section_title,
                    "page_title": page["title"],
                    "slug": page["slug"],
                    "file": page["file"],
                }
            )
    return pages


# ── Markdown header-based splitting ──────────────────────────────────────

_HEADER_RE = re.compile(r"^(#{1,3})\s+(.+)$")


def _split_markdown_by_headers(
    text: str, base_metadata: dict
) -> list[Document]:
    """
    Split markdown content by H1–H3 headers.
    Each chunk contains the header line and all content until the next
    same-or-higher-level header.  Parent headers are tracked so the
    ``header_path`` metadata gives full context (e.g. "Battery > Status").
    """
    lines = text.split("\n")
    chunks: list[Document] = []

    headers: dict[int, str] = {1: "", 2: "", 3: ""}
    current_lines: list[str] = []

    def _flush():
        body = "\n".join(current_lines).strip()
        if not body:
            return
        header_path = " > ".join(
            h for h in (headers[1], headers[2], headers[3]) if h
        )
        chunks.append(
            Document(
                text=body,
                metadata={**base_metadata, "header_path": header_path},
            )
        )

    for line in lines:
        m = _HEADER_RE.match(line)
        if m:
            _flush()
            level = len(m.group(1))
            headers[level] = m.group(2).strip()
            for lvl in range(level + 1, 4):
                headers[lvl] = ""
            current_lines = [line]
        else:
            current_lines.append(line)

    _flush()
    return chunks


# ── Public API ───────────────────────────────────────────────────────────


def load_and_split_documents() -> list[Document]:
    """
    Load every page referenced in sidebar.json, split by markdown headers,
    and return a flat list of Documents ready for indexing.
    """
    pages = parse_sidebar()
    all_chunks: list[Document] = []

    for page in pages:
        file_path = PAGES_DIR / page["file"]
        if not file_path.exists():
            print(f"[loader] warning: {file_path} not found, skipping")
            continue

        content = file_path.read_text(encoding="utf-8")
        if not content.strip():
            continue

        base_metadata = {
            "file_path": page["file"],
            "page_title": page["page_title"],
            "section_title": page["section_title"],
            "url_path": page["slug"],
        }

        chunks = _split_markdown_by_headers(content, base_metadata)
        if chunks:
            all_chunks.extend(chunks)
        else:
            all_chunks.append(Document(text=content, metadata=base_metadata))

    print(f"[loader] loaded {len(all_chunks)} chunks from {len(pages)} pages")
    return all_chunks
