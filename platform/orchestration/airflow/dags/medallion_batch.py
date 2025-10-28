"""Demo medallion DAG orchestrating Bronze -> Silver -> Gold pipeline."""
from __future__ import annotations

import io
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

import boto3
import pandas as pd
import psycopg2
import requests
from include.transformations import bronze_frame_from_records, silver_frame
from airflow.decorators import dag, task
from airflow.hooks.base import BaseHook
from great_expectations.core.batch import RuntimeBatchRequest
from great_expectations.data_context import get_context
from clickhouse_driver import Client as ClickHouseClient


def _airbyte_api_base() -> str:
    conn = BaseHook.get_connection("airbyte_api")
    base = f"{conn.schema or 'http'}://{conn.host}:{conn.port}"
    extra = conn.extra_dejson
    endpoint = extra.get("endpoint") if isinstance(extra, dict) else None
    if endpoint:
        base = f"{base}/{endpoint.strip('/') }"
    return base.rstrip("/")

def _airbyte_workspace_id() -> str:
    base = _airbyte_api_base()
    response = requests.post(f"{base}/v1/workspaces/list", json={}, timeout=30)
    response.raise_for_status()
    workspaces = response.json().get("workspaces", [])
    if not workspaces:
        raise RuntimeError("No Airbyte workspaces available")
    return workspaces[0]["workspaceId"]


def _airbyte_connection_id() -> str:
    base = _airbyte_api_base()
    workspace_id = _airbyte_workspace_id()
    payload = {"workspaceId": workspace_id}
    response = requests.post(f"{base}/v1/connections/list", json=payload, timeout=30)
    response.raise_for_status()
    name = os.getenv("AIRBYTE_DEMO_CONNECTION", "Faker Orders to Bronze")
    for connection in response.json().get("connections", []):
        if connection.get("name") == name:
            return connection.get("connectionId")
    raise RuntimeError(f"Airbyte connection '{name}' not found")



def _boto_client() -> boto3.client:
    conn = BaseHook.get_connection("minio_default")
    extra = conn.extra_dejson or {}
    return boto3.client(
        "s3",
        endpoint_url=extra.get("endpoint_url", os.getenv("MINIO_ENDPOINT", "http://minio:9000")),
        aws_access_key_id=conn.login,
        aws_secret_access_key=conn.password,
        region_name=extra.get("region_name", "us-east-1"),
    )


def _clickhouse_client() -> ClickHouseClient:
    conn = BaseHook.get_connection("clickhouse_default")
    return ClickHouseClient(
        host=conn.host,
        port=conn.port or 8123,
        user=conn.login,
        password=conn.password,
        database=conn.schema or "analytics",
        secure=conn.extra_dejson.get("secure", False) if conn.extra else False,
    )


def _postgres_conn_info() -> Dict[str, Any]:
    conn = BaseHook.get_connection("postgres_curated")
    return {
        "dbname": conn.schema or "curated",
        "user": conn.login,
        "password": conn.password,
        "host": conn.host,
        "port": conn.port or 5432,
    }


def _ge_context():
    return get_context(context_root_dir="/opt/great_expectations")


def _run_checkpoint(suite_name: str, dataframe: pd.DataFrame, batch_id: str) -> None:
    context = _ge_context()
    batch_request = RuntimeBatchRequest(
        datasource_name="runtime_pandas",
        data_connector_name="runtime_data_connector",
        data_asset_name="orders",
        runtime_parameters={"batch_data": dataframe},
        batch_identifiers={"batch_id": batch_id},
    )
    result = context.run_checkpoint(
        checkpoint_name="orders_checkpoint",
        validations=[
            {
                "batch_request": batch_request,
                "expectation_suite_name": suite_name,
            }
        ],
    )
    if not result.success:
        raise ValueError(f"Great Expectations checkpoint failed for {suite_name}")


