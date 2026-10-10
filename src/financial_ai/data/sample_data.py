from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

DEFAULT_SYMBOLS = [
    "AAPL",
    "MSFT",
    "RELIANCE.NS",
    "TCS.NS",
    "HDFCBANK.NS",
    "RELIANCE.BO",
]


def generate_sample_prices(
    symbol: str,
    start: date = date(2024, 1, 1),
    days: int = 300,
    seed: int = 42,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(start=start, periods=days)

    # Deterministic synthetic price series for tests/local development.
    returns = rng.normal(loc=0.0004, scale=0.015, size=len(dates))
    close = 100 * np.exp(np.cumsum(returns))

    open_price = close * (1 + rng.normal(0, 0.003, len(dates)))
    high = np.maximum(open_price, close) * (1 + rng.uniform(0, 0.01, len(dates)))
    low = np.minimum(open_price, close) * (1 - rng.uniform(0, 0.01, len(dates)))
    volume = rng.integers(100_000, 5_000_000, len(dates))

    return pd.DataFrame(
        {
            "trade_date": dates,
            "open": open_price,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
    )


def write_sample_datasets(
    directory: str | Path = "data/raw/market",
    symbols: list[str] | None = None,
) -> list[Path]:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    symbols = symbols or DEFAULT_SYMBOLS

    paths: list[Path] = []
    for index, symbol in enumerate(symbols):
        df = generate_sample_prices(symbol, seed=42 + index)
        path = directory / f"{symbol.replace('/', '_')}.csv"
        df.to_csv(path, index=False)
        paths.append(path)

    return paths
