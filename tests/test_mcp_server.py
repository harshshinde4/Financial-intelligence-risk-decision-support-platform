import asyncio

import pytest
from fastapi import HTTPException

from financial_ai import mcp_server


def test_expected_tools_are_registered():
    tools = asyncio.run(mcp_server.mcp.list_tools())

    assert {tool.name for tool in tools} == {
        "get_analytics_summary",
        "get_risk_intelligence",
        "compare_forecasting_models",
    }

    for tool in tools:
        assert "ticker" in tool.inputSchema["required"]
        assert tool.description


class FakeSession:
    def __init__(self):
        self.entered = False
        self.closed = False

    def __enter__(self):
        self.entered = True
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.closed = True
        return False


def test_run_tool_returns_result_and_closes_session(monkeypatch):
    session = FakeSession()
    monkeypatch.setattr(mcp_server, "SessionLocal", lambda: session)

    def handler(*, ticker, db):
        assert db is session
        return {"ticker": ticker, "count": 12}

    result = mcp_server._run_tool(handler, " aapl ")

    assert result == {"ticker": "AAPL", "count": 12}
    assert session.entered
    assert session.closed


def test_run_tool_closes_session_when_handler_fails(monkeypatch):
    session = FakeSession()
    monkeypatch.setattr(mcp_server, "SessionLocal", lambda: session)

    def handler(*, ticker, db):
        raise RuntimeError("simulated failure")

    with pytest.raises(RuntimeError, match="simulated failure"):
        mcp_server._run_tool(handler, "AAPL")

    assert session.closed


def test_run_tool_sanitizes_http_errors(monkeypatch):
    session = FakeSession()
    monkeypatch.setattr(mcp_server, "SessionLocal", lambda: session)

    def handler(*, ticker, db):
        raise HTTPException(status_code=404, detail="Ticker not found")

    with pytest.raises(ValueError, match="HTTP status 404"):
        mcp_server._run_tool(handler, "AAPL")

    assert session.closed


@pytest.mark.parametrize("ticker", ["", " ", "A" * 31])
def test_run_tool_rejects_invalid_ticker(ticker):
    with pytest.raises(ValueError, match="Ticker"):
        mcp_server._run_tool(lambda **kwargs: {}, ticker)
