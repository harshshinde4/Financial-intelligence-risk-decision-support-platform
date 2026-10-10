# Stage 6 — Explainability & Risk Intelligence

This stage adds two production-oriented capabilities:

1. **SHAP model explainability** for the XGBoost next-day-return forecast.
2. **Deterministic risk intelligence** that combines volatility, drawdown, VaR and the ML forecast into an auditable risk level and driver list.

## Why SHAP belongs here

The ML model can tell us *what* it predicts. SHAP helps answer *why the model made that prediction* by decomposing the prediction into feature contributions relative to the model baseline.

The API exposes the largest absolute contributors so a future analyst agent can cite structured evidence instead of inventing explanations.

## Why risk scoring is deterministic

Risk classification is deliberately not delegated to an LLM. Thresholds are explicit and testable. Later, an LLM/RAG layer can explain the result using evidence, but it should not silently change the underlying risk calculation.

## Endpoints

`GET /api/v1/intelligence/{ticker}/explain?top_n=8`

Returns the latest XGBoost prediction and its largest SHAP drivers.

`GET /api/v1/intelligence/{ticker}/risk`

Returns the XGBoost forecast plus deterministic risk level and risk drivers.

## RAG design decision

RAG is intentionally **not** introduced in Stage 6. There is no knowledge corpus to retrieve yet. In the RAG stage, the pipeline will be built explicitly:

`documents → parsing → chunking → metadata → embeddings → vector store → retrieval → optional reranking → grounded context → generation → citations`

The first implementation will use a small local financial-document corpus so each step is visible and testable before any external knowledge/API integration is added.
