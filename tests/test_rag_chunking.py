import pytest

from financial_ai.rag.chunking import chunk_document
from financial_ai.rag.documents import FinancialDocument


def test_chunking_overlap_and_stable_ids():
    doc = FinancialDocument("doc1", "abcdefghijklmnopqrstuvwxyz", "demo.md", ticker="AAPL")
    chunks = chunk_document(doc, 10, 2)
    assert len(chunks) == 3
    assert chunks[0].text[-2:] == chunks[1].text[:2]
    assert chunks[0].chunk_id == chunk_document(doc, 10, 2)[0].chunk_id


def test_invalid_chunk_parameters():
    doc = FinancialDocument("doc1", "text", "demo.md")
    with pytest.raises(ValueError):
        chunk_document(doc, 10, 10)
