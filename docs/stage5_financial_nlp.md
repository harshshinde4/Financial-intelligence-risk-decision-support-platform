# Stage 5 — Financial NLP & Event Intelligence

Adds a deterministic API layer for financial text intelligence:

- FinBERT sentiment analysis with a deterministic fallback.
- Rule-based financial event classification and severity.
- Ticker/entity extraction for the project's supported instruments.
- Aggregate sentiment and event counts by ticker.
- API endpoint accepting normalized news articles, keeping the ingestion contract provider-neutral.

## API

`POST /api/v1/nlp/{ticker}/analyze?use_finbert=true`

The request body is a JSON array of `NewsArticle` objects.

For reproducible tests, set `use_finbert=false`. With `true`, the first request downloads/caches `ProsusAI/finbert` through Hugging Face and then reuses the model in-process.

## Design

The NLP layer deliberately does not make investment decisions. It produces structured signals that later stages can combine with quantitative analytics, ML forecasts, explainability, retrieval and agentic investigation.
