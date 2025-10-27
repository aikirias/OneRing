import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT / "platform" / "orchestration"))

from airflow.include.transformations import bronze_frame_from_records, silver_frame


def test_bronze_frame_normalizes_types():
    df = pd.DataFrame([
        {
            "_airbyte_data": {
                "order_id": "1001",
                "order_date": "2024-01-01",
                "customer_id": "ACME",
                "status": "shipped",
                "sales_total": "120.5",
            }
        }
    ])

    bronze = bronze_frame_from_records(df)

    assert list(bronze.columns) == ["order_id", "order_date", "customer_id", "status", "sales_total"]
    assert pd.api.types.is_datetime64_any_dtype(bronze["order_date"])
    assert pd.api.types.is_float_dtype(bronze["sales_total"])


def test_silver_frame_filters_invalid_status():
    records = [
        {
            "order_id": "ok",
            "order_date": "2024-01-01",
            "customer_id": "ACME",
            "status": "shipped",
            "sales_total": 10,
        },
        {
            "order_id": "drop",
            "order_date": "2024-01-02",
            "customer_id": "BAD",
            "status": "cancelled",
            "sales_total": 5,
        },
    ]

    silver = silver_frame(records)

    assert len(silver) == 1
    assert silver.iloc[0]["order_id"] == "ok"
    assert "ingestion_date" in silver.columns
