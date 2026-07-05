from __future__ import annotations

from typing import Iterable, List

import numpy as np
import pandas as pd
from fastapi import HTTPException, status

from . import config
from .schemas import ListingFeatures, PredictionResponse


def records_to_dataframe(records: Iterable[ListingFeatures]) -> pd.DataFrame:
    """Convert validated API payloads into the exact DataFrame expected by the model."""
    rows = [record.model_dump() for record in records]
    df = pd.DataFrame(rows)

    # TODO 1: reject unknown fields and forbidden leakage fields.
    # TODO 2: check missing fields against config.EXPECTED_FEATURE_COLUMNS.
    # TODO 3: return df[config.EXPECTED_FEATURE_COLUMNS].

    missing_cols = [c for c in config.EXPECTED_FEATURE_COLUMNS if c not in df.columns]
    if missing_cols:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Missing required model input fields.", "missing_fields": missing_cols},
        )

    unknown_cols = sorted(set(df.columns) - set(config.EXPECTED_FEATURE_COLUMNS))
    forbidden_cols = sorted(set(df.columns).intersection(config.FORBIDDEN_FIELDS))
    if unknown_cols or forbidden_cols:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Request contains fields that are not accepted as model inputs.",
                "unknown_fields": unknown_cols,
                "forbidden_fields": forbidden_cols,
            },
        )

    return df[config.EXPECTED_FEATURE_COLUMNS]


def predict_records(model, records: List[ListingFeatures]) -> List[PredictionResponse]:
    """TODO: Run model prediction and return API responses."""
    X = records_to_dataframe(records)

    # TODO:
    # - if model has predict_proba, use positive-class probability.
    # - apply config.PREDICTION_THRESHOLD.
    # - return one PredictionResponse per record.
    if hasattr(model, "predict_proba"):
        probabilities = np.asarray(model.predict_proba(X))[:, 1]
    elif hasattr(model, "decision_function"):
        raw_scores = model.decision_function(X)
        probabilities = 1 / (1 + np.exp(-raw_scores))
    else:
        probabilities = np.asarray(model.predict(X), dtype=float)

    predictions = (probabilities >= config.PREDICTION_THRESHOLD).astype(int)

    responses = []
    for prediction, probability in zip(predictions, probabilities):
        responses.append(
            PredictionResponse(
                prediction=int(prediction),
                prediction_label=config.POSITIVE_LABEL if int(prediction) == 1 else config.NEGATIVE_LABEL,
                probability=float(probability),
                threshold=config.PREDICTION_THRESHOLD,
            )
        )
    return responses
