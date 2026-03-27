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
LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-5.4-mini")

# ── Vector Stores (per-product) ──────────────────────────────────────────
OPENAI_VECTOR_STORE_MASTER_ULTRA_ID: str = os.getenv("OPENAI_VECTOR_STORE_MASTER_ULTRA_ID", "")
OPENAI_VECTOR_STORE_FUTURIST_ULTRA_ID: str = os.getenv("OPENAI_VECTOR_STORE_FUTURIST_ULTRA_ID", "")
OPENAI_VECTOR_STORE_AEGIS_ULTRA_ID: str = os.getenv("OPENAI_VECTOR_STORE_AEGIS_ULTRA_ID", "")
OPENAI_VECTOR_STORE_AEGIS_EDU_ID: str = os.getenv("OPENAI_VECTOR_STORE_AEGIS_EDU_ID", "")
OPENAI_VECTOR_STORE_FF91_ID: str = os.getenv("OPENAI_VECTOR_STORE_FF91_ID", "")
OPENAI_VECTOR_STORE_ROBOT_ALL_ID: str = os.getenv("OPENAI_VECTOR_STORE_ROBOT_ALL_ID", "")

# ── Logging ───────────────────────────────────────────────────────────────
LOG_DIR: Path = Path(os.getenv("LOG_DIR", str(RAG_SERVER_ROOT / "logs")))
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_MAX_BYTES: int = int(os.getenv("LOG_MAX_BYTES", str(10 * 1024 * 1024)))  # 10 MB
LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))

# ── Alert (smart email notifications for errors) ─────────────────────────
ALERT_ENABLED: bool = os.getenv("ALERT_ENABLED", "false").lower() in ("1", "true", "yes")
ALERT_SMTP_HOST: str = os.getenv("ALERT_SMTP_HOST", "")
ALERT_SMTP_PORT: int = int(os.getenv("ALERT_SMTP_PORT", "587"))
ALERT_SMTP_USE_TLS: bool = os.getenv("ALERT_SMTP_USE_TLS", "true").lower() in ("1", "true", "yes")
ALERT_SMTP_USER: str = os.getenv("ALERT_SMTP_USER", "")
ALERT_SMTP_PASSWORD: str = os.getenv("ALERT_SMTP_PASSWORD", "")
ALERT_FROM_EMAIL: str = os.getenv("ALERT_FROM_EMAIL", "")
ALERT_TO_EMAILS: list[str] = [
    e.strip() for e in os.getenv("ALERT_TO_EMAILS", "").split(",") if e.strip()
]
ALERT_COOLDOWN_SECONDS: int = int(os.getenv("ALERT_COOLDOWN_SECONDS", "300"))
ALERT_CONTEXT_LINES: int = int(os.getenv("ALERT_CONTEXT_LINES", "50"))
ALERT_LEVEL: str = os.getenv("ALERT_LEVEL", "ERROR").upper()
ALERT_APP_NAME: str = os.getenv("ALERT_APP_NAME", "EAI Robot")
ALERT_DIGEST_INTERVAL: int = int(os.getenv("ALERT_DIGEST_INTERVAL", "3600"))  # 1 hour

# ── Leads (contact form submissions) ─────────────────────────────────────
LEADS_DIR: Path = Path(os.getenv("LEADS_DIR", str(RAG_SERVER_ROOT / "data")))

# ── Public URL (for rewriting image paths in ChatKit iframe) ─────────────
PUBLIC_BASE_URL: str = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
