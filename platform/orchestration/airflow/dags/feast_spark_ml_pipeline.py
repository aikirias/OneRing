"""Airflow DAG orchestrating Feast feature pipeline and Spark ML training with MLflow."""
from __future__ import annotations

import os
import sys
import subprocess
from datetime import datetime, timedelta

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from feast import FeatureStore

sys.path.append("/opt/airflow/platform")
from ml.training.train_pipeline import run_hyperopt_training

FEAST_FEATURES = [
    "customer_features:total_transactions",
    "customer_features:total_spend",
    "customer_features:avg_transaction_value",
    "customer_features:spend_last_30d",
]


def _repo_path() -> str:
    return os.environ.get("FEAST_REPO_PATH", "/opt/airflow/feast_repo")


def feast_apply(**_):
    subprocess.run(["feast", "apply"], cwd=_repo_path(), check=True)


def feast_materialize(**_):
    target = datetime.utcnow().isoformat()
    subprocess.run(["feast", "materialize-incremental", target], cwd=_repo_path(), check=True)


def generate_training_dataset(**_):
    repo_path = _repo_path()
    store = FeatureStore(repo_path)
    data_root = os.environ.get("FEAST_REFERENCE_DATA_PATH", "/opt/airflow/storage/data/ml")
    source_path = os.path.join(data_root, "customer_transactions.csv")
    entity_df = pd.read_csv(source_path)[["customer_id", "event_timestamp", "churned"]]
    entity_df["event_timestamp"] = pd.to_datetime(entity_df["event_timestamp"])
    historical = store.get_historical_features(features=FEAST_FEATURES, entity_df=entity_df)
    training_df = historical.to_df()
    training_df["label"] = entity_df["churned"].values
    output_dir = os.path.join(data_root, "outputs")
    os.makedirs(output_dir, exist_ok=True)
    training_path = os.path.join(output_dir, "training_dataset.parquet")
    training_df.to_parquet(training_path, index=False)
    return training_path


def train_spark_model(**context):
    data_root = os.environ.get("FEAST_REFERENCE_DATA_PATH", "/opt/airflow/storage/data/ml")
    outputs_dir = os.path.join(data_root, "outputs")
    os.makedirs(outputs_dir, exist_ok=True)
    csv_path = os.path.join(data_root, "customer_transactions.csv")
    experiment_name = "customer_churn_experiment"
    model_name = os.environ.get("MLFLOW_MODEL_NAME", "oner_churn_model")
    run_id = run_hyperopt_training(csv_path, experiment_name, model_name)
    context["ti"].xcom_push(key="model_name", value=model_name)
    context["ti"].xcom_push(key="best_run_id", value=run_id)


def build_bento(**context):
    model_name = context["ti"].xcom_pull(task_ids="spark_train_model", key="model_name")
    service_dir = "/opt/airflow/platform/ml/bento_service"
    env = os.environ.copy()
    env.setdefault("BENTO_MODEL_NAME", model_name or env.get("MLFLOW_MODEL_NAME", "oner_churn_model"))
    subprocess.run(["bentoml", "build"], cwd=service_dir, env=env, check=True)


def refresh_bento_server(**_):
    # trigger reload by touching a file Bento watches
    signal_file = "/home/airflow/bentoml/refresh.signal"
    os.makedirs(os.path.dirname(signal_file), exist_ok=True)
    with open(signal_file, "w", encoding="utf-8") as fp:
        fp.write(datetime.utcnow().isoformat())


def create_dag() -> DAG:
    default_args = {
        "owner": "ml-platform",
        "depends_on_past": False,
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    }

    with DAG(
        dag_id="feast_spark_ml_pipeline",
        default_args=default_args,
        description="Feature engineering with Feast, Spark ML training with MLflow, and Bento packaging",
        start_date=datetime(2024, 1, 1),
        schedule=None,
        catchup=False,
    ) as dag:
        apply = PythonOperator(task_id="feast_apply", python_callable=feast_apply)
        materialize = PythonOperator(task_id="feast_materialize", python_callable=feast_materialize)
        export_dataset = PythonOperator(task_id="generate_training_dataset", python_callable=generate_training_dataset)
        train = PythonOperator(task_id="spark_train_model", python_callable=train_spark_model)
        build = PythonOperator(task_id="build_bento_bundle", python_callable=build_bento)
        notify = PythonOperator(task_id="refresh_bento", python_callable=refresh_bento_server)

        apply >> materialize >> export_dataset >> train >> build >> notify

    return dag


globals()["feast_spark_ml_pipeline"] = create_dag()
