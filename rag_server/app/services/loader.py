"""
Load sidebar.json → match Markdown files → split by headers → produce chunks.

Key guarantees:
- Image markdown syntax (![alt](url)) is preserved in every chunk.
- Each chunk carries rich metadata from sidebar.json: file_path, page_title,
  section_id, section_title, url_path, header_path, heading_anchor.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from app.core.config import PAGES_DIR, SIDEBAR_PATH


@dataclass
class Chunk:
    id: str
    text: str
    metadata: dict = field(default_factory=dict)


# ── sidebar.json parsing ─────────────────────────────────────────────────


def parse_sidebar(sidebar_path: Path = SIDEBAR_PATH) -> list[dict]:
    """Extract every page entry from sidebar.json,
    preserving the section_id for navigation context."""
    with open(sidebar_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    pages: list[dict] = []
    for section in data.get("sections", []):
        section_id = section.get("id", "")
        section_title = section.get("title", "")
        for page in section.get("pages", []):
            pages.append(
                {
                    "section_id": section_id,
                    "section_title": section_title,
                    "page_title": page["title"],
                    "slug": page["slug"],
                    "file": page["file"],
                }
            )
    return pages


# ── Heading anchor (must match frontend toAnchor in chunks.ts / MarkdownRenderer.tsx)

def _to_anchor(text: str) -> str:
    """Convert heading text to a URL-friendly anchor slug.
    Mirrors the frontend toAnchor() so links scroll to the right heading."""
    return re.sub(
        r"^-|-$", "",
        re.sub(r"\s+", "-",
               re.sub(r"[^a-z0-9\s-]", "", text.lower()))
    )


# ── Markdown header-based splitting ──────────────────────────────────────

_HEADER_RE = re.compile(r"^(#{1,3})\s+(.+)$")


def _split_markdown_by_headers(
    text: str, base_metadata: dict
) -> list[Chunk]:
    """Split markdown content by H1-H3 headers.

    Each chunk contains the header line and all content until the next
    same-or-higher-level header. Parent headers are tracked so the
    ``header_path`` metadata gives full context (e.g. "Battery > Status").

    Every chunk also gets a ``heading_anchor`` that matches the frontend's
    rendered heading ID, enabling deep-linking like ``/page#section-name``.
    """
    lines = text.split("\n")
    chunks: list[Chunk] = []

    headers: dict[int, str] = {1: "", 2: "", 3: ""}
    current_anchor: str = ""
    current_lines: list[str] = []

    def _flush():
        body = "\n".join(current_lines).strip()
        if not body:
            return
        header_path = " > ".join(
            h for h in (headers[1], headers[2], headers[3]) if h
        )
        meta = {
            **base_metadata,
            "header_path": header_path,
            "heading_anchor": current_anchor,
        }
        chunk_id = f"{meta['file_path']}#{current_anchor or 'top'}"
        chunks.append(Chunk(id=chunk_id, text=body, metadata=meta))

    for line in lines:
        m = _HEADER_RE.match(line)
        if m:
            _flush()
            level = len(m.group(1))
            heading_text = m.group(2).strip()
            headers[level] = heading_text
            current_anchor = _to_anchor(heading_text)
            for lvl in range(level + 1, 4):
                headers[lvl] = ""
            current_lines = [line]
        else:
            current_lines.append(line)

    _flush()
    return chunks


# ── Public API ───────────────────────────────────────────────────────────


def load_and_split_documents() -> list[Chunk]:
    """Load every page referenced in sidebar.json, split by markdown headers,
    and return a flat list of Chunks ready for indexing."""
    pages = parse_sidebar()
    all_chunks: list[Chunk] = []

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
            "section_id": page["section_id"],
            "section_title": page["section_title"],
            "url_path": page["slug"],
        }

        chunks = _split_markdown_by_headers(content, base_metadata)
        if chunks:
            all_chunks.extend(chunks)
        else:
            meta = {**base_metadata, "header_path": "", "heading_anchor": ""}
            all_chunks.append(
                Chunk(id=f"{page['file']}#top", text=content, metadata=meta)
            )

    print(f"[loader] loaded {len(all_chunks)} chunks from {len(pages)} pages")
    return all_chunks
