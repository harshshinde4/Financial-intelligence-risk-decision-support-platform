from financial_ai.data.sample_data import generate_sample_prices


def test_sample_prices_are_deterministic() -> None:
    first = generate_sample_prices("AAPL", days=10, seed=42)
    second = generate_sample_prices("AAPL", days=10, seed=42)

    assert first.equals(second)
    assert len(first) == 10
    assert {"trade_date", "open", "high", "low", "close", "volume"} <= set(first.columns)
