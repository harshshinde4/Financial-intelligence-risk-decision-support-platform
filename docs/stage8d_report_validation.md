# Stage 8D — Financial brief validation and provenance

This read-only script validates a saved Stage 8C JSON brief. It makes no API or Groq calls.

## Run from the project root

```powershell
python scripts/validate_financial_brief.py AAPL
python scripts/validate_financial_brief.py RELIANCE.NS
```

Reports are written to `data/reports/AAPL_validation.json` and
`data/reports/RELIANCE.NS_validation.json`.

It checks required sections, status/HTTP metadata, summary counts, and basic RAG citation
provenance (answer markers map to citation IDs and citation sources appear in retrieved
evidence). A no-evidence response must have neither evidence nor citations.

Passing validates structure and basic provenance, not financial accuracy or semantic
support for every sentence. Review failures in the original brief before changing code.
