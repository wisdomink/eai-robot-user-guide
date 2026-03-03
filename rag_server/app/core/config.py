import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ── Paths ────────────────────────────────────────────────────────────────
RAG_SERVER_ROOT = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = RAG_SERVER_ROOT.parent
CONTENT_DIR = PROJECT_ROOT / "src" / "content"
SIDEBAR_PATH = CONTENT_DIR / "sidebar.json"
PAGES_DIR = CONTENT_DIR / "pages"
VECTOR_STORAGE_PATH = RAG_SERVER_ROOT / "vector_storage"

# ── OpenAI ───────────────────────────────────────────────────────────────
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_ASSISTANT_ID: str = os.getenv("OPENAI_ASSISTANT_ID", "")
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# ── RAG ──────────────────────────────────────────────────────────────────
SIMILARITY_TOP_K: int = int(os.getenv("SIMILARITY_TOP_K", "5"))
