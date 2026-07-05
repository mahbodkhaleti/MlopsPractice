from __future__ import annotations

import os
from contextlib import asynccontextmanager

import mlflow
import mlflow.sklearn
import joblib
from pathlib import Path
from fastapi import FastAPI, HTTPException

from .predictor import predict_batch, predict_single
from .schema import ListingFeatures, PredictionResponse

_model = None
_model_run_id = ""


def load_serving_model(model_uri: str):
    local_model = Path(os.getenv("LOCAL_MODEL_PATH", "artifacts/hw02_model/pipeline.joblib"))
    if local_model.exists():
        return joblib.load(local_model)
    try:
        return mlflow.sklearn.load_model(model_uri)
    except Exception:
        artifact_path = Path(mlflow.artifacts.download_artifacts(artifact_uri=model_uri))
        joblib_candidates = list(artifact_path.rglob("*.joblib"))
        if not joblib_candidates:
            raise
        return joblib.load(joblib_candidates[0])


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _model, _model_run_id
    _model_run_id = os.environ["MODEL_RUN_ID"]
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://185.50.38.163:33014"))
    if os.getenv("MLFLOW_TRACKING_USERNAME"):
        os.environ["MLFLOW_TRACKING_USERNAME"] = os.getenv("MLFLOW_TRACKING_USERNAME", "")
    if os.getenv("MLFLOW_TRACKING_PASSWORD"):
        os.environ["MLFLOW_TRACKING_PASSWORD"] = os.getenv("MLFLOW_TRACKING_PASSWORD", "")
    _model = load_serving_model(f"runs:/{_model_run_id}/model")
    yield
    _model = None


app = FastAPI(title="QBC12 Airbnb Serving", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "model_run_id": _model_run_id}


@app.post("/predict", response_model=PredictionResponse)
def predict(features: ListingFeatures) -> PredictionResponse:
    if _model is None:
        raise HTTPException(status_code=503, detail="model not loaded")
    return predict_single(features, _model, _model_run_id)


@app.post("/predict/batch", response_model=list[PredictionResponse])
def batch(features: list[ListingFeatures]) -> list[PredictionResponse]:
    if _model is None:
        raise HTTPException(status_code=503, detail="model not loaded")
    if not features:
        raise HTTPException(status_code=422, detail="batch must not be empty")
    return predict_batch(features, _model, _model_run_id)
