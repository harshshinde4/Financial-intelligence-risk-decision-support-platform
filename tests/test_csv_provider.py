from datetime import date

from financial_ai.data.providers.csv_provider import CsvMarketDataProvider
from financial_ai.data.sample_data import write_sample_datasets


def test_csv_provider(tmp_path) -> None:
    write_sample_datasets(tmp_path, ["AAPL"])

    provider = CsvMarketDataProvider(tmp_path)
    data = provider.get_prices(
        "AAPL",
        date(2024, 1, 1),
        date(2025, 1, 1),
    )

    assert not data.empty
    assert list(data.columns) == ["open", "high", "low", "close", "volume"]
