"""Data transformation helpers for the medallion demo."""
from __future__ import annotations

from typing import Dict, List

import pandas as pd


def bronze_frame_from_records(records: pd.DataFrame) -> pd.DataFrame:
    """Normalize Airbyte JSONL payload into a typed Bronze DataFrame."""
    df = records.copy()
    if "_airbyte_data" in df.columns:
        df = df["_airbyte_data"].apply(pd.Series)
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["sales_total"] = df["sales_total"].astype(float)
    return df


def silver_frame(bronze_records: List[Dict[str, object]]) -> pd.DataFrame:
    """Filter and enrich Bronze records for the Silver layer."""
    df = pd.DataFrame(bronze_records)
    if df.empty:
        return df
    df["order_date"] = pd.to_datetime(df["order_date"])
    df = df[df["status"].isin(["shipped", "delivered", "processing"])]
    df["sales_total"] = df["sales_total"].astype(float)
    df["ingestion_date"] = pd.Timestamp.utcnow()
    return df.reset_index(drop=True)
