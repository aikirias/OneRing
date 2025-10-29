"""BentoML service loading the latest model from MLflow registry."""
from __future__ import annotations

import os
from typing import List

import mlflow
import numpy as np
import pandas as pd
from bentoml import Service, api
from bentoml.io import JSON

FEATURE_COLUMNS = [
    "total_transactions",
    "total_spend",
    "avg_transaction_value",
    "spend_last_30d",
]


def _load_model():
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI", "http://mlflow:5000")
    mlflow.set_tracking_uri(tracking_uri)
    model_name = os.environ.get("BENTO_MODEL_NAME", os.environ.get("MLFLOW_MODEL_NAME", "oner_churn_model"))
    stage = os.environ.get("BENTO_MODEL_STAGE", "Staging")
    model_uri = f"models:/{model_name}/{stage}"
    return mlflow.pyfunc.load_model(model_uri)


REFRESH_FLAG = os.path.join(os.environ.get("BENTOML_HOME", "/home/bento/bentoml"), "refresh.signal")
_MODEL_CACHE: dict[str, float | object] = {"model": _load_model(), "timestamp": 0.0}


def _get_model():
    refresh_timestamp = 0.0
    if os.path.exists(REFRESH_FLAG):
        refresh_timestamp = os.path.getmtime(REFRESH_FLAG)
    if refresh_timestamp > _MODEL_CACHE["timestamp"]:
        _MODEL_CACHE["model"] = _load_model()
        _MODEL_CACHE["timestamp"] = refresh_timestamp
    return _MODEL_CACHE["model"]


svc = Service("oner_model_service")


@svc.api(input=JSON(), output=JSON())
def predict(payload: dict) -> dict:
    model = _get_model()
    if isinstance(payload, dict) and "instances" in payload:
        records: List[dict] = payload["instances"]
    else:
        records = [payload]
    frame = pd.DataFrame(records)
    frame = frame.reindex(columns=FEATURE_COLUMNS).fillna(0.0)
    predictions = model.predict(frame)
    if isinstance(predictions, pd.DataFrame):
        scores = predictions.get("probability")
        if scores is None:
            scores = predictions.get("prediction")
        probs = scores if scores is not None else predictions.iloc[:, 0]
        probs = np.array([float(p[-1] if isinstance(p, (list, tuple, np.ndarray)) else p) for p in probs])
    else:
        probs = np.array(predictions, dtype=float)
    return {
        "predictions": probs.tolist(),
        "classes": [int(p >= 0.5) for p in probs],
    }
