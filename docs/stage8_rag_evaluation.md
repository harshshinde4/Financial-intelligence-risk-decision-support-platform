# Stage 8A — RAG retrieval evaluation

## Purpose
This additive evaluation harness calls only `POST /api/v1/rag/retrieve`. It does not
call Groq and does not change the existing RAG service, route, vector database, or
generation code.

## Files
- `scripts/evaluate_rag.py`: calls the running local API and checks retrieval outcomes.
- `data/rag/evaluation/questions.json`: labelled starter evaluation dataset.
- `data/rag/evaluation/latest_report.json`: generated report after a run.

## Run on Windows PowerShell
1. Activate the project's existing virtual environment.
2. Start the API in a separate terminal from the project root:
   `python -m uvicorn financial_ai.api.main:app --reload`
3. In another terminal, from the project root, run:
   `python scripts/evaluate_rag.py`

No new Python package is required; the script uses Python's standard library.

## What is measured
A normal retrieval case passes when evidence is returned and includes its expected
source/ticker where specified. A negative case passes only when it returns no evidence.
The pass rate is a small regression check, not a statistically robust quality estimate.

The TSLA negative case assumes no TSLA-tagged document exists in the current corpus.
With the current two demo documents and correctly parsed sidecar metadata, AAPL should
retrieve `demo_aapl_risk.md`, the methodology query should retrieve
`demo_market_risk.md`, and the TSLA-filtered query should return no evidence.

If a case fails, inspect the reported source/ticker and compare with the API response
before changing production code.

## After this passes
Expand labelled questions, then separately test citation IDs against the evidence passed
to generation. Keep generation checks separate so retrieval and provider failures can
be diagnosed independently.
