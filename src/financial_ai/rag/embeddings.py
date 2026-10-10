import hashlib
from typing import Protocol

import numpy as np


class Embedder(Protocol):
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...


class SentenceTransformerEmbedder:
    """Local sentence embedding model; first use downloads/caches the model."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return (
            self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
            .astype(float)
            .tolist()
        )

    def embed_query(self, text: str) -> list[float]:
        return (
            self.model.encode([text], normalize_embeddings=True, show_progress_bar=False)[0]
            .astype(float)
            .tolist()
        )


class HashingEmbedder:
    """Deterministic test embedder only; not semantic embeddings."""

    def __init__(self, dimensions: int = 384) -> None:
        self.dimensions = dimensions

    def _embed(self, text: str) -> list[float]:
        vec = np.zeros(self.dimensions)
        for token in text.lower().split():
            vec[int(hashlib.sha256(token.encode()).hexdigest(), 16) % self.dimensions] += 1
        norm = float(np.linalg.norm(vec))
        if norm:
            vec /= norm
        return vec.tolist()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)
