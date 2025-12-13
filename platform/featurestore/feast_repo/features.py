"""Feast feature repository for customer churn demo."""
import os
from datetime import timedelta

from feast import Entity, FeatureService, FeatureView, Field
from feast.data_source import FileSource, FileFormat
from feast.types import Float32, Int64

CEPH_ENDPOINT = os.getenv("CEPH_RGW_ENDPOINT", "http://ceph:9000")
FEATURESTORE_BUCKET = os.getenv("CEPH_BUCKET_FEATURESTORE", os.getenv("CEPH_BUCKET_BRONZE", "bronze"))
FEATURESTORE_OBJECT_KEY = os.getenv(
    "FEAST_OBJECT_KEY", os.getenv("FEAST_FEATURESTORE_OBJECT_KEY", "featurestore/customer_transactions.csv")
)
FEATURESTORE_SOURCE_URI = os.getenv(
    "FEAST_SOURCE_URI", f"s3://{FEATURESTORE_BUCKET}/{FEATURESTORE_OBJECT_KEY}"
)

customer = Entity(name="customer_id", join_keys=["customer_id"], description="Unique customer identifier")

customer_transactions_source = FileSource(
    name="customer_transactions_source",
    path=FEATURESTORE_SOURCE_URI,
    timestamp_field="event_timestamp",
    created_timestamp_column="created_at",
    file_format=FileFormat.CSV,
    s3_endpoint_override=CEPH_ENDPOINT,
)

customer_features_view = FeatureView(
    name="customer_features",
    entities=[customer],
    ttl=timedelta(days=1),
    schema=[
        Field(name="total_transactions", dtype=Int64),
        Field(name="total_spend", dtype=Float32),
        Field(name="avg_transaction_value", dtype=Float32),
        Field(name="spend_last_30d", dtype=Float32),
    ],
    online=True,
    source=customer_transactions_source,
    tags={"owner": "ml-platform", "usage": "training"},
)

customer_feature_service = FeatureService(
    name="customer_feature_service",
    features=[customer_features_view],
)
