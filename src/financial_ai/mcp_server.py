"""MCP server exposing bounded financial-analysis tools."""

from __future__ import annotations

from inspect import signature
from typing import Any

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.params import Query as QueryParameter
from mcp.server.fastmcp import FastMCP

from financial_ai.api.routes import analytics, explainability, ml
from financial_ai.db.session import SessionLocal

mcp = FastMCP("Financial Intelligence and Risk Platform")


def _run_tool(handler: Any, ticker: str) -> dict[str, Any]:
    """Run a route handler with explicit values for FastAPI parameters."""
    symbol = ticker.strip().upper()
    if not symbol or len(symbol) > 30:
        raise ValueError("Ticker must contain between 1 and 30 characters.")

    parameters = signature(handler).parameters
    kwargs: dict[str, Any] = {"ticker": symbol}

    # Route handlers called outside FastAPI need concrete Query defaults.
    for name, parameter in parameters.items():
        if isinstance(parameter.default, QueryParameter):
            kwargs[name] = parameter.default.default

    with SessionLocal() as db:
        kwargs["db"] = db
        try:
            result = handler(**kwargs)
            return jsonable_encoder(result)
        except HTTPException as exc:
            raise ValueError(
                f"Financial analysis failed with HTTP status {exc.status_code}."
            ) from exc


@mcp.tool()
def get_analytics_summary(ticker: str) -> dict[str, Any]:
    """Get quantitative analytics for a ticker from stored market data."""
    return _run_tool(analytics.analytics_summary, ticker)


@mcp.tool()
def get_risk_intelligence(ticker: str) -> dict[str, Any]:
    """Get risk metrics and risk interpretation for a ticker."""
    return _run_tool(explainability.risk_intelligence, ticker)


@mcp.tool()
def compare_forecasting_models(ticker: str) -> dict[str, Any]:
    """Compare available forecasting models for a ticker."""
    return _run_tool(ml.compare_forecasting_models, ticker)


if __name__ == "__main__":
    mcp.run(transport="stdio")
