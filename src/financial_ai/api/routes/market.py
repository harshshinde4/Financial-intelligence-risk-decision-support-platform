from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from financial_ai.data.ingestion.market import ingest_market_prices
from financial_ai.data.normalization import normalize_symbol
from financial_ai.data.providers.yfinance_provider import YFinanceProvider
from financial_ai.db.models import Company, MarketPrice
from financial_ai.db.session import get_db

router = APIRouter(prefix="/market", tags=["market-data"])


@router.post("/ingest/{ticker}")
def ingest(
    ticker: str,
    start: date = Query(...),
    end: date = Query(...),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    symbol = normalize_symbol(ticker)
    company = db.scalar(select(Company).where(Company.ticker == symbol))

    if company is None:
        raise HTTPException(
            status_code=404,
            detail=f"Company {symbol!r} is not registered.",
        )

    if start >= end:
        raise HTTPException(status_code=400, detail="start must be before end")

    provider = YFinanceProvider()

    try:
        count = ingest_market_prices(
            db=db,
            provider=provider,
            company=company,
            start=start,
            end=end,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {
        "ticker": symbol,
        "provider": "yfinance",
        "rows_upserted": count,
        "start": start.isoformat(),
        "end": end.isoformat(),
    }


@router.get("/{ticker}", response_model=list[dict[str, object]])
def get_market_prices(
    ticker: str,
    limit: int = Query(default=100, ge=1, le=5000),
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    symbol = normalize_symbol(ticker)
    company = db.scalar(select(Company).where(Company.ticker == symbol))

    if company is None:
        raise HTTPException(status_code=404, detail=f"Company {symbol!r} not found.")

    rows = db.scalars(
        select(MarketPrice)
        .where(MarketPrice.company_id == company.id)
        .order_by(MarketPrice.trade_date.desc())
        .limit(limit)
    ).all()

    return [
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
