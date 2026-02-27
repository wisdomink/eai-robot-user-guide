"""
RAG engine: ChromaDB vector index + citation-aware streaming query.
"""

from __future__ import annotations

import asyncio
from typing import AsyncGenerator

import chromadb
from llama_index.core import Settings, StorageContext, VectorStoreIndex
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.vector_stores.chroma import ChromaVectorStore

from app.core.config import (
    SIMILARITY_TOP_K,
    VECTOR_STORAGE_PATH,
    get_embed_model,
    get_llm,
)
from app.services.loader import load_and_split_documents

COLLECTION_NAME = "ff_robot_docs"

SYSTEM_PROMPT = """\
你是一名专业的技术支持工程师，专门负责 FF Master Ultra Edition 机器人的用户支持。

规则：
1. 仅根据下方【参考文档】的内容回答用户问题，不要使用任何外部知识。
2. 在回答中使用 [1], [2] 等标注你引用了哪段参考文档。
3. 如果参考文档中未提及相关信息，请直接回答："抱歉，说明书中未找到相关信息。"
4. 回答末尾必须附带【参考来源】列表，格式：
   【参考来源】
   [1] 标题 - 路径
   [2] 标题 - 路径
5. 保持回答简洁、专业、结构化，使用中文回答。
6. 如果参考文档中包含图片链接，请在回答中保留图片的 Markdown 语法。
"""


class RAGEngine:
    def __init__(self) -> None:
        self.index: VectorStoreIndex | None = None
        self.llm = None
        self.embed_model = None

    # ── lifecycle ─────────────────────────────────────────────────────

    def initialize(self) -> None:
        """Load models, connect to ChromaDB, build or reuse the index."""
        self.llm = get_llm()
        self.embed_model = get_embed_model()
        Settings.llm = self.llm
        Settings.embed_model = self.embed_model

        VECTOR_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
        chroma_client = chromadb.PersistentClient(path=str(VECTOR_STORAGE_PATH))
        collection = chroma_client.get_or_create_collection(COLLECTION_NAME)
        vector_store = ChromaVectorStore(chroma_collection=collection)

        if collection.count() > 0:
            print(
                f"[rag] reusing existing index ({collection.count()} vectors)"
            )
            self.index = VectorStoreIndex.from_vector_store(vector_store)
        else:
            self._build_fresh(vector_store)

    def reindex(self) -> None:
        """Force a full rebuild of the vector index."""
        VECTOR_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
        chroma_client = chromadb.PersistentClient(path=str(VECTOR_STORAGE_PATH))

        try:
            chroma_client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass

        collection = chroma_client.get_or_create_collection(COLLECTION_NAME)
        vector_store = ChromaVectorStore(chroma_collection=collection)
        self._build_fresh(vector_store)

    def _build_fresh(self, vector_store: ChromaVectorStore) -> None:
        documents = load_and_split_documents()
        storage_ctx = StorageContext.from_defaults(vector_store=vector_store)
        self.index = VectorStoreIndex.from_documents(
            documents, storage_context=storage_ctx
        )
        print(f"[rag] built new index with {len(documents)} chunks")

    # ── query helpers ─────────────────────────────────────────────────

    def _retrieve_and_format(
        self, query: str
    ) -> tuple[str, list[dict]]:
        """Retrieve top-k nodes and return (formatted context, deduplicated sources)."""
        retriever = self.index.as_retriever(similarity_top_k=SIMILARITY_TOP_K)
        nodes = retriever.retrieve(query)

        context_parts: list[str] = []
        sources: list[dict] = []
        seen: set[tuple[str, str]] = set()

        for idx, node_with_score in enumerate(nodes, 1):
            meta = node_with_score.metadata
            label = meta.get("header_path") or meta.get("page_title", "")
            context_parts.append(
                f"[{idx}] (来源: {meta.get('page_title', '')} | {label})\n"
                f"{node_with_score.text}"
            )

            key = (meta.get("page_title", ""), meta.get("url_path", ""))
            if key not in seen:
                seen.add(key)
                sources.append(
                    {
                        "title": meta.get("page_title", ""),
                        "section": meta.get("section_title", ""),
                        "header_path": meta.get("header_path", ""),
                        "url_path": meta.get("url_path", ""),
                        "file_path": meta.get("file_path", ""),
                    }
                )

        context = "\n\n---\n\n".join(context_parts)
        return context, sources

    # ── streaming query ───────────────────────────────────────────────

    async def query_stream(
        self, query: str
    ) -> AsyncGenerator[dict, None]:
        """
        Yield SSE-friendly dicts:
          {"type": "token",   "content": "..."}
          {"type": "sources", "sources": [...]}
          {"type": "done"}
        """
        context, sources = await asyncio.to_thread(
            self._retrieve_and_format, query
        )

        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=SYSTEM_PROMPT),
            ChatMessage(
                role=MessageRole.USER,
                content=f"【参考文档】\n{context}\n\n用户问题：{query}",
            ),
        ]

        response_gen = await self.llm.astream_chat(messages)
        async for chunk in response_gen:
            if chunk.delta:
                yield {"type": "token", "content": chunk.delta}

        yield {"type": "sources", "sources": sources}
        yield {"type": "done"}

    # ── non-streaming query ───────────────────────────────────────────

    async def query(self, query: str) -> dict:
        context, sources = await asyncio.to_thread(
            self._retrieve_and_format, query
        )

        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=SYSTEM_PROMPT),
            ChatMessage(
                role=MessageRole.USER,
                content=f"【参考文档】\n{context}\n\n用户问题：{query}",
            ),
        ]

        response = await self.llm.achat(messages)
        return {
            "answer": response.message.content,
            "sources": sources,
        }


rag_engine = RAGEngine()
