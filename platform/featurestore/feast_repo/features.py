"""Feast feature repository for customer churn demo."""
from datetime import timedelta

from feast import Entity, FeatureService, FeatureView, Field
from feast.data_source import FileSource, FileFormat
from feast.types import Float32, Int64

customer = Entity(name="customer_id", join_keys=["customer_id"], description="Unique customer identifier")

customer_transactions_source = FileSource(
    name="customer_transactions_source",
    path="data/customer_transactions.csv",
    timestamp_field="event_timestamp",
    created_timestamp_column="created_at",
    file_format=FileFormat.CSV,
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
