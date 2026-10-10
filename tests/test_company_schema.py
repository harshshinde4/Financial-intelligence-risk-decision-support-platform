from financial_ai.api.schemas import CompanyCreate


def test_company_payload_normalizes_to_expected_fields() -> None:
    company = CompanyCreate(
        ticker="AAPL",
        name="Apple Inc.",
        exchange="NASDAQ",
        sector="Technology",
    )

    assert company.ticker == "AAPL"
    assert company.name == "Apple Inc."
    assert company.industry is None
