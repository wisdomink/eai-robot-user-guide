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

# ── Provider ─────────────────────────────────────────────────────────────
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")

# ── RAG ──────────────────────────────────────────────────────────────────
SIMILARITY_TOP_K: int = int(os.getenv("SIMILARITY_TOP_K", "5"))


def get_llm():
    """Return the configured LLM instance."""
    if LLM_PROVIDER == "gemini":
        from llama_index.llms.gemini import Gemini

        return Gemini(
            model=os.getenv("GEMINI_LLM_MODEL", "models/gemini-2.0-flash"),
            api_key=os.getenv("GOOGLE_API_KEY"),
        )

    from llama_index.llms.openai import OpenAI

    return OpenAI(
        model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )


def get_embed_model():
    """Return the configured embedding model instance."""
    if LLM_PROVIDER == "gemini":
        from llama_index.embeddings.gemini import GeminiEmbedding

        return GeminiEmbedding(
            model_name=os.getenv(
                "GEMINI_EMBEDDING_MODEL", "models/text-embedding-004"
            ),
            api_key=os.getenv("GOOGLE_API_KEY"),
        )

    from llama_index.embeddings.openai import OpenAIEmbedding

    return OpenAIEmbedding(
        model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )
