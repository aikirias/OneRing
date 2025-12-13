#!/usr/bin/env python3
"""Upload sample CSV data to the Ceph RGW buckets for demo purposes."""
import os
import sys
from pathlib import Path

import boto3
from botocore.client import Config

CEPH_ENDPOINT = os.getenv("CEPH_RGW_ENDPOINT", "http://localhost:9000")
ACCESS_KEY = os.getenv("CEPH_ACCESS_KEY", "cephadmin")
SECRET_KEY = os.getenv("CEPH_SECRET_KEY", "cephpass")
BRONZE_BUCKET = os.getenv("CEPH_BUCKET_BRONZE", "bronze")
FEATURESTORE_BUCKET = os.getenv("CEPH_BUCKET_FEATURESTORE", BRONZE_BUCKET)
REGION = os.getenv("CEPH_REGION", "us-east-1")
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SAMPLE = ROOT / "platform" / "storage" / "postgres" / "seeds" / "orders_raw.csv"
FILE_PATH = Path(os.getenv("BRONZE_SAMPLE_FILE", str(DEFAULT_SAMPLE)))
OBJECT_KEY = os.getenv("BRONZE_OBJECT_KEY", "airbyte/orders/orders_raw.csv")
DEFAULT_FEAST_SAMPLE = ROOT / "platform" / "featurestore" / "feast_repo" / "data" / "customer_transactions.csv"
FEAST_SAMPLE = Path(os.getenv("FEAST_SAMPLE_FILE", str(DEFAULT_FEAST_SAMPLE)))
FEAST_OBJECT_KEY = os.getenv("FEAST_OBJECT_KEY", "featurestore/customer_transactions.csv")


def _upload_file(client, *, path: Path, bucket: str, key: str, label: str) -> None:
    if not path.exists():
        print(f"{label} not found: {path}", file=sys.stderr)
        sys.exit(1)
    with path.open("rb") as handle:
        client.upload_fileobj(handle, bucket, key)
    print(f"Uploaded {label} ({path}) to s3://{bucket}/{key}")


def main() -> None:
    session = boto3.session.Session()
    client = session.client(
        "s3",
        endpoint_url=CEPH_ENDPOINT,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name=REGION,
    )
    _upload_file(
        client,
        path=FILE_PATH,
        bucket=BRONZE_BUCKET,
        key=OBJECT_KEY,
        label="Bronze sample data",
    )
    _upload_file(
        client,
        path=FEAST_SAMPLE,
        bucket=FEATURESTORE_BUCKET,
        key=FEAST_OBJECT_KEY,
        label="Feast feature sample",
    )


if __name__ == "__main__":
    main()
