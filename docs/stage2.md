# Stage 2 — Data Layer

## Install

```bash
pip install -e ".[dev]"
```

## Configure

```bash
cp .env.example .env
```

## Start PostgreSQL

```bash
docker compose up -d postgres
```

## Run migrations

```bash
alembic upgrade head
```

## Generate deterministic local datasets

```bash
python scripts/generate_sample_data.py
```

This creates sample datasets for:

- AAPL
- MSFT
- RELIANCE.NS
- TCS.NS
- HDFCBANK.NS
- RELIANCE.BO

## Register demo companies

```bash
python scripts/register_demo_companies.py
```

## Fetch live/research historical data

Example:

```bash
curl -X POST \
  "http://localhost:8000/api/v1/market/ingest/AAPL?start=2025-01-01&end=2026-01-01"
```

For India:

```bash
curl -X POST \
  "http://localhost:8000/api/v1/market/ingest/RELIANCE.NS?start=2025-01-01&end=2026-01-01"
```

BSE:

```bash
curl -X POST \
  "http://localhost:8000/api/v1/market/ingest/RELIANCE.BO?start=2025-01-01&end=2026-01-01"
```

Retrieve stored prices:

```bash
curl "http://localhost:8000/api/v1/market/AAPL?limit=20"
```

## Tests

```bash
pytest
```

## Design principle

Live providers are adapters. They are not allowed to leak into model code.

That means future components can consume a canonical internal schema regardless
of whether the source is Yahoo Finance, a licensed market-data vendor, SEC,
NSE data, or a local dataset.
