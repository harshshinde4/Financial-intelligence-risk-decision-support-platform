from pathlib import Path
from typing import Any

import chromadb

from financial_ai.rag.chunking import DocumentChunk
from financial_ai.rag.embeddings import Embedder


class ChromaVectorStore:
    def __init__(
        self,
        persist_directory: str | Path = "data/rag/chroma",
        collection_name: str = "financial_knowledge",
    ) -> None:
        self.client = chromadb.PersistentClient(path=str(persist_directory))
        self.collection = self.client.get_or_create_collection(
            name=collection_name, metadata={"hnsw:space": "cosine"}
        )

    def upsert_chunks(self, chunks: list[DocumentChunk], embedder: Embedder) -> int:
        if not chunks:
            return 0
        self.collection.upsert(
            ids=[c.chunk_id for c in chunks],
            documents=[c.text for c in chunks],
            embeddings=embedder.embed_documents([c.text for c in chunks]),
            metadatas=[
                {
                    "document_id": c.document_id,
                    "source": c.source,
                    "ticker": c.ticker or "",
                    "published_at": c.published_at or "",
                    "chunk_index": c.chunk_index,
                    **c.metadata,
                }
                for c in chunks
            ],
        )
        return len(chunks)

    def query(
        self, text: str, embedder: Embedder, top_k: int = 5, ticker: str | None = None
    ) -> list[dict[str, Any]]:
        if top_k < 1:
            raise ValueError("top_k must be >= 1")
        result = self.collection.query(
            query_embeddings=[embedder.embed_query(text)],
            n_results=top_k,
            where={"ticker": ticker} if ticker else None,
            include=["documents", "metadatas", "distances"],
        )
        hits = []
        for cid, doc, meta, dist in zip(
            result["ids"][0],
            result["documents"][0],
            result["metadatas"][0],
            result["distances"][0],
            strict=True,
        ):
            hits.append(
                {
                    "chunk_id": cid,
                    "text": doc,
                    "metadata": meta or {},
                    "distance": float(dist),
                    "similarity": 1 - float(dist),
                }
            )
        return hits
