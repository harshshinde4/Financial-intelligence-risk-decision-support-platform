from __future__ import annotations

from datetime import date

import pandas as pd
import yfinance as yf


class YFinanceProvider:
    """Research/development market-data adapter.

    Supports Yahoo Finance symbols, including US and common Indian
    exchange suffixes such as .NS and .BO.
    """

    REQUIRED_COLUMNS = ["open", "high", "low", "close", "volume"]

    def get_prices(
        self,
        symbol: str,
        start: date,
        end: date,
    ) -> pd.DataFrame:
        raw = yf.download(
            symbol,
            start=start.isoformat(),
            end=end.isoformat(),
            auto_adjust=False,
            progress=False,
            group_by="column",
        )

        if raw.empty:
            raise ValueError(
                f"No market data returned for symbol={symbol!r}. "
                "Check the symbol and requested date range."
            )

        # yfinance may return a MultiIndex even for one ticker.
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = [str(col[0]).lower() for col in raw.columns]
        else:
            raw.columns = [str(col).lower() for col in raw.columns]

        missing = [column for column in self.REQUIRED_COLUMNS if column not in raw.columns]
        if missing:
            raise ValueError(f"Provider response is missing columns: {missing}")

        result = raw[self.REQUIRED_COLUMNS].copy()
        result.index = pd.to_datetime(result.index).tz_localize(None)
        result.index.name = "trade_date"

        for column in self.REQUIRED_COLUMNS:
            result[column] = pd.to_numeric(result[column], errors="coerce")

        result = result.dropna(subset=["open", "high", "low", "close"])
        result["volume"] = result["volume"].fillna(0).astype("int64")
        result = result[~result.index.duplicated(keep="last")]
        return result.sort_index()
