#!/usr/bin/env python3
"""Create Airflow connections and variables after services are up."""
import json
import os
import subprocess
import sys
from pathlib import Path

ENV = {
    "MINIO_ROOT_USER": os.getenv("MINIO_ROOT_USER", "minioadmin"),
    "MINIO_ROOT_PASSWORD": os.getenv("MINIO_ROOT_PASSWORD", "minioadmin"),
    "CURATED_PG_USER": os.getenv("CURATED_PG_USER", "curated_user"),
    "CURATED_PG_PASSWORD": os.getenv("CURATED_PG_PASSWORD", "curatedpass"),
    "CLICKHOUSE_USER": os.getenv("CLICKHOUSE_USER", "default"),
    "CLICKHOUSE_PASSWORD": os.getenv("CLICKHOUSE_PASSWORD", "clickpass"),
    "MINIO_BUCKET_BRONZE": os.getenv("MINIO_BUCKET_BRONZE", "bronze"),
    "MINIO_BUCKET_SILVER": os.getenv("MINIO_BUCKET_SILVER", "silver"),
}

CONNECTIONS = [
    {
        "conn_id": "minio_default",
        "conn_type": "aws",
        "login": ENV["MINIO_ROOT_USER"],
        "password": ENV["MINIO_ROOT_PASSWORD"],
        "extra": json.dumps(
            {
                "endpoint_url": "http://minio:9000",
                "region_name": "us-east-1",
                "aws_access_key_id": ENV["MINIO_ROOT_USER"],
                "aws_secret_access_key": ENV["MINIO_ROOT_PASSWORD"],
            }
        ),
    },
    {
        "conn_id": "postgres_curated",
        "conn_type": "postgres",
        "host": "postgres",
        "schema": "curated",
        "login": ENV["CURATED_PG_USER"],
        "password": ENV["CURATED_PG_PASSWORD"],
        "port": 5432,
    },
    {
        "conn_id": "clickhouse_default",
        "conn_type": "clickhouse",
        "host": "clickhouse",
        "schema": "analytics",
        "login": ENV["CLICKHOUSE_USER"],
        "password": ENV["CLICKHOUSE_PASSWORD"],
        "port": 8123,
        "extra": json.dumps({"secure": False}),
    },
    {
        "conn_id": "airbyte_api",
        "conn_type": "http",
        "host": "airbyte-server",
        "schema": "http",
        "port": 8001,
        "extra": json.dumps({"endpoint": "api/v1"}),
    },
]

VARIABLES = {
    "bronze_bucket": ENV["MINIO_BUCKET_BRONZE"],
    "silver_bucket": ENV["MINIO_BUCKET_SILVER"],
    "gold_schema": "gold",
}

PYTHON_PAYLOAD = f"""
import json
from airflow import settings
from airflow.models import Connection, Variable

session = settings.Session()
try:
    for conn in {json.dumps(CONNECTIONS)}:
        existing = session.query(Connection).filter(Connection.conn_id == conn["conn_id"]).one_or_none()
        if existing:
            session.delete(existing)
            session.commit()
        new_conn = Connection(**{k: v for k, v in conn.items() if v is not None})
        session.add(new_conn)
        session.commit()
    for key, value in {json.dumps(VARIABLES)}.items():
        Variable.set(key, value, serialize_json=False)
finally:
    session.close()
"""


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    cmd = [
        "docker",
        "compose",
        "exec",
        "-T",
        "airflow-webserver",
        "python",
        "-c",
        PYTHON_PAYLOAD,
    ]
    subprocess.run(cmd, check=True, cwd=root)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print("Failed to provision Airflow connections", file=sys.stderr)
        sys.exit(exc.returncode)
