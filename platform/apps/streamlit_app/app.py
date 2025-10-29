import os
import requests
import streamlit as st

BENTO_ENDPOINT = os.environ.get("BENTO_ENDPOINT", "http://localhost:3001/predict")

st.set_page_config(page_title="Customer Churn Scorer", page_icon="🤖")
st.title("Customer Churn Mini-App")
st.write("Interactively score customers using the latest model served by BentoML.")

with st.form("prediction_form"):
    total_transactions = st.slider("Total Transactions", min_value=0, max_value=150, value=20)
    total_spend = st.number_input("Total Spend", min_value=0.0, value=500.0, step=50.0)
    avg_transaction_value = st.number_input("Average Transaction Value", min_value=0.0, value=25.0, step=5.0)
    spend_last_30d = st.number_input("Spend in Last 30 Days", min_value=0.0, value=120.0, step=10.0)
    submitted = st.form_submit_button("Score Customer")

if submitted:
    payload = {
        "instances": [
            {
                "total_transactions": total_transactions,
                "total_spend": total_spend,
                "avg_transaction_value": avg_transaction_value,
                "spend_last_30d": spend_last_30d,
            }
        ]
    }
    try:
        response = requests.post(BENTO_ENDPOINT, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()
        probability = result["predictions"][0]
        label = result["classes"][0]
        st.success(f"Predicted churn probability: {probability:.3f}")
        st.write("Predicted class:", "High risk" if label == 1 else "Low risk")
    except requests.RequestException as exc:
        st.error(f"Request failed: {exc}")
    except Exception as exc:  # noqa: BLE001
        st.error(f"Unexpected error: {exc}")
