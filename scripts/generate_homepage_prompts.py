#!/usr/bin/env python3
"""Generate apps/rag-api/data/homepage_prompts.json from input/FF_Assist_QA_EN.md.

Run from the repo root:
    python3 scripts/generate_homepage_prompts.py

For each ## section in the EN markdown that contains a Path and Greeting,
this script extracts the first 3 ### questions and writes them as prompts
into the homepage config JSON. Existing page/prompt IDs are preserved when
patterns match, so a re-run after editing the markdown is safe.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RAG_ROOT = REPO_ROOT / "apps" / "rag-api"
EN_MD = REPO_ROOT / "input" / "FF_Assist_QA_EN.md"
OUT_JSON = RAG_ROOT / "data" / "homepage_prompts.json"

_PATH_RE = re.compile(r"\*\*Path:\*\*\s*`([^`]+)`", re.IGNORECASE)
_GREETING_RE = re.compile(r"\*\*Greeting:\*\*\s*(.+)$", re.IGNORECASE | re.MULTILINE)
_Q_RE = re.compile(r"^###\s+[\d.]+\s+(.+)$", re.MULTILINE)


def _import_storage():
    sys.path.insert(0, str(RAG_ROOT))
    from app.services.homepage_prompts_service import HomepagePromptsStorage
    return HomepagePromptsStorage


def parse_sections(text: str) -> list[dict]:
    parts = re.split(r"^## ", text, flags=re.MULTILINE)
    sections: list[dict] = []
    for raw in parts[1:]:
        title_line, _, rest = raw.partition("\n")
        title = title_line.strip()
        block = rest
        pm = _PATH_RE.search(block)
        if not pm:
            continue
        raw_path = pm.group(1).strip()
        gm = _GREETING_RE.search(block)
        greeting = gm.group(1).strip() if gm else ""
        questions = [m.group(1).strip() for m in _Q_RE.finditer(block)][:3]
        if len(questions) < 3:
            raise ValueError(f"Section {title!r} needs 3 ### questions, got {len(questions)}")
        sections.append({
            "title": title,
            "raw_path": raw_path,
            "greeting": greeting,
            "questions": questions,
        })
    return sections


def main() -> int:
    H = _import_storage()

    print(f"Reading:  {EN_MD}")
    if not EN_MD.exists():
        print(f"ERROR: File not found: {EN_MD}", file=sys.stderr)
        return 1

    old_data: dict = {}
    old_pages: list[dict] = []
    if OUT_JSON.exists():
        old_data = json.loads(OUT_JSON.read_text(encoding="utf-8"))
        old_pages = old_data.get("pages", [])
        print(f"Existing: {OUT_JSON} ({len(old_pages)} pages)")
    else:
        print(f"Existing: (none, will create {OUT_JSON})")

    pattern_to_meta: dict[str, tuple[str, list[str], str, str]] = {}
    for page in old_pages:
        pat = H._normalize_pattern(str(page.get("pattern", "")))
        pid = str(page.get("id", ""))
        pids = [str(p.get("id", "")) for p in page.get("prompts", []) if isinstance(p, dict)]
        placeholder = str(page.get("placeholder", ""))
        pattern_to_meta[pat] = (pid, pids, str(page.get("label", "")), placeholder)

    text = EN_MD.read_text(encoding="utf-8")
    parsed = parse_sections(text)
    print(f"\nParsed {len(parsed)} sections:\n")

    new_pages: list[dict] = []
    preserved_count = 0
    new_count = 0

    for i, sec in enumerate(parsed, 1):
        pat = H._normalize_pattern(sec["raw_path"])
        meta = pattern_to_meta.get(pat)
        if meta:
            page_id, prompt_ids, _old_label, placeholder = meta
            id_note = f"ID preserved: {page_id}"
            preserved_count += 1
        else:
            page_id = H._to_slug(pat) or "page"
            prompt_ids = [f"{page_id}_{j}" for j in (1, 2, 3)]
            placeholder = "Ask anything about FF..."
            id_note = f"ID new: {page_id}"
            new_count += 1

        print(f"  [{i}/{len(parsed)}] {sec['title']}")
        print(f"          Path:     {sec['raw_path']}")
        print(f"          Greeting: {sec['greeting']}")
        for q in sec["questions"]:
            print(f"            - {q}")
        print(f"          {id_note}")
        print()

        prompts = []
        for j, q in enumerate(sec["questions"]):
            pid = prompt_ids[j] if j < len(prompt_ids) else f"{page_id}_{j + 1}"
            prompts.append({
                "id": pid,
                "enabled": True,
                "type": "message",
                "label": q,
                "prompt": q,
                "sort_order": j,
            })

        new_pages.append({
            "id": page_id,
            "pattern": pat,
            "label": sec["title"],
            "greeting": sec["greeting"],
            "placeholder": placeholder or "Ask anything about FF...",
            "info_text": "",
            "prompts": prompts,
        })

    storage = H(OUT_JSON, backend="file")
    # Preserve existing global_prompts; inject default only if absent
    existing_global = old_data.get("global_prompts")
    data: dict = {"pages": new_pages}
    if existing_global is not None:
        data["global_prompts"] = existing_global
    normalized, _changed = storage._normalize_data_container(data)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(normalized, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Written:  {OUT_JSON}")
    print(f"Result:   {len(normalized['pages'])} pages  (preserved {preserved_count}, new {new_count})")
    print(f"          global_prompts: {len(normalized.get('global_prompts', []))} items")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
