from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from financial_ai.ml.features import FEATURE_COLUMNS, build_features
from financial_ai.ml.models import evaluate_model, make_model

MODEL_DIR = Path("data/models")


def compare_models(rows: pd.DataFrame) -> dict[str, object]:
    frame = build_features(rows)
    candidates = ["xgboost", "lightgbm", "hist_gradient_boosting"]
    results = []
    for name in candidates:
        result = evaluate_model(frame, name)
        results.append(
            {
                "model": result.model_name,
                "mae": result.mae,
                "rmse": result.rmse,
                "directional_accuracy": result.directional_accuracy,
            }
        )
    results.sort(key=lambda item: (item["rmse"], -item["directional_accuracy"]))
    return {
        "observations": len(frame),
        "train_observations": int(len(frame) * 0.8),
        "test_observations": len(frame) - int(len(frame) * 0.8),
        "models": results,
        "selected_model": results[0]["model"],
    }


def train_and_forecast(rows: pd.DataFrame, model_name: str) -> dict[str, object]:
    frame = build_features(rows)
    evaluation = evaluate_model(frame, model_name)
    model = make_model(model_name)
    model.fit(frame[FEATURE_COLUMNS], frame["target_next_return"])

    latest = frame.iloc[[-1]]
    predicted_return = float(model.predict(latest[FEATURE_COLUMNS])[0])
    current_price = float(rows.sort_values("trade_date")["close"].iloc[-1])
    predicted_price = float(current_price * np.exp(predicted_return))
    latest_date = pd.to_datetime(latest["trade_date"].iloc[0]).date()

    return {
        "model": model_name,
        "as_of": latest_date.isoformat(),
        "current_price": current_price,
        "predicted_next_day_log_return": predicted_return,
        "predicted_next_day_price": predicted_price,
        "evaluation": {
            "mae": evaluation.mae,
            "rmse": evaluation.rmse,
            "directional_accuracy": evaluation.directional_accuracy,
            "test_observations": len(evaluation.actuals),
        },
        "feature_count": len(FEATURE_COLUMNS),
    }


def persist_model(ticker: str, model_name: str, rows: pd.DataFrame) -> Path:
    frame = build_features(rows)
    model = make_model(model_name)
    model.fit(frame[FEATURE_COLUMNS], frame["target_next_return"])
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    path = MODEL_DIR / f"{ticker.lower().replace('.', '_')}_{model_name}.joblib"
    joblib.dump(
        {
            "model": model,
            "features": FEATURE_COLUMNS,
            "trained_through": str(frame["trade_date"].iloc[-1]),
        },
        path,
    )
    return path
