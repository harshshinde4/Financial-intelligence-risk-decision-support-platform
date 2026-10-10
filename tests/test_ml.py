import numpy as np
import pandas as pd

from financial_ai.ml.features import FEATURE_COLUMNS, build_features
from financial_ai.ml.models import evaluate_model


def sample_prices(n=220):
    rng = np.random.default_rng(42)
    returns = rng.normal(0.0005, 0.012, n)
    close = 100 * np.exp(np.cumsum(returns))
    return pd.DataFrame(
        {
            "trade_date": pd.date_range("2020-01-01", periods=n, freq="B"),
            "open": close * (1 + rng.normal(0, 0.002, n)),
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": rng.integers(100_000, 500_000, n),
        }
    )


def test_feature_engineering_is_leakage_safe_shape():
    frame = build_features(sample_prices())
    assert len(frame) > 100
    assert all(column in frame.columns for column in FEATURE_COLUMNS)
    assert frame[FEATURE_COLUMNS].notna().all().all()


def test_xgboost_walk_forward_metrics_are_finite():
    result = evaluate_model(build_features(sample_prices()), "xgboost")
    assert np.isfinite(result.mae)
    assert np.isfinite(result.rmse)
    assert 0 <= result.directional_accuracy <= 1
