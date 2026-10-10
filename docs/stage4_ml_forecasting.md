# Stage 4 — ML Forecasting & Risk Modeling

## Goal
Move from deterministic quantitative analytics to leakage-safe, out-of-sample machine-learning forecasting.

## Target
The model predicts the **next trading day's log return**, not a raw stock price. The API converts that predicted return into an indicative next-day price using the latest close.

## Features
- 1/5/20-day log returns
- 20-day annualized volatility
- volume change
- price/SMA ratios
- RSI-14
- MACD and signal
- Bollinger position
- intraday high-low range
- close/open return

## Models
- XGBoost
- LightGBM
- HistGradientBoosting baseline

## Evaluation
A chronological 80/20 split is used. No random shuffle is used because financial observations are time-dependent. Metrics:
- MAE
- RMSE
- directional accuracy

## API
- `GET /api/v1/ml/{ticker}/compare`
- `GET /api/v1/ml/{ticker}/forecast?model=xgboost`

This stage deliberately keeps model training deterministic and separate from future LLM/agent reasoning. Agents will consume validated analytics/model outputs rather than perform numerical calculations themselves.
