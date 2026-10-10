# Stage 8B — Answer generation reliability checks

This patch adds a smoke-test script only. It does not edit the working RAG routes,
generation service, vector store, or prior retrieval evaluation script.

## Run

From the project root with `.venv` active and the FastAPI server running:

```powershell
python scripts/evaluate_rag_answers.py
```

The positive AAPL case invokes Groq and may consume a small amount of provider usage.
The unknown-TSLA case should return the no-evidence response without invoking generation.

The script checks:
- retrieved evidence exists for the AAPL question;
- the answer endpoint reports `generation_status="generated"`;
- answer citation markers such as `[E1]` map to returned citation IDs;
- citation sources are a subset of retrieved evidence sources;
- the answer includes key concepts present in the illustrative risk note;
- the TSLA-filtered case returns no evidence, abstains, and returns no citations.

The report is saved to `data/rag/evaluation/latest_answer_report.json`.

These are smoke tests, not a full semantic groundedness benchmark. Matching source names
and citation IDs cannot prove every sentence is supported. Review failures before
changing production code, since wording can vary across model responses.
