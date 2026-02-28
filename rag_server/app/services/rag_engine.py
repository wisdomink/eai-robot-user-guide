"""
RAG engine: ChromaDB vector store + OpenAI embeddings.

Uses ChromaDB's native OpenAI embedding function — no LlamaIndex needed.
LLM inference is handled by the OpenAI Agents SDK via chatkit_handler.py;
this module is responsible only for indexing and retrieval.
"""

from __future__ import annotations

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

from app.core.config import (
    EMBEDDING_MODEL,
    OPENAI_API_KEY,
    SIMILARITY_TOP_K,
    VECTOR_STORAGE_PATH,
)
from app.services.loader import load_and_split_documents

COLLECTION_NAME = "ff_robot_docs"


class RAGEngine:
    def __init__(self) -> None:
        self._collection: chromadb.Collection | None = None

    def _get_embedding_fn(self) -> OpenAIEmbeddingFunction:
        return OpenAIEmbeddingFunction(
            api_key=OPENAI_API_KEY,
            model_name=EMBEDDING_MODEL,
        )

    # ── lifecycle ─────────────────────────────────────────────────────

    def initialize(self) -> None:
        """Connect to ChromaDB and build or reuse the vector index."""
        VECTOR_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(VECTOR_STORAGE_PATH))
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self._get_embedding_fn(),
        )

        if collection.count() > 0:
            print(f"[rag] reusing existing index ({collection.count()} vectors)")
            self._collection = collection
        else:
            self._collection = collection
            self._build_fresh()

    def reindex(self) -> None:
        """Force a full rebuild of the vector index."""
        VECTOR_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(VECTOR_STORAGE_PATH))

        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass

        self._collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self._get_embedding_fn(),
        )
        self._build_fresh()

    def _build_fresh(self) -> None:
        chunks = load_and_split_documents()
        if not chunks:
            print("[rag] no chunks to index")
            return

        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            self._collection.add(
                ids=[c.id for c in batch],
                documents=[c.text for c in batch],
                metadatas=[c.metadata for c in batch],
            )

        print(f"[rag] built new index with {len(chunks)} chunks")

    # ── retrieval ─────────────────────────────────────────────────────

    def retrieve(self, query: str) -> tuple[str, list[dict]]:
        """Retrieve top-k chunks and return (formatted context, deduplicated sources).

        Each source carries a ``url_with_anchor`` field (e.g. ``/charging-procedure#steps``)
        that deep-links to the exact heading in the frontend H5 page.
        """
        results = self._collection.query(
            query_texts=[query],
            n_results=SIMILARITY_TOP_K,
        )

        context_parts: list[str] = []
        sources: list[dict] = []
        seen: set[str] = set()

        ids = results["ids"][0]
        docs = results["documents"][0]
        metas = results["metadatas"][0]

        for idx, (doc_id, text, meta) in enumerate(zip(ids, docs, metas), 1):
            label = meta.get("header_path") or meta.get("page_title", "")
            context_parts.append(
                f"[{idx}] (来源: {meta.get('page_title', '')} | {label})\n"
                f"{text}"
            )

            anchor = meta.get("heading_anchor", "")
            base_url = meta.get("url_path", "")
            url_with_anchor = f"{base_url}#{anchor}" if anchor else base_url

            if url_with_anchor in seen:
                continue
            seen.add(url_with_anchor)

            sources.append(
                {
                    "title": meta.get("page_title", ""),
                    "section": meta.get("section_title", ""),
                    "section_id": meta.get("section_id", ""),
                    "header_path": meta.get("header_path", ""),
                    "heading_anchor": anchor,
                    "url_path": base_url,
                    "url_with_anchor": url_with_anchor,
                    "file_path": meta.get("file_path", ""),
                }
            )

        context = "\n\n---\n\n".join(context_parts)
        return context, sources


rag_engine = RAGEngine()
