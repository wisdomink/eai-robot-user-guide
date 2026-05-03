import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ── Paths ────────────────────────────────────────────────────────────────
# __file__ = …/apps/rag-api/app/core/config.py → RAG_SERVER_ROOT = apps/rag-api
RAG_SERVER_ROOT = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = RAG_SERVER_ROOT.parent.parent
_default_content_dir = PROJECT_ROOT / "apps" / "web" / "src" / "content"
CONTENT_DIR = Path(os.getenv("CONTENT_DIR", str(_default_content_dir)))
SIDEBAR_PATH = CONTENT_DIR / "sidebar.json"

# ── OpenAI ───────────────────────────────────────────────────────────────
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-5.4-mini")

# httpx: OpenAI SDK default is connect=5s — too low on slow or filtered networks (ConnectTimeout).
OPENAI_HTTP_CONNECT_TIMEOUT: float = float(os.getenv("OPENAI_HTTP_CONNECT_TIMEOUT", "30"))
OPENAI_HTTP_READ_TIMEOUT: float = float(os.getenv("OPENAI_HTTP_READ_TIMEOUT", "600"))
LOOP_PASS_MAX_CONCURRENCY: int = int(os.getenv("LOOP_PASS_MAX_CONCURRENCY", "4"))
LOOP_PASS_TIMEOUT_SECONDS: float = float(os.getenv("LOOP_PASS_TIMEOUT_SECONDS", "240"))
LOOP_PROGRESS_HEARTBEAT_SECONDS: float = float(os.getenv("LOOP_PROGRESS_HEARTBEAT_SECONDS", "20"))

# ── Vector Stores (per-product) ──────────────────────────────────────────
OPENAI_VECTOR_STORE_MASTER_ID: str = os.getenv("OPENAI_VECTOR_STORE_MASTER_ID", "")
OPENAI_VECTOR_STORE_FUTURIST_ID: str = os.getenv("OPENAI_VECTOR_STORE_FUTURIST_ID", "")
OPENAI_VECTOR_STORE_FUTURIST_ULTRA_ID: str = os.getenv("OPENAI_VECTOR_STORE_FUTURIST_ULTRA_ID", "")
OPENAI_VECTOR_STORE_AEGIS_ID: str = os.getenv("OPENAI_VECTOR_STORE_AEGIS_ID", "")
OPENAI_VECTOR_STORE_AEGIS_ULTRA_ID: str = os.getenv("OPENAI_VECTOR_STORE_AEGIS_ULTRA_ID", "")
OPENAI_VECTOR_STORE_FF91_ID: str = os.getenv("OPENAI_VECTOR_STORE_FF91_ID", "")
OPENAI_VECTOR_STORE_ROBOT_ALL_ID: str = os.getenv("OPENAI_VECTOR_STORE_ROBOT_ALL_ID", "")
OPENAI_VECTOR_STORE_PRICE_ID: str = os.getenv("OPENAI_VECTOR_STORE_PRICE_ID", "")
OPENAI_VECTOR_STORE_NEWS_ID: str = os.getenv(
    "OPENAI_VECTOR_STORE_NEWS_ID",
    os.getenv("OPENAI_VECTOR_STORE_NWES_ID", ""),
)

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
LEADS_BACKEND: str = os.getenv("LEADS_BACKEND", "file").strip().lower()
LEADS_DDB_TABLE: str = os.getenv("LEADS_DDB_TABLE", "").strip()
LEADS_FORWARD_URL: str = os.getenv("LEADS_FORWARD_URL", "").strip()
LEADS_FORWARD_TIMEOUT: float = float(os.getenv("LEADS_FORWARD_TIMEOUT", "10"))
LEADS_FORWARD_SOURCE: str = os.getenv("LEADS_FORWARD_SOURCE", "AI Chat").strip() or "AI Chat"

# ── Homepage prompts config persistence ────────────────────────────────────
HOMEPAGE_PROMPTS_BACKEND: str = os.getenv("HOMEPAGE_PROMPTS_BACKEND", "file").strip().lower()
HOMEPAGE_PROMPTS_DDB_TABLE: str = os.getenv("HOMEPAGE_PROMPTS_DDB_TABLE", "").strip()
HOMEPAGE_PROMPTS_DATA_PATH: Path = Path(
    os.getenv("HOMEPAGE_PROMPTS_DATA_PATH", str(RAG_SERVER_ROOT / "data" / "homepage_prompts.json"))
)

# ── Recommendation config persistence ─────────────────────────────────────
RECOMMENDATIONS_BACKEND: str = os.getenv("RECOMMENDATIONS_BACKEND", "file").strip().lower()
RECOMMENDATIONS_DDB_TABLE: str = os.getenv("RECOMMENDATIONS_DDB_TABLE", "").strip()
AWS_REGION_NAME: str = (
    os.getenv("AWS_DEFAULT_REGION", "").strip()
    or os.getenv("AWS_REGION", "").strip()
)

# ── Fast answers: preset FAQ + repeated-question memory ───────────────────
FAST_ANSWER_ENABLED: bool = os.getenv("FAST_ANSWER_ENABLED", "true").lower() in ("1", "true", "yes")
PRESET_FAQ_PATH: Path = Path(
    os.getenv(
        "PRESET_FAQ_PATH",
        str(PROJECT_ROOT / "input" / "FF Assist_QA_CN.md"),
    )
)
_preset_faq_paths_env = os.getenv("PRESET_FAQ_PATHS", "").strip()
PRESET_FAQ_PATHS: list[Path] = (
    [Path(p.strip()) for p in _preset_faq_paths_env.split(",") if p.strip()]
    if _preset_faq_paths_env
    else [
        PRESET_FAQ_PATH,
        PROJECT_ROOT / "input" / "FF_Assist_QA_EN.md",
    ]
)
ANSWER_MEMORY_ENABLED: bool = os.getenv("ANSWER_MEMORY_ENABLED", "true").lower() in ("1", "true", "yes")
ANSWER_MEMORY_DATA_PATH: Path = Path(
    os.getenv("ANSWER_MEMORY_DATA_PATH", str(LEADS_DIR / "answer_memory.jsonl"))
)
ANSWER_MEMORY_MAX_RECORDS: int = int(os.getenv("ANSWER_MEMORY_MAX_RECORDS", "2000"))
PRESET_FAQ_FUZZY_THRESHOLD: float = float(os.getenv("PRESET_FAQ_FUZZY_THRESHOLD", "0.82"))
ANSWER_MEMORY_FUZZY_THRESHOLD: float = float(os.getenv("ANSWER_MEMORY_FUZZY_THRESHOLD", "0.90"))

# ── Public URL (for rewriting image paths in ChatKit iframe) ─────────────
PUBLIC_BASE_URL: str = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
