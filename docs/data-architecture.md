# Stage 2 — Financial Data Architecture

## Market coverage

The platform supports:

- US equities, e.g. `AAPL`, `MSFT`
- NSE equities, e.g. `RELIANCE.NS`, `TCS.NS`
- BSE equities, e.g. `RELIANCE.BO`

The application does not depend directly on a market-data vendor. It depends on
`MarketDataProvider`.

## Provider strategy

### Development / research

`YFinanceProvider` provides historical OHLCV data for development and experiments.

### Reproducibility

`CsvMarketDataProvider` allows tests and offline runs to use deterministic datasets.

### Production

A licensed provider can later implement the same `MarketDataProvider` interface.
This is important for commercial deployment because exchange data licensing and
redistribution rules are provider-specific.

## Data flow

```text
Provider
   |
   v
Provider Adapter
   |
   v
Normalization
   |
   v
Validation
   |
   v
Ingestion Service
   |
   v
PostgreSQL
   |
   +--> Feature Engineering
   +--> Forecasting
   +--> Risk Models
   +--> Anomaly Detection
```

## Current database entities

- `companies`
- `market_prices`
- `risk_snapshots`

Upcoming stages add:

- `fundamentals`
- `financial_statements`
- `news_articles`
- `events`
- `documents`
- `model_predictions`
- `risk_factors`
