from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from financial_ai.api.routes.ml import _company, _load_prices
from financial_ai.data.normalization import normalize_symbol
from financial_ai.db.session import get_db
from financial_ai.explainability.service import assess_risk, explain_latest_prediction
from financial_ai.ml.service import train_and_forecast

router = APIRouter(prefix="/intelligence", tags=["explainability-and-risk"])


@router.get("/{ticker}/explain")
def explain_prediction(
    ticker: str,
    top_n: int = Query(default=8, ge=1, le=14),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    company = _company(db, ticker)
    try:
        result = explain_latest_prediction(_load_prices(db, company.id), top_n=top_n)
        return {
            "ticker": normalize_symbol(ticker),
            "model": "xgboost",
            "as_of": str(
                pd.to_datetime(_load_prices(db, company.id)["trade_date"].iloc[-1]).date()
            ),
            "predicted_next_day_log_return": result.predicted_return,
            "baseline_return": result.baseline_return,
            "drivers": result.contributions,
        }
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{ticker}/risk")
def risk_intelligence(ticker: str, db: Session = Depends(get_db)) -> dict[str, object]:
    company = _company(db, ticker)
    try:
        prices = _load_prices(db, company.id)
        from financial_ai.analytics.quantitative import calculate_metrics

        analytics = {"metrics": calculate_metrics(prices).to_dict()}
        forecast = train_and_forecast(prices, "xgboost")
        return {
            "ticker": normalize_symbol(ticker),
            "forecast": forecast,
            "risk": assess_risk(analytics, forecast),
        }
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
