#!/usr/bin/env python3
"""Upload sample CSV data to MinIO Bronze bucket for demo purposes."""
import os
import sys
from pathlib import Path

import boto3
from botocore.client import Config

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "minioadmin")
SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
BRONZE_BUCKET = os.getenv("MINIO_BUCKET_BRONZE", "bronze")
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SAMPLE = ROOT / "platform" / "storage" / "postgres" / "seeds" / "orders_raw.csv"
FILE_PATH = Path(os.getenv("BRONZE_SAMPLE_FILE", str(DEFAULT_SAMPLE)))
OBJECT_KEY = os.getenv("BRONZE_OBJECT_KEY", "airbyte/orders/orders_raw.csv")


def main() -> None:
    if not FILE_PATH.exists():
        print(f"Sample file not found: {FILE_PATH}", file=sys.stderr)
        sys.exit(1)
    session = boto3.session.Session()
    client = session.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )
    with FILE_PATH.open("rb") as handle:
        client.upload_fileobj(handle, BRONZE_BUCKET, OBJECT_KEY)
    print(f"Uploaded {FILE_PATH} to s3://{BRONZE_BUCKET}/{OBJECT_KEY}")


if __name__ == "__main__":
    main()
