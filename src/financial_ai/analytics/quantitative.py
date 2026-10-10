from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 252


@dataclass(frozen=True)
class QuantitativeMetrics:
    observations: int
    current_price: float
    period_return: float | None
    annualized_return: float | None
    annualized_volatility: float | None
    sharpe_ratio: float | None
    sortino_ratio: float | None
    max_drawdown: float | None
    value_at_risk_95: float | None
    expected_shortfall_95: float | None
    average_daily_volume: float | None

    def to_dict(self) -> dict[str, float | int | None]:
        return asdict(self)


def prepare_prices(rows: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalize market-price data for analytics."""
    required = {"trade_date", "open", "high", "low", "close", "volume"}
    missing = required.difference(rows.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    data = rows.copy()
    data["trade_date"] = pd.to_datetime(data["trade_date"], errors="coerce")
    for column in ("open", "high", "low", "close", "volume"):
        data[column] = pd.to_numeric(data[column], errors="coerce")

    data = data.dropna(subset=["trade_date", "close"])
    data = data[data["close"] > 0]
    data = data.sort_values("trade_date").drop_duplicates("trade_date")
    if data.empty:
        raise ValueError("No valid market-price observations available.")

    data["daily_return"] = data["close"].pct_change()
    return data.reset_index(drop=True)


def _annualized_return(prices: pd.Series, observations: int) -> float | None:
    if observations < 2 or prices.iloc[0] <= 0 or prices.iloc[-1] <= 0:
        return None
    years = observations / TRADING_DAYS_PER_YEAR
    if years <= 0:
        return None
    return float((prices.iloc[-1] / prices.iloc[0]) ** (1 / years) - 1)


def _sharpe(returns: pd.Series) -> float | None:
    clean = returns.dropna()
    if len(clean) < 2:
        return None
    volatility = clean.std(ddof=1)
    if volatility == 0 or pd.isna(volatility):
        return None
    return float(np.sqrt(TRADING_DAYS_PER_YEAR) * clean.mean() / volatility)


def _sortino(returns: pd.Series) -> float | None:
    clean = returns.dropna()
    if len(clean) < 2:
        return None
    downside = clean.clip(upper=0)
    downside_deviation = np.sqrt((downside**2).mean())
    if downside_deviation == 0 or pd.isna(downside_deviation):
        return None
    return float(np.sqrt(TRADING_DAYS_PER_YEAR) * clean.mean() / downside_deviation)


def _historical_var_es(
    returns: pd.Series, confidence: float = 0.95
) -> tuple[float | None, float | None]:
    clean = returns.dropna()
    if len(clean) < 20:
        return None, None
    quantile = float(clean.quantile(1 - confidence))
    tail = clean[clean <= quantile]
    if tail.empty:
        return None, None
    return float(max(0.0, -quantile)), float(max(0.0, -tail.mean()))


def max_drawdown(prices: pd.Series) -> float | None:
    if prices.empty:
        return None
    running_peak = prices.cummax()
    drawdowns = prices / running_peak - 1
    return float(drawdowns.min())


def calculate_metrics(rows: pd.DataFrame, lookback: int | None = None) -> QuantitativeMetrics:
    data = prepare_prices(rows)
    if lookback is not None:
        if lookback < 2:
            raise ValueError("lookback must be at least 2")
        data = data.tail(lookback).reset_index(drop=True)

    returns = data["daily_return"]
    clean_returns = returns.dropna()
    var_95, es_95 = _historical_var_es(returns)
    annualized_volatility = (
        float(clean_returns.std(ddof=1) * np.sqrt(TRADING_DAYS_PER_YEAR))
        if len(clean_returns) >= 2
        else None
    )

    return QuantitativeMetrics(
        observations=len(data),
        current_price=float(data["close"].iloc[-1]),
        period_return=(
            float(data["close"].iloc[-1] / data["close"].iloc[0] - 1) if len(data) >= 2 else None
        ),
        annualized_return=_annualized_return(data["close"], len(data)),
        annualized_volatility=annualized_volatility,
        sharpe_ratio=_sharpe(returns),
        sortino_ratio=_sortino(returns),
        max_drawdown=max_drawdown(data["close"]),
        value_at_risk_95=var_95,
        expected_shortfall_95=es_95,
        average_daily_volume=(
            float(data["volume"].mean())
            if "volume" in data and data["volume"].notna().any()
            else None
        ),
    )


def technical_indicators(rows: pd.DataFrame) -> dict[str, float | None | str]:
    """Return the latest technical indicators from a price history."""
    data = prepare_prices(rows)
    close = data["close"]

    sma20 = close.rolling(20).mean()
    sma50 = close.rolling(50).mean()
    sma200 = close.rolling(200).mean()
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    macd_signal = macd.ewm(span=9, adjust=False).mean()

    delta = close.diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)
    avg_gain = gains.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    avg_loss = losses.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.fillna(100).where(avg_gain.notna(), np.nan)

    rolling20 = close.rolling(20)
    middle = rolling20.mean()
    std = rolling20.std(ddof=0)
    upper = middle + 2 * std
    lower = middle - 2 * std

    latest = {
        "sma_20": sma20.iloc[-1],
        "sma_50": sma50.iloc[-1],
        "sma_200": sma200.iloc[-1],
        "rsi_14": rsi.iloc[-1],
        "macd": macd.iloc[-1],
        "macd_signal": macd_signal.iloc[-1],
        "macd_histogram": (macd - macd_signal).iloc[-1],
        "bollinger_middle_20": middle.iloc[-1],
        "bollinger_upper_20": upper.iloc[-1],
        "bollinger_lower_20": lower.iloc[-1],
    }

    result: dict[str, float | None | str] = {}
    for key, value in latest.items():
        result[key] = None if pd.isna(value) else float(value)

    if result["sma_20"] is not None:
        result["price_vs_sma_20"] = float(close.iloc[-1] / result["sma_20"] - 1)  # type: ignore[operator]
    else:
        result["price_vs_sma_20"] = None

    return result


def detect_anomalies(rows: pd.DataFrame, return_z_threshold: float = 3.5) -> dict[str, object]:
    """Detect unusual returns and volume using robust rolling MAD scores."""
    data = prepare_prices(rows)
    returns = data["daily_return"]
    volume = data["volume"].replace(0, np.nan)

    rolling_median = returns.rolling(30, min_periods=15).median()
    rolling_mad = (returns - rolling_median).abs().rolling(30, min_periods=15).median()
    return_score = 0.6745 * (returns - rolling_median) / rolling_mad.replace(0, np.nan)

    volume_log = np.log1p(volume)
    volume_median = volume_log.rolling(30, min_periods=15).median()
    volume_mad = (volume_log - volume_median).abs().rolling(30, min_periods=15).median()
    volume_score = 0.6745 * (volume_log - volume_median) / volume_mad.replace(0, np.nan)

    data["return_robust_z"] = return_score
    data["volume_robust_z"] = volume_score
    data["is_anomaly"] = (return_score.abs() >= return_z_threshold) | (
        volume_score.abs() >= return_z_threshold
    )

    anomalies = data[data["is_anomaly"]].tail(20)
    latest = data.iloc[-1]
    return {
        "total_anomalies": int(data["is_anomaly"].sum()),
        "latest_is_anomaly": bool(latest["is_anomaly"]),
        "latest_return_z": None
        if pd.isna(latest["return_robust_z"])
        else float(latest["return_robust_z"]),
        "latest_volume_z": None
        if pd.isna(latest["volume_robust_z"])
        else float(latest["volume_robust_z"]),
        "recent_anomalies": [
            {
                "trade_date": row.trade_date.date().isoformat(),
                "close": float(row.close),
                "daily_return": None if pd.isna(row.daily_return) else float(row.daily_return),
                "return_z": None if pd.isna(row.return_robust_z) else float(row.return_robust_z),
                "volume_z": None if pd.isna(row.volume_robust_z) else float(row.volume_robust_z),
            }
            for row in anomalies.itertuples(index=False)
        ],
    }
