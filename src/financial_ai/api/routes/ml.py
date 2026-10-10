from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from financial_ai.data.normalization import normalize_symbol
from financial_ai.db.models import Company, MarketPrice
from financial_ai.db.session import get_db
from financial_ai.ml.service import compare_models, train_and_forecast

router = APIRouter(prefix="/ml", tags=["machine-learning"])


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


def _company(db: Session, ticker: str) -> Company:
    symbol = normalize_symbol(ticker)
    company = db.scalar(select(Company).where(Company.ticker == symbol))
    if company is None:
        raise HTTPException(status_code=404, detail=f"Company {symbol!r} not found.")
    return company


@router.get("/{ticker}/compare")
def compare_forecasting_models(ticker: str, db: Session = Depends(get_db)) -> dict[str, object]:
    company = _company(db, ticker)
    try:
        return {"ticker": normalize_symbol(ticker), **compare_models(_load_prices(db, company.id))}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{ticker}/forecast")
def forecast_next_day(
    ticker: str,
    model: str = Query(default="xgboost", pattern="^(xgboost|lightgbm|hist_gradient_boosting)$"),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    company = _company(db, ticker)
    try:
        return {
            "ticker": normalize_symbol(ticker),
            **train_and_forecast(_load_prices(db, company.id), model),
        }
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
