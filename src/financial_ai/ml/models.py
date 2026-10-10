from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from xgboost import XGBRegressor

try:
    from lightgbm import LGBMRegressor
except ImportError:  # pragma: no cover
    LGBMRegressor = None  # type: ignore[assignment,misc]

from financial_ai.ml.features import FEATURE_COLUMNS


@dataclass(frozen=True)
class ModelResult:
    model_name: str
    mae: float
    rmse: float
    directional_accuracy: float
    predictions: np.ndarray
    actuals: np.ndarray


def make_model(name: str):
    name = name.lower()
    if name == "xgboost":
        return XGBRegressor(
            n_estimators=350,
            max_depth=4,
            learning_rate=0.035,
            subsample=0.85,
            colsample_bytree=0.85,
            reg_lambda=1.5,
            objective="reg:squarederror",
            random_state=42,
            n_jobs=2,
        )
    if name == "lightgbm":
        if LGBMRegressor is None:
            raise RuntimeError("LightGBM is not installed. Install the [ml] dependency group.")
        return LGBMRegressor(
            n_estimators=300,
            num_leaves=24,
            learning_rate=0.035,
            subsample=0.85,
            colsample_bytree=0.85,
            reg_lambda=1.5,
            random_state=42,
            verbosity=-1,
        )
    if name == "hist_gradient_boosting":
        return HistGradientBoostingRegressor(
            max_iter=250,
            learning_rate=0.04,
            max_leaf_nodes=24,
            l2_regularization=1.0,
            random_state=42,
        )
    raise ValueError("Unsupported model. Choose xgboost, lightgbm, or hist_gradient_boosting.")


def evaluate_model(
    frame: pd.DataFrame, model_name: str, train_fraction: float = 0.8
) -> ModelResult:
    if not 0.6 <= train_fraction < 1:
        raise ValueError("train_fraction must be between 0.6 and 0.99")
    if len(frame) < 120:
        raise ValueError("At least 120 engineered observations are required for model evaluation.")

    split = int(len(frame) * train_fraction)
    train = frame.iloc[:split]
    test = frame.iloc[split:]
    model = make_model(model_name)
    model.fit(train[FEATURE_COLUMNS], train["target_next_return"])
    predictions = np.asarray(model.predict(test[FEATURE_COLUMNS]), dtype=float)
    actuals = test["target_next_return"].to_numpy(dtype=float)
    mae = float(mean_absolute_error(actuals, predictions))
    rmse = float(np.sqrt(mean_squared_error(actuals, predictions)))
    directional_accuracy = float((np.sign(actuals) == np.sign(predictions)).mean())
    return ModelResult(model_name, mae, rmse, directional_accuracy, predictions, actuals)
