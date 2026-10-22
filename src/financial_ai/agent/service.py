"""Bounded orchestration for the Financial Analyst Agent."""

from __future__ import annotations

import json
from collections.abc import Callable
from inspect import signature
from typing import Any

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from financial_ai.api.routes import analytics, explainability, ml, nlp
from financial_ai.api.routes.rag import _service as get_rag_service
from financial_ai.rag.generation import generate_grounded_answer

# Fixed allowlist: the agent cannot call arbitrary functions or code.
TOOL_HANDLERS: dict[str, Callable[..., Any]] = {
    "analytics_summary": analytics.analytics_summary,
    "risk_intelligence": explainability.risk_intelligence,
    "forecast": ml.forecast_next_day,
    "model_comparison": ml.compare_forecasting_models,
    "explain_prediction": explainability.explain_prediction,
    "news_analysis": nlp.analyze_news,
}

FORECAST_TERMS = ("forecast", "predict", "prediction", "future price", "next day")
MODEL_TERMS = ("compare model", "model comparison", "best model", "model performance")
EXPLANATION_TERMS = ("explain", "why", "feature importance", "shap", "reason")
NEWS_TERMS = ("news", "sentiment", "headline", "event")
RISK_TERMS = ("risk", "volatility", "drawdown", "exposure")


def select_tools(question: str) -> list[str]:
    """Select a bounded set of tools using transparent keyword rules."""
    normalized = question.casefold()
    selected = ["analytics_summary", "risk_intelligence"]

    if any(term in normalized for term in FORECAST_TERMS):
        selected.append("forecast")

    if any(term in normalized for term in MODEL_TERMS):
        selected.append("model_comparison")

    if any(term in normalized for term in EXPLANATION_TERMS):
        selected.append("explain_prediction")

    if any(term in normalized for term in NEWS_TERMS):
        selected.append("news_analysis")

    return selected


def _invoke_handler(
    handler: Callable[..., Any],
    ticker: str,
    db: Session,
    articles: list[nlp.NewsArticle] | None = None,
) -> Any:
    """Invoke an allowlisted route handler with its supported inputs."""
    parameters = signature(handler).parameters
    kwargs: dict[str, Any] = {"ticker": ticker}

    if "db" in parameters:
        kwargs["db"] = db

    if "articles" in parameters:
        if not articles:
            raise ValueError("News analysis requires at least one article.")
        kwargs["articles"] = articles

    return jsonable_encoder(handler(**kwargs))


def analyze_financial_question(
    question: str,
    ticker: str,
    db: Session,
    articles: list[nlp.NewsArticle] | None = None,
) -> dict[str, Any]:
    """Execute selected financial tools and generate an evidence-grounded answer."""
    selected_tools = select_tools(question)
    tool_results: dict[str, Any] = {}
    tool_errors: dict[str, str] = {}

    for tool_name in selected_tools:
        if tool_name == "news_analysis" and not articles:
            tool_errors[tool_name] = (
                "News analysis skipped: provide at least one article "
                "in the request's articles field."
            )
        continue
        try:
            tool_results[tool_name] = _invoke_handler(
                TOOL_HANDLERS[tool_name],
                ticker,
                db,
                articles=articles,
            )
        except HTTPException as exc:
            tool_errors[tool_name] = f"Tool returned HTTP {exc.status_code}."
        except Exception:
            # Keep internal exception details in logs, not public responses.
            import structlog

            structlog.get_logger(__name__).exception(
                "agent_tool_execution_failed",
                tool=tool_name,
                ticker=ticker,
            )
            tool_errors[tool_name] = "Tool execution failed."

    evidence: list[dict[str, Any]] = []

    # Include structured tool outputs as explicitly identified evidence.
    for tool_name, result in tool_results.items():
        evidence.append(
            {
                "text": json.dumps(result, ensure_ascii=False, default=str),
                "source": f"platform_tool:{tool_name}",
                "document_id": f"{ticker}:{tool_name}",
                "ticker": ticker,
            }
        )

    # Add retrieved document evidence, preserving its original metadata.
    try:
        retrieved = get_rag_service().retrieve(
            question=question,
            top_k=3,
            ticker=ticker,
        )
        for item in retrieved.get("evidence", []):
            evidence.append(item)
    except Exception:
        import structlog

        structlog.get_logger(__name__).exception(
            "agent_rag_retrieval_failed",
            ticker=ticker,
        )
        tool_errors["rag_retrieval"] = "Evidence retrieval failed."

    try:
        answer = generate_grounded_answer(question, evidence)
    except Exception as exc:
        import structlog

        structlog.get_logger(__name__).exception(
            "agent_answer_generation_failed",
            ticker=ticker,
        )
        raise HTTPException(
            status_code=503,
            detail="The analyst answer service is temporarily unavailable.",
        ) from exc

    return {
        "ticker": ticker,
        "question": question,
        "selected_tools": selected_tools,
        "tool_results": tool_results,
        "tool_errors": tool_errors,
        "answer": answer,
    }
