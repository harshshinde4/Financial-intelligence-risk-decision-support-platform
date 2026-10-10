import numpy as np
import pandas as pd

from financial_ai.analytics.quantitative import (
    calculate_metrics,
    detect_anomalies,
    technical_indicators,
)


def make_prices(n: int = 260) -> pd.DataFrame:
    dates = pd.bdate_range("2024-01-01", periods=n)
    close = 100 * np.cumprod(1 + np.full(n, 0.001))
    return pd.DataFrame(
        {
            "trade_date": dates,
            "open": close,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": np.full(n, 1_000_000),
        }
    )


def test_metrics_are_computed() -> None:
    metrics = calculate_metrics(make_prices(), lookback=252)
    assert metrics.observations == 252
    assert metrics.current_price > 100
    assert metrics.period_return is not None
    assert metrics.annualized_volatility is not None
    assert metrics.max_drawdown == 0.0


def test_technical_indicators() -> None:
    result = technical_indicators(make_prices())
    assert result["sma_20"] is not None
    assert result["sma_50"] is not None
    assert result["rsi_14"] is not None
    assert result["macd"] is not None


def test_anomaly_output_shape() -> None:
    result = detect_anomalies(make_prices())
    assert "total_anomalies" in result
    assert "recent_anomalies" in result
