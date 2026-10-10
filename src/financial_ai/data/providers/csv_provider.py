from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd


class CsvMarketDataProvider:
    """Deterministic provider for local/reproducible datasets."""

    def __init__(self, directory: str | Path = "data/raw/market") -> None:
        self.directory = Path(directory)

    def get_prices(
        self,
        symbol: str,
        start: date,
        end: date,
    ) -> pd.DataFrame:
        path = self.directory / f"{symbol.replace('/', '_')}.csv"
        if not path.exists():
            raise FileNotFoundError(f"Dataset not found: {path}")

        df = pd.read_csv(path, parse_dates=["trade_date"])
        required = {"trade_date", "open", "high", "low", "close", "volume"}
        missing = required.difference(df.columns)
        if missing:
            raise ValueError(f"CSV is missing columns: {sorted(missing)}")

        df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.tz_localize(None)
        df = df.set_index("trade_date").sort_index()

        mask = (df.index.date >= start) & (df.index.date < end)
        return df.loc[mask, ["open", "high", "low", "close", "volume"]].copy()
