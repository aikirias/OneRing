import os
from functools import lru_cache

import mlflow
import numpy as np
import pandas as pd
import streamlit as st

TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000")
MODEL_NAME = os.environ.get("MLFLOW_MODEL_NAME", "oner_churn_model")
MODEL_STAGE = os.environ.get("STREAMLIT_MODEL_STAGE", os.environ.get("MLFLOW_MODEL_STAGE", "Staging"))


@lru_cache(maxsize=1)
def _load_model():
    mlflow.set_tracking_uri(TRACKING_URI)
    model_uri = f"models:/{MODEL_NAME}/{MODEL_STAGE}"
    return mlflow.pyfunc.load_model(model_uri)


def _score(payload):
    model = _load_model()
    frame = pd.DataFrame(payload)
    predictions = model.predict(frame)
    if isinstance(predictions, pd.DataFrame):
        probs = predictions[predictions.columns[-1]].to_numpy(dtype=float)
    else:
        probs = np.array(predictions, dtype=float).flatten()
    return probs.tolist()


st.set_page_config(page_title="Customer Churn Scorer", page_icon="🤖")
st.title("Customer Churn Mini-App")
st.write("Interactively score customers using the latest model registered in MLflow.")

with st.form("prediction_form"):
    total_transactions = st.slider("Total Transactions", min_value=0, max_value=150, value=20)
    total_spend = st.number_input("Total Spend", min_value=0.0, value=500.0, step=50.0)
    avg_transaction_value = st.number_input("Average Transaction Value", min_value=0.0, value=25.0, step=5.0)
    spend_last_30d = st.number_input("Spend in Last 30 Days", min_value=0.0, value=120.0, step=10.0)
    submitted = st.form_submit_button("Score Customer")

if submitted:
    record = {
        "total_transactions": total_transactions,
        "total_spend": total_spend,
        "avg_transaction_value": avg_transaction_value,
        "spend_last_30d": spend_last_30d,
    }
    try:
        scores = _score([record])
        probability = scores[0]
        label = int(probability >= 0.5)
        st.success(f"Predicted churn probability: {probability:.3f}")
        st.write("Predicted class:", "High risk" if label == 1 else "Low risk")
    except Exception as exc:  # noqa: BLE001
        st.error(f"Prediction failed: {exc}")
