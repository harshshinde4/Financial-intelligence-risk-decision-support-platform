# Stage 3 — Quantitative Financial Analytics

Stage 3 adds a schema-free analytics layer over the existing `market_prices` table.

## Endpoint

`GET /api/v1/analytics/{ticker}/summary?lookback=252`

The response includes:

- period and annualized returns
- annualized volatility
- Sharpe and Sortino ratios
- maximum drawdown
- historical 95% VaR and Expected Shortfall
- average daily volume
- SMA(20/50/200)
- RSI(14)
- MACD and signal/histogram
- Bollinger Bands
- robust return/volume anomaly detection

## Design decisions

1. Analytics are computed from persisted market prices; no duplicate analytics tables are introduced yet.
2. The default lookback is 252 observations, approximately one trading year.
3. VaR/Expected Shortfall are historical, not parametric.
4. Risk ratios use a zero daily risk-free rate in this stage. A configurable risk-free curve can be added later.
5. Anomaly detection uses robust rolling median/MAD scores rather than an LLM or arbitrary thresholds.
6. The LLM/agent layer will consume these deterministic outputs later; it will not calculate financial metrics itself.
