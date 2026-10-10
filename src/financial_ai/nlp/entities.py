from __future__ import annotations

import re

DEFAULT_TICKERS = {"AAPL", "MSFT", "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "RELIANCE.BO"}


def extract_ticker_entities(text: str, known_tickers: set[str] | None = None) -> list[str]:
    tickers = known_tickers or DEFAULT_TICKERS
    upper = text.upper()
    found = [
        ticker
        for ticker in tickers
        if re.search(rf"(?<![A-Z0-9]){re.escape(ticker)}(?![A-Z0-9])", upper)
    ]
    return sorted(found)
