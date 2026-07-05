from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import os

import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient

from . import config


@dataclass
class LoadedModelState:
    model: Any = None
    loaded: bool = False
    error: Optional[str] = None
    model_uri: Optional[str] = None
    run_id: Optional[str] = None
    run_name: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    params: Dict[str, Any] = field(default_factory=dict)
    tags: Dict[str, Any] = field(default_factory=dict)


class ModelService:
    """TODO: Load the HW02 model from MLflow.

    Required behavior:
    - Use MLFLOW_TRACKING_URI, MLFLOW_TRACKING_USERNAME, and MLFLOW_TRACKING_PASSWORD.
    - If MLFLOW_RUN_ID is set, load runs:/<run_id>/model.
    - Otherwise auto-select a clean/selected run from MLFLOW_EXPERIMENT_NAME.
    - Do not crash the API on startup. Store the error in self.state.error.
    """

    def __init__(self) -> None:
        self.state = LoadedModelState()

    def load(self) -> None:
        # TODO: Replace this placeholder with real MLflow loading.
        # Hint:
        #   os.environ["MLFLOW_TRACKING_USERNAME"] = config.MLFLOW_TRACKING_USERNAME
        #   os.environ["MLFLOW_TRACKING_PASSWORD"] = config.MLFLOW_TRACKING_PASSWORD
        #   mlflow.set_tracking_uri(config.MLFLOW_TRACKING_URI)
        #   model = mlflow.sklearn.load_model(f"runs:/{config.MLFLOW_RUN_ID}/model")
        self.state = LoadedModelState()

        try:
            if config.MLFLOW_TRACKING_USERNAME:
                os.environ["MLFLOW_TRACKING_USERNAME"] = config.MLFLOW_TRACKING_USERNAME
            if config.MLFLOW_TRACKING_PASSWORD:
                os.environ["MLFLOW_TRACKING_PASSWORD"] = config.MLFLOW_TRACKING_PASSWORD

            mlflow.set_tracking_uri(config.MLFLOW_TRACKING_URI)
            client = MlflowClient()

            run_id = config.MLFLOW_RUN_ID or self._select_run_id(client)
            model_uri = f"runs:/{run_id}/model"
            model = mlflow.sklearn.load_model(model_uri)
            run = client.get_run(run_id)

            self.state = LoadedModelState(
                model=model,
                loaded=True,
                error=None,
                model_uri=model_uri,
                run_id=run_id,
                run_name=run.data.tags.get("mlflow.runName"),
                metrics=dict(run.data.metrics),
                params=dict(run.data.params),
                tags=dict(run.data.tags),
            )
        except Exception as exc:
            self.state.loaded = False
            self.state.error = str(exc)

    def _select_run_id(self, client: MlflowClient) -> str:
        experiment = client.get_experiment_by_name(config.MLFLOW_EXPERIMENT_NAME)
        if experiment is None:
            raise ValueError(f"MLflow experiment not found: {config.MLFLOW_EXPERIMENT_NAME}")

        selected_runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            filter_string="tags.selected_for_serving = 'true'",
            order_by=["metrics.test_f1 DESC"],
            max_results=1,
        )
        if selected_runs:
            return selected_runs[0].info.run_id

        clean_runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            filter_string="tags.uses_leakage != 'true'",
            order_by=["metrics.test_f1 DESC"],
            max_results=1,
        )
        if clean_runs:
            return clean_runs[0].info.run_id

        any_runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            order_by=["start_time DESC"],
            max_results=1,
        )
        if any_runs:
            return any_runs[0].info.run_id

        raise ValueError(f"No MLflow runs found in experiment: {config.MLFLOW_EXPERIMENT_NAME}")

    def require_model(self):
        if not self.state.loaded or self.state.model is None:
            raise RuntimeError(self.state.error or "Model is not loaded.")
        return self.state.model

    def model_info(self) -> dict:
        return {
            "model_loaded": self.state.loaded,
            "tracking_uri": config.MLFLOW_TRACKING_URI,
            "experiment_name": config.MLFLOW_EXPERIMENT_NAME,
            "model_uri": self.state.model_uri,
            "run_id": self.state.run_id,
            "run_name": self.state.run_name,
            "dataset_version": config.DATASET_VERSION,
            "target": config.TARGET_NAME,
            "threshold": config.PREDICTION_THRESHOLD,
            "metrics": self.state.metrics,
            "params": self.state.params,
            "tags": self.state.tags,
            "error": self.state.error,
        }
