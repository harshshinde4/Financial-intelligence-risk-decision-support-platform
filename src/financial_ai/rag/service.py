from pathlib import Path
from typing import Any

from financial_ai.rag.chunking import chunk_documents
from financial_ai.rag.documents import load_documents
from financial_ai.rag.embeddings import SentenceTransformerEmbedder
from financial_ai.rag.retrieval import retrieve_context
from financial_ai.rag.vector_store import ChromaVectorStore


class FinancialRAGService:
    def __init__(
        self,
        corpus_directory: str | Path = "data/rag/corpus",
        persist_directory: str | Path = "data/rag/chroma",
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ) -> None:
        self.corpus_directory = Path(corpus_directory)
        self.embedder = SentenceTransformerEmbedder(model_name)
        self.store = ChromaVectorStore(persist_directory)

    def index_corpus(self, chunk_size: int = 900, overlap: int = 150) -> dict[str, int]:
        docs = load_documents(self.corpus_directory)
        chunks = chunk_documents(docs, chunk_size, overlap)
        return {
            "documents_loaded": len(docs),
            "chunks_created": len(chunks),
            "chunks_indexed": self.store.upsert_chunks(chunks, self.embedder),
        }

    def retrieve(self, question: str, top_k: int = 5, ticker: str | None = None) -> dict[str, Any]:
        hits = retrieve_context(question, self.store, self.embedder, top_k, ticker)
        return {
            "question": question,
            "ticker_filter": ticker,
            "retrieved_count": len(hits),
            "evidence": [
                {
                    "chunk_id": h["chunk_id"],
                    "text": h["text"],
                    "source": h["metadata"].get("source"),
                    "document_id": h["metadata"].get("document_id"),
                    "ticker": h["metadata"].get("ticker") or None,
                    "published_at": h["metadata"].get("published_at") or None,
                    "similarity": h["similarity"],
                }
                for h in hits
            ],
            "answer": None,
            "answer_note": (
                "Retrieval-only baseline; generation follows after retrieval quality is inspected."
            ),
        }
