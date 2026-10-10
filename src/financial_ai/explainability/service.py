from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import shap

from financial_ai.ml.features import FEATURE_COLUMNS, build_features
from financial_ai.ml.models import make_model


@dataclass(frozen=True)
class ExplainabilityResult:
    predicted_return: float
    baseline_return: float
    contributions: list[dict[str, float | str]]


def _train_xgboost(frame: pd.DataFrame):
    model = make_model("xgboost")
    model.fit(frame[FEATURE_COLUMNS], frame["target_next_return"])
    return model


def explain_latest_prediction(rows: pd.DataFrame, top_n: int = 8) -> ExplainabilityResult:
    frame = build_features(rows)
    model = _train_xgboost(frame)
    latest = frame.iloc[[-1]][FEATURE_COLUMNS]

    predicted = float(model.predict(latest)[0])
    explainer = shap.TreeExplainer(model)
    shap_values = np.asarray(explainer.shap_values(latest)).reshape(-1)
    expected = float(np.asarray(explainer.expected_value).reshape(-1)[0])

    contributions = [
        {
            "feature": feature,
            "value": float(latest.iloc[0][feature]),
            "contribution": float(contribution),
        }
        for feature, contribution in zip(FEATURE_COLUMNS, shap_values, strict=True)
    ]
    contributions.sort(key=lambda item: abs(float(item["contribution"])), reverse=True)

    return ExplainabilityResult(
        predicted_return=predicted,
        baseline_return=expected,
        contributions=contributions[:top_n],
    )


def assess_risk(analytics: dict[str, object], forecast: dict[str, object]) -> dict[str, object]:
    """Deterministic risk classification; no LLM is used for the decision."""
    metrics = analytics.get("metrics", {})
    if not isinstance(metrics, dict):
        metrics = {}

    volatility = float(metrics.get("annualized_volatility") or 0.0)
    drawdown = abs(float(metrics.get("max_drawdown") or 0.0))
    var_95 = abs(float(metrics.get("value_at_risk_95") or 0.0))
    predicted_return = float(forecast.get("predicted_next_day_log_return") or 0.0)

    score = 0
    drivers: list[dict[str, object]] = []

    if volatility >= 0.45:
        score += 2
        drivers.append({"driver": "high_volatility", "severity": "high", "value": volatility})
    elif volatility >= 0.30:
        score += 1
        drivers.append({"driver": "elevated_volatility", "severity": "medium", "value": volatility})

    if drawdown >= 0.30:
        score += 2
        drivers.append({"driver": "large_drawdown", "severity": "high", "value": drawdown})
    elif drawdown >= 0.15:
        score += 1
        drivers.append({"driver": "meaningful_drawdown", "severity": "medium", "value": drawdown})

    if var_95 >= 0.03:
        score += 2
        drivers.append({"driver": "high_daily_var", "severity": "high", "value": var_95})
    elif var_95 >= 0.02:
        score += 1
        drivers.append({"driver": "elevated_daily_var", "severity": "medium", "value": var_95})

    if predicted_return <= -0.02:
        score += 2
        drivers.append(
            {"driver": "negative_forecast", "severity": "high", "value": predicted_return}
        )
    elif predicted_return < 0:
        score += 1
        drivers.append(
            {"driver": "negative_forecast", "severity": "medium", "value": predicted_return}
        )

    level = (
        "low" if score <= 1 else "medium" if score <= 3 else "high" if score <= 5 else "critical"
    )
    return {"risk_score": score, "risk_level": level, "drivers": drivers}
