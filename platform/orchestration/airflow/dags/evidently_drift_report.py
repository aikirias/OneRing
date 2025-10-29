"""Daily Evidently drift report DAG."""
from __future__ import annotations

import os
from datetime import datetime

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from evidently.metric_preset import DataDriftPreset
from evidently.report import Report


def generate_drift_report(**_):
    data_root = os.environ.get("FEAST_REFERENCE_DATA_PATH", "/opt/airflow/storage/data/ml")
    baseline_path = os.path.join(data_root, "outputs", "training_dataset.parquet")
    if not os.path.exists(baseline_path):
        # fallback to initial csv if training set not generated yet
        baseline_path = os.path.join(data_root, "customer_transactions.csv")
        reference = pd.read_csv(baseline_path)
    else:
        reference = pd.read_parquet(baseline_path)

    current_path = os.path.join(data_root, "customer_transactions.csv")
    current = pd.read_csv(current_path)

    report = Report(metrics=[DataDriftPreset()])
    report.run(reference_data=reference, current_data=current)

    output_dir = os.path.join(data_root, "reports")
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(output_dir, f"evidently_data_drift_{timestamp}.html")
    report.save_html(report_path)
    return report_path


def create_dag() -> DAG:
    with DAG(
        dag_id="evidently_drift_report",
        description="Generate daily data drift report with Evidently",
        start_date=datetime(2024, 1, 1),
        schedule="@daily",
        catchup=False,
        tags=["monitoring", "ml"],
    ) as dag:
        PythonOperator(task_id="generate_report", python_callable=generate_drift_report)
    return dag


globals()["evidently_drift_report"] = create_dag()
