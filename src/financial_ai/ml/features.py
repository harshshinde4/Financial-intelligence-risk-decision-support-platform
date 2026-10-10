from __future__ import annotations

import numpy as np
import pandas as pd

FEATURE_COLUMNS = [
    "return_1d",
    "return_5d",
    "return_20d",
    "volatility_20d",
    "volume_change_1d",
    "sma_5_ratio",
    "sma_20_ratio",
    "sma_50_ratio",
    "rsi_14",
    "macd",
    "macd_signal",
    "bb_position",
    "high_low_range",
    "close_open_return",
]


def build_features(rows: pd.DataFrame) -> pd.DataFrame:
    required = {"trade_date", "open", "high", "low", "close", "volume"}
    missing = required.difference(rows.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    data = rows.copy()
    data["trade_date"] = pd.to_datetime(data["trade_date"], errors="coerce")
    for col in ("open", "high", "low", "close", "volume"):
        data[col] = pd.to_numeric(data[col], errors="coerce")
    data = data.dropna(subset=["trade_date", "open", "high", "low", "close", "volume"])
    data = data[data["close"] > 0].sort_values("trade_date").drop_duplicates("trade_date")
    if len(data) < 60:
        raise ValueError("At least 60 observations are required for ML feature engineering.")

    close = data["close"]
    returns = np.log(close / close.shift(1))
    data["return_1d"] = returns
    data["return_5d"] = np.log(close / close.shift(5))
    data["return_20d"] = np.log(close / close.shift(20))
    data["volatility_20d"] = returns.rolling(20).std() * np.sqrt(252)
    data["volume_change_1d"] = data["volume"].pct_change().replace([np.inf, -np.inf], np.nan)
    for window in (5, 20, 50):
        data[f"sma_{window}_ratio"] = close / close.rolling(window).mean() - 1

    delta = close.diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)
    avg_gain = gains.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    avg_loss = losses.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    data["rsi_14"] = 100 - 100 / (1 + rs)

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    data["macd"] = ema12 - ema26
    data["macd_signal"] = data["macd"].ewm(span=9, adjust=False).mean()
    middle = close.rolling(20).mean()
    std = close.rolling(20).std(ddof=0)
    upper = middle + 2 * std
    lower = middle - 2 * std
    data["bb_position"] = (close - lower) / (upper - lower).replace(0, np.nan)
    data["high_low_range"] = (data["high"] - data["low"]) / close
    data["close_open_return"] = data["close"] / data["open"] - 1

    # Target is the next trading day's log return. Features are shifted only by target construction,
    # so a row dated t uses information available at the close of t to predict t+1.
    data["target_next_return"] = returns.shift(-1)
    return data.dropna(subset=FEATURE_COLUMNS + ["target_next_return"]).reset_index(drop=True)
