from __future__ import annotations

import numpy as np
import pandas as pd

from .schema import ListingFeatures, PredictionResponse


def _sanitize_frame(X: pd.DataFrame) -> pd.DataFrame:
    return X.astype(object).where(pd.notna(X), np.nan)


def _probability_high_demand(model, X: pd.DataFrame, predictions) -> list[float]:
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)
        if proba.ndim == 2 and proba.shape[1] > 1:
            return [float(x) for x in proba[:, 1]]
        return [float(x) for x in proba.reshape(-1)]
    return [float(x) for x in predictions]


def predict_single(features: ListingFeatures, model, run_id: str) -> PredictionResponse:
    X = _sanitize_frame(pd.DataFrame([features.model_dump()]))
    predictions = model.predict(X)
    probs = _probability_high_demand(model, X, predictions)
    return PredictionResponse(
        prediction=int(predictions[0]),
        probability_high_demand=float(probs[0]),
        model_run_id=run_id,
    )


def predict_batch(features_list: list[ListingFeatures], model, run_id: str) -> list[PredictionResponse]:
    X = _sanitize_frame(pd.DataFrame([features.model_dump() for features in features_list]))
    predictions = model.predict(X)
    probs = _probability_high_demand(model, X, predictions)
    return [
        PredictionResponse(
            prediction=int(pred),
            probability_high_demand=float(prob),
            model_run_id=run_id,
        )
        for pred, prob in zip(predictions, probs)
    ]
