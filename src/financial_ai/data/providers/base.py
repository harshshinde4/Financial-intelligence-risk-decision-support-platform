from __future__ import annotations

from datetime import date
from typing import Protocol

import pandas as pd


class MarketDataProvider(Protocol):
    """Provider contract used by the application.

    The application depends on this interface, not on a vendor SDK.
    """

    def get_prices(
        self,
        symbol: str,
        start: date,
        end: date,
    ) -> pd.DataFrame:
        """Return normalized OHLCV data indexed by trading date."""
        ...
