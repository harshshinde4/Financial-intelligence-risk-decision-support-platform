from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from financial_ai.data.providers.base import MarketDataProvider
from financial_ai.db.models import Company, MarketPrice


def ingest_market_prices(
    db: Session,
    provider: MarketDataProvider,
    company: Company,
    start: date,
    end: date,
) -> int:
    prices = provider.get_prices(company.ticker, start, end)
    records = 0

    for trade_date, row in prices.iterrows():
        existing = (
            db.query(MarketPrice)
            .filter(
                MarketPrice.company_id == company.id,
                MarketPrice.trade_date == trade_date.to_pydatetime(),
            )
            .one_or_none()
        )

        values = {
            "company_id": company.id,
            "trade_date": trade_date.to_pydatetime(),
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "volume": int(row["volume"]),
        }

        if existing:
            for key, value in values.items():
                setattr(existing, key, value)
        else:
            db.add(MarketPrice(**values))

        records += 1

    db.commit()
    return records


def export_prices_to_parquet(
    prices: pd.DataFrame,
    output_path: str | Path,
) -> Path:
    """Persist a normalized provider response for reproducible downstream work."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    prices.reset_index().to_parquet(path, index=False)
    return path
