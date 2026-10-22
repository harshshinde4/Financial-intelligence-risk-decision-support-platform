# Stage 8.2 — MCP Integration

## Overview

The Financial Intelligence and Risk Decision Support Platform exposes selected financial-analysis capabilities through the Model Context Protocol (MCP).

The MCP server is implemented in `src/financial_ai/mcp_server.py` using the MCP Python SDK and FastMCP. It reuses existing analytics, risk, and forecasting handlers rather than duplicating their business logic.

## Available tools

| Tool | Purpose |
|---|---|
| `get_analytics_summary` | Returns quantitative analytics and technical indicators for a ticker. |
| `get_risk_intelligence` | Returns risk metrics, risk drivers, and forecast information. |
| `compare_forecasting_models` | Compares supported forecasting models using evaluation metrics. |

Each tool accepts a ticker symbol, such as `AAPL`.

## Prerequisites

- The project virtual environment and dependencies are installed.
- PostgreSQL is running and accessible using the configured database URL.
- Database migrations have been applied.
- The requested ticker has sufficient company and market-price data.

## Run the MCP server

From the project root, activate the virtual environment and run:

```powershell
python -m financial_ai.mcp_server
```

The server uses stdio transport. When connecting through an MCP-compatible client, the client should launch this command using the project's virtual-environment Python executable.

Do not run a separate interactive server in the same terminal as a client-managed stdio connection.

## Verify tool discovery and execution

Run the project's MCP smoke-test script:

```powershell
python .\scripts\test_mcp_live.py
```

The script initializes an MCP session, lists the available tools, and calls the analytics, risk, and model-comparison tools.

A successful tool call returns `Is error: False`. The returned content should be inspected for valid financial-analysis output.

## Architecture

1. The MCP client starts the server over stdio.
2. FastMCP exposes the registered tools.
3. Each tool validates the ticker and opens a short-lived database session.
4. The tool calls the corresponding existing application handler.
5. Results are converted into JSON-compatible content and returned to the MCP client.

## Security and operational considerations

- Keep API keys and database credentials in environment variables; never commit `.env`.
- Expose only explicitly registered, allowlisted tools.
- Do not return raw internal exceptions or credentials to clients.
- Treat tool results as analytical outputs, not guaranteed market predictions.
- Validate data freshness, model performance, and risk-score calibration before production use.
- Configure the external MCP client to use the correct Python interpreter and working directory.
