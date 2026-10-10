import pytest

from financial_ai.data.normalization import infer_market, normalize_symbol


@pytest.mark.parametrize(
    ("symbol", "expected"),
    [
        ("aapl", "AAPL"),
        ("RELIANCE.NS", "RELIANCE.NS"),
        ("reliance.bo", "RELIANCE.BO"),
    ],
)
def test_normalize_symbol(symbol: str, expected: str) -> None:
    assert normalize_symbol(symbol) == expected


@pytest.mark.parametrize(
    ("symbol", "market"),
    [
        ("AAPL", "US_OR_OTHER"),
        ("RELIANCE.NS", "NSE"),
        ("RELIANCE.BO", "BSE"),
    ],
)
def test_infer_market(symbol: str, market: str) -> None:
    assert infer_market(symbol) == market
