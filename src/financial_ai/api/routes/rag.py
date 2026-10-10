from functools import lru_cache
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from financial_ai.rag.generation import generate_grounded_answer
from financial_ai.rag.service import FinancialRAGService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/rag", tags=["Financial RAG"])


class IndexRequest(BaseModel):
    chunk_size: int = Field(900, ge=200, le=3000)
    overlap: int = Field(150, ge=0, le=1000)


class RetrieveRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    ticker: str | None = Field(None, max_length=30)
    top_k: int = Field(5, ge=1, le=20)


class AnswerRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    ticker: str | None = Field(None, max_length=30)
    top_k: int = Field(3, ge=1, le=10)


@lru_cache(maxsize=1)
def _service() -> FinancialRAGService:
    return FinancialRAGService()


@router.post("/index")
def index_corpus(request: IndexRequest) -> dict[str, int]:
    try:
        return _service().index_corpus(
            request.chunk_size,
            request.overlap,
        )
    except Exception as exc:
        logger.exception(
            "rag_indexing_failed",
            error_type=type(exc).__name__,
        )
        raise HTTPException(
            status_code=500,
            detail="Indexing failed. Check the application logs.",
        ) from exc


@router.post("/retrieve")
def retrieve(request: RetrieveRequest) -> dict[str, Any]:
    try:
        return _service().retrieve(
            request.question,
            request.top_k,
            request.ticker,
        )
    except Exception as exc:
        logger.exception(
            "rag_retrieval_failed",
            error_type=type(exc).__name__,
        )
        raise HTTPException(
            status_code=500,
            detail="Retrieval failed. Check the application logs.",
        ) from exc


@router.post("/answer")
def answer_with_rag(request: AnswerRequest) -> dict[str, Any]:
    # Step 1: Retrieve evidence using our existing local RAG pipeline.
    try:
        retrieved = _service().retrieve(
            request.question,
            request.top_k,
            request.ticker,
        )
    except Exception as exc:
        logger.exception(
            "rag_evidence_retrieval_failed",
            error_type=type(exc).__name__,
        )
        raise HTTPException(
            status_code=500,
            detail="Evidence retrieval failed.",
        ) from exc

    # Step 2: Extract the evidence returned by the existing service.
    evidence = retrieved.get("evidence", [])

    # Step 3: Generate a grounded answer using Groq.
    try:
        generated = generate_grounded_answer(
            request.question,
            evidence,
        )
    except ValueError as exc:
        logger.exception(
            "rag_generation_failed",
            error_type=type(exc).__name__,
        )
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        logger.exception(
            "rag_generation_failed",
            error_type=type(exc).__name__,
        )
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        # Do not expose API keys or raw provider errors to the client.
        logger.exception(
            "rag_generation_failed",
            error_type=type(exc).__name__,
        )
        try:
            from openai import APIError

            is_provider_error = isinstance(exc, APIError)
        except ImportError:
            is_provider_error = False

        if is_provider_error:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Groq generation is temporarily unavailable or "
                    "the request was rejected. Check the provider "
                    "dashboard and application logs."
                ),
            ) from exc

        raise HTTPException(
            status_code=502,
            detail="Answer generation failed. Check the application logs.",
        ) from exc

    # Step 4: Return the answer and the evidence used to generate it.
    return {
        "question": request.question,
        "ticker_filter": request.ticker,
        "retrieved_count": len(evidence),
        "evidence": evidence,
        **generated,
    }
