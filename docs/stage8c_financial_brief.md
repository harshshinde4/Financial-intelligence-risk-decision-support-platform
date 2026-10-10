# Stage 8C — Deterministic Financial Intelligence Brief

## Goal

Combine existing analytics, ML, explainability, risk, and RAG endpoints into one
repeatable report. This first version is deliberately deterministic: it stores each
endpoint's raw JSON output separately rather than asking an LLM to merge numbers or
make unsupported conclusions.

## Files

- `scripts/build_financial_brief.py`: calls the six existing API endpoints and creates
  a JSON report.
- Output: `data/reports/<TICKER>_financial_brief.json`.

## Run

From the project root with `.venv` active and FastAPI running:

```powershell
python scripts/build_financial_brief.py AAPL
```

For an Indian ticker already supported by the market-data pipeline:

```powershell
python scripts/build_financial_brief.py RELIANCE.NS
```

Optional RAG evidence count:

```powershell
python scripts/build_financial_brief.py AAPL --top-k 5
```

The script uses Python's standard library only. It does not change application code
and it does not call the Groq API except indirectly through the existing `/rag/answer`
endpoint when evidence is found. That endpoint may use a generation request.

## Important endpoint assumptions

This script uses the project's previously established routes:
- `GET /api/v1/analytics/{ticker}/summary`
- `GET /api/v1/ml/{ticker}/compare`
- `GET /api/v1/ml/{ticker}/forecast`
- `GET /api/v1/intelligence/{ticker}/explain`
- `GET /api/v1/intelligence/{ticker}/risk`
- `POST /api/v1/rag/answer`

Each section records success or error independently. If a route differs in your current
code, the report will identify the failed section and its HTTP response rather than
silently discarding the failure.

## Interpretation

- This is a tool-orchestration baseline, not yet an autonomous agent.
- Raw endpoint outputs remain separate so provenance is preserved.
- A successful HTTP response does not certify model quality or factual correctness.
- Some endpoints may return errors when data is unavailable for a ticker.
- RAG generation can consume provider usage; no-evidence responses should abstain.

## Next increment

Once the script runs successfully, add a validated executive summary schema, then
test that every summarized metric is traceable to a named endpoint field. Only after
that should an LLM be permitted to draft prose from the verified report.
