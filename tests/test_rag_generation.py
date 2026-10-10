"""Unit tests for grounded RAG answer generation."""

import pytest

from financial_ai.rag.generation import (
    build_user_prompt,
    format_evidence,
    generate_grounded_answer,
    normalize_citations,
)


def sample_citations():
    return [
        {
            "citation_id": "E1",
            "source": "demo_aapl_risk.md",
            "document_id": "demo_aapl_risk",
            "ticker": "AAPL",
            "published_at": "2026-10-01",
            "chunk_id": "chunk-001",
        }
    ]


def test_evidence_is_labelled_and_metadata_is_included():
    evidence = [
        {
            "text": "Review realized volatility and maximum drawdown.",
            "source": "risk.md",
            "ticker": "AAPL",
            "published_at": "2026-10-01",
        }
    ]

    formatted = format_evidence(evidence)

    assert "[E1]" in formatted
    assert "source=risk.md" in formatted
    assert "ticker=AAPL" in formatted


def test_prompt_admits_missing_evidence():
    prompt = build_user_prompt("What is the risk?", [])

    assert "[No evidence retrieved]" in prompt
    assert "say so" in prompt


def test_normalize_citations_preserves_valid_marker():
    result = normalize_citations(
        "Volatility is a risk consideration [E1].",
        sample_citations(),
    )

    assert "[E1]" in result
    assert "Sources:" not in result


def test_normalize_citations_adds_missing_source_marker():
    result = normalize_citations(
        "Volatility is a risk consideration.",
        sample_citations(),
    )

    assert "[E1]" in result
    assert "Sources: [E1]" in result


def test_normalize_citations_removes_unknown_marker():
    result = normalize_citations(
        "Risk considerations are documented [E9].",
        sample_citations(),
    )

    assert "[E9]" not in result
    assert "Sources: [E1]" in result


def test_normalize_citations_without_sources():
    result = normalize_citations(
        "There is insufficient evidence.",
        [],
    )

    assert result == "There is insufficient evidence."


def test_no_evidence_returns_abstention_without_api_call():
    result = generate_grounded_answer(
        "What are the TSLA risk considerations?",
        [],
    )

    assert result["generation_status"] == "no_evidence"
    assert result["citations"] == []
    assert "cannot answer this reliably" in result["answer"]


def test_empty_question_is_rejected():
    with pytest.raises(ValueError, match="question must not be empty"):
        generate_grounded_answer("   ", [])
