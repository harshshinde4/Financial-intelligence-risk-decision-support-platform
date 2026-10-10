from financial_ai.data.normalization import infer_market
from financial_ai.db.models import Company
from financial_ai.db.session import SessionLocal

COMPANIES = [
    ("AAPL", "Apple Inc."),
    ("MSFT", "Microsoft Corporation"),
    ("RELIANCE.NS", "Reliance Industries Limited"),
    ("TCS.NS", "Tata Consultancy Services Limited"),
    ("HDFCBANK.NS", "HDFC Bank Limited"),
    ("RELIANCE.BO", "Reliance Industries Limited"),
]


def main() -> None:
    with SessionLocal() as db:
        for ticker, name in COMPANIES:
            existing = db.query(Company).filter(Company.ticker == ticker).one_or_none()
            if existing:
                continue

            market = infer_market(ticker)
            db.add(
                Company(
                    ticker=ticker,
                    name=name,
                    exchange=market,
                )
            )

        db.commit()


if __name__ == "__main__":
    main()