@dag(
    dag_id="medallion_batch_demo",
    schedule=None,
    catchup=False,
    start_date=datetime(2024, 1, 1),
    default_args={"owner": "data-platform", "retries": 1, "retry_delay": timedelta(minutes=5)},
    tags=["medallion", "demo", "batch"],
)
def medallion_batch_demo() -> None:
    @task()
    def trigger_airbyte_sync() -> Dict[str, Any]:
        base = _airbyte_api_base()
        logging.info("Triggering Airbyte sync via %s", base)
        connection_id = _airbyte_connection_id()
        response = requests.post(f"{base}/v1/connections/sync", json={"connectionId": connection_id}, timeout=30)
        response.raise_for_status()
        payload = response.json()
        job = payload.get("job") or {}
        job_id = job.get("id")
        if not job_id:
            raise RuntimeError(f"Airbyte response missing job id: {payload}")
        return {"job_id": job_id}

    @task(retries=5, retry_delay=timedelta(minutes=1))
    def wait_for_airbyte(job: Dict[str, Any]) -> Dict[str, Any]:
        base = _airbyte_api_base()
        job_id = job["job_id"]
        status = ""
        while status not in {"succeeded", "failed", "cancelled"}:
            response = requests.post(f"{base}/v1/jobs/get", json={"id": job_id}, timeout=30)
            response.raise_for_status()
            body = response.json()
            status = body.get("job", {}).get("status", "unknown")
            logging.info("Airbyte job %s status: %s", job_id, status)
            if status in {"succeeded", "failed", "cancelled"}:
                if status != "succeeded":
                    raise RuntimeError(f"Airbyte job {job_id} finished with status {status}")
                return body
            time.sleep(15)
        return body

    @task()
    def pull_bronze_objects(_: Dict[str, Any]) -> List[Dict[str, Any]]:
        bucket = os.getenv("MINIO_BUCKET_BRONZE", "bronze")
        prefix = os.getenv("AIRBYTE_BRONZE_PREFIX", "airbyte")
        client = _boto_client()
        paginator = client.get_paginator("list_objects_v2")
        latest = None
        latest_obj = None
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                if latest is None or obj["LastModified"] > latest:
                    latest = obj["LastModified"]
                    latest_obj = obj
        if not latest_obj:
            raise FileNotFoundError(f"No objects found in s3://{bucket}/{prefix}")
        s3_obj = client.get_object(Bucket=bucket, Key=latest_obj["Key"])
        raw_bytes = s3_obj["Body"].read()
        df = pd.read_json(io.BytesIO(raw_bytes), lines=True)
        bronze_df = bronze_frame_from_records(df)
        _run_checkpoint("orders_bronze", bronze_df, batch_id="bronze")
        return bronze_df.to_dict(orient="records")

    @task()
    def transform_to_silver(bronze_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        df = silver_frame(bronze_records)
        _run_checkpoint("orders_silver", df, batch_id="silver")
        return df.to_dict(orient="records")

    @task()
    def load_silver_clickhouse(records: List[Dict[str, Any]]) -> str:
        client = _clickhouse_client()
        payload = [
            (
                rec.get("order_id"),
                rec.get("order_date"),
                rec.get("customer_id"),
                rec.get("status"),
                float(rec.get("sales_total", 0)),
                rec.get("ingestion_date"),
            )
            for rec in records
        ]
        client.execute("TRUNCATE TABLE IF EXISTS analytics.orders_clean")
        client.execute(
            "INSERT INTO analytics.orders_clean (order_id, order_date, customer_id, status, sales_total, ingestion_date) VALUES",
            payload,
            types_check=True,
        )
        return "analytics.orders_clean"

    @task()
    def publish_gold(_: str) -> int:
        client = _clickhouse_client()
        rows = client.execute(
            "SELECT order_id, order_date, customer_id, status, sales_total, ingestion_date FROM analytics.orders_clean"
        )
        if not rows:
            logging.warning("No rows found in analytics.orders_clean")
            return 0
        connection = psycopg2.connect(**_postgres_conn_info())
        cursor = connection.cursor()
        upsert_sql = (
            "INSERT INTO gold.orders_snapshot (order_id, order_date, customer_id, sales_total, status, ingested_at)"
            " VALUES (%s, %s, %s, %s, %s, %s)"
            " ON CONFLICT (order_id) DO UPDATE SET order_date = EXCLUDED.order_date,"
            " customer_id = EXCLUDED.customer_id, sales_total = EXCLUDED.sales_total,"
            " status = EXCLUDED.status, ingested_at = EXCLUDED.ingested_at"
        )
        cursor.executemany(upsert_sql, rows)
        affected = cursor.rowcount
        connection.commit()
        cursor.close()
        connection.close()
        return affected

    @task()
    def notify_lineage(rows_upserted: int) -> None:
        logging.info("Gold layer updated with %s records", rows_upserted)

    job = trigger_airbyte_sync()
    airbyte_result = wait_for_airbyte(job)
    bronze_records = pull_bronze_objects(airbyte_result)
    silver_records = transform_to_silver(bronze_records)
    silver_table = load_silver_clickhouse(silver_records)
    upsert_count = publish_gold(silver_table)
    notify_lineage(upsert_count)


medallion_batch_demo()
