import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ── Paths ────────────────────────────────────────────────────────────────
RAG_SERVER_ROOT = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = RAG_SERVER_ROOT.parent
CONTENT_DIR = PROJECT_ROOT / "src" / "content"
SIDEBAR_PATH = CONTENT_DIR / "sidebar.json"

# ── OpenAI ───────────────────────────────────────────────────────────────
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_VECTOR_STORE_ID: str = os.getenv("OPENAI_VECTOR_STORE_ID", "")
LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-5")

# ── Public URL (for rewriting image paths in ChatKit iframe) ─────────────
PUBLIC_BASE_URL: str = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
