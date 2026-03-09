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
LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-5")

# ── Vector Stores (per-product) ──────────────────────────────────────────
OPENAI_VECTOR_STORE_MASTER_ULTRA_ID: str = os.getenv("OPENAI_VECTOR_STORE_MASTER_ULTRA_ID", "")
OPENAI_VECTOR_STORE_FUTURIST_ULTRA_ID: str = os.getenv("OPENAI_VECTOR_STORE_FUTURIST_ULTRA_ID", "")
OPENAI_VECTOR_STORE_AEGIS_ULTRA_ID: str = os.getenv("OPENAI_VECTOR_STORE_AEGIS_ULTRA_ID", "")
OPENAI_VECTOR_STORE_AEGIS_EDU_ID: str = os.getenv("OPENAI_VECTOR_STORE_AEGIS_EDU_ID", "")
OPENAI_VECTOR_STORE_ROBOT_ALL_ID: str = os.getenv("OPENAI_VECTOR_STORE_ROBOT_ALL_ID", "")

# ── Public URL (for rewriting image paths in ChatKit iframe) ─────────────
PUBLIC_BASE_URL: str = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
