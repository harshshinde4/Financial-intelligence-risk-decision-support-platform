from financial_ai.rag.embeddings import Embedder
from financial_ai.rag.vector_store import ChromaVectorStore


def retrieve_context(
    question: str,
    store: ChromaVectorStore,
    embedder: Embedder,
    top_k: int = 5,
    ticker: str | None = None,
    min_similarity: float | None = None,
) -> list[dict]:
    hits = store.query(question, embedder, top_k=top_k, ticker=ticker)
    return [h for h in hits if min_similarity is None or h["similarity"] >= min_similarity]
