import hashlib
import re
from dataclasses import dataclass

from financial_ai.rag.documents import FinancialDocument


@dataclass(frozen=True)
class DocumentChunk:
    chunk_id: str
    document_id: str
    text: str
    source: str
    ticker: str | None
    published_at: str | None
    chunk_index: int
    metadata: dict[str, str]


def chunk_document(
    document: FinancialDocument, chunk_size: int = 900, overlap: int = 150
) -> list[DocumentChunk]:
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("Require chunk_size > overlap >= 0.")
    text = re.sub(r"\s+", " ", document.text).strip()
    chunks, start, idx = [], 0, 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        body = text[start:end].strip()
        if body:
            cid = hashlib.sha256(f"{document.document_id}:{idx}:{body}".encode()).hexdigest()[:20]
            chunks.append(
                DocumentChunk(
                    cid,
                    document.document_id,
                    body,
                    document.source,
                    document.ticker,
                    document.published_at,
                    idx,
                    {str(k): str(v) for k, v in (document.metadata or {}).items()},
                )
            )
        if end == len(text):
            break
        start, idx = end - overlap, idx + 1
    return chunks


def chunk_documents(
    documents: list[FinancialDocument], chunk_size: int = 900, overlap: int = 150
) -> list[DocumentChunk]:
    return [c for d in documents for c in chunk_document(d, chunk_size, overlap)]
