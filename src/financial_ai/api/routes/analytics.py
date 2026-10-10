import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from financial_ai.analytics.quantitative import (
    calculate_metrics,
    detect_anomalies,
    technical_indicators,
)
from financial_ai.data.normalization import normalize_symbol
from financial_ai.db.models import Company, MarketPrice
from financial_ai.db.session import get_db

router = APIRouter(prefix="/analytics", tags=["quantitative-analytics"])


def _load_prices(db: Session, company_id: int) -> pd.DataFrame:
    rows = db.scalars(
        select(MarketPrice)
        .where(MarketPrice.company_id == company_id)
        .order_by(MarketPrice.trade_date.asc())
    ).all()
    if not rows:
        raise HTTPException(
            status_code=404, detail="No market-price history is available for this ticker."
        )

    return pd.DataFrame(
        [
            {
                "trade_date": row.trade_date,
                "open": row.open,
                "high": row.high,
                "low": row.low,
                "close": row.close,
                "volume": row.volume,
            }
            for row in rows
        ]
    )


@router.get("/{ticker}/summary")
def analytics_summary(
    ticker: str,
    lookback: int = Query(default=252, ge=20, le=5000),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    symbol = normalize_symbol(ticker)
    company = db.scalar(select(Company).where(Company.ticker == symbol))
    if company is None:
        raise HTTPException(status_code=404, detail=f"Company {symbol!r} not found.")

    prices = _load_prices(db, company.id)
    if len(prices) < 20:
        raise HTTPException(
            status_code=422, detail="At least 20 observations are required for analytics."
        )

    analysis_prices = prices.tail(lookback).reset_index(drop=True)
    metrics = calculate_metrics(analysis_prices)
    indicators = technical_indicators(analysis_prices)
    anomalies = detect_anomalies(analysis_prices)

    latest_date = pd.to_datetime(analysis_prices["trade_date"]).max().date()
    return {
        "ticker": symbol,
        "analysis_date": latest_date.isoformat(),
        "lookback": len(analysis_prices),
        "metrics": metrics.to_dict(),
        "technical_indicators": indicators,
        "anomaly_detection": anomalies,
    }
