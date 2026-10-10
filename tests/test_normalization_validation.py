import pytest

from financial_ai.data.normalization import normalize_symbol


@pytest.mark.parametrize(
    ("symbol", "expected"),
    [
        ("AAPL", "AAPL"),
        (" aapl ", "AAPL"),
        ("RELIANCE.NS", "RELIANCE.NS"),
        ("reliance.ns", "RELIANCE.NS"),
        ("TCS.NS", "TCS.NS"),
        ("HDFCBANK.NS", "HDFCBANK.NS"),
        ("RELIANCE.BO", "RELIANCE.BO"),
        ("BRK.B", "BRK.B"),
        ("M&M", "M&M"),
        ("ABC-1", "ABC-1"),
    ],
)
def test_normalize_valid_symbols(symbol: str, expected: str) -> None:
    assert normalize_symbol(symbol) == expected


@pytest.mark.parametrize(
    "symbol",
    [
        "",
        "   ",
        "AAPL/US",
        "AAP L",
        ".AAPL",
        "AAPL.",
        "AAPL..NS",
        "AAPL@",
        "A" * 33,
    ],
)
def test_reject_invalid_symbols(symbol: str) -> None:
    with pytest.raises(ValueError):
        normalize_symbol(symbol)


def test_reject_non_string_symbol() -> None:
    with pytest.raises(ValueError):
        normalize_symbol(None)  # type: ignore[arg-type]
