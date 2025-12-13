# Platform Concept Glossary

This glossary expands on the less-common technologies bundled inside OneRing so that newcomers can connect the moving pieces without jumping between README sections. Each entry calls out where the concept shows up in this repository.

## Medallion Data Architecture
- **What it is**: A layered pattern (Bronze → Silver → Gold) popularised by the Databricks Lakehouse for gradually refining ingested data.
- **How OneRing uses it**: Bronze landings (raw JSONL) sit under `storage/medallion/bronze` on Ceph RGW, Silver aggregations are materialised into ClickHouse (`analytics.orders_clean`), and the Gold snapshot for consumers lives in Postgres (`gold.orders_snapshot`).
- **Where to look**: `platform/orchestration/airflow/dags/medallion_batch.py` encodes the canonical DAG and shows how Great Expectations checkpoints gate each hop.

## Ceph RGW & Iceberg REST Catalog
- **Ceph RGW**: Rook-Ceph’s Rados Gateway exposes an S3-compatible API, letting local environments emulate cloud object stores with proper access policies. The `.env` file seeds users/buckets such as `${CEPH_BUCKET_BRONZE}`, `${CEPH_BUCKET_SILVER}`, `${CEPH_BUCKET_GOLD}`, and the restricted `${CEPH_BUCKET_STAGE}`.
- **Iceberg REST Catalog**: Apache Iceberg’s REST service is deployed beside Ceph so metadata operations happen through REST instead of Hive Metastore. Spark, Flink, and Trino sessions point to `http://iceberg-rest:8181` using the `rest` catalog type, while data files sit in `${CEPH_BUCKET_ICEBERG}`.
- **Why it matters**: The combo mirrors production-grade lakehouse stacks that rely on cloud object storage plus table format catalogs to guarantee ACID semantics for large analytics tables.

## Apache Pulsar & Debezium
- **Apache Pulsar**: A multi-tenant messaging system with tiered storage; here it powers the `streaming` profile for CDC and event-driven demos. Configuration lives in `platform/streaming/pulsar` with helper scripts inside `ops/scripts/bootstrap.sh`.
- **Debezium Server**: Streams logical replication changes from external Postgres sources directly into Pulsar topics declared by `${DEBEZIUM_PULSAR_TOPIC}` (the demo version points at the curated database to stay self-contained). The Debezium server definition is under `platform/streaming/debezium`.
- **Key workflow**: Debezium draws the CDC boundary, Flink jobs consume the resulting topics, and they decide whether to fan out enriched events to new Pulsar topics or persist them into Ceph Bronze for downstream batch layers.

## Feast Feature Store
- **Role**: Provides reusable feature views, historical retrieval, and a Redis online store for serving features with low latency.
- **Implementation**: The repository in `platform/featurestore/feast_repo/` defines entities, data sources, and feature views backed by Spark jobs that materialise features from the Ceph Bronze/Silver layers.
- **Storage**: Historical sources now live in Ceph (`s3://${CEPH_BUCKET_FEATURESTORE}/featurestore/...`), and `ops/scripts/seed_ceph.py` refreshes the default CSV so your local cluster reads/write directly against the bucket used for ML workloads.
- **Integration path**: The Airflow DAG `feast_spark_ml_pipeline.py` applies Feast objects, builds training datasets, and logs experiments to MLflow, so a single workflow handles both feature management and model experimentation.

## MLflow Tracking & Hyperopt Search
- **MLflow**: Tracks experiments, artifacts, and registered models. In this stack it runs with a Postgres backend and saves models/artifacts inside Ceph.
- **Hyperopt**: A Bayesian optimisation library that tunes Spark ML pipeline hyperparameters during DAG execution (`platform/ml/training/train.py`). Search results are written back to MLflow runs, so you get automatic tracking of winning parameter sets.
- **Takeaway**: Hyperopt is less common in turnkey stacks; the docs in `docs/architecture.md` describe the flow, and this glossary clarifies that you do not need to manage separate orchestration—the DAG controls Hyperopt loops inside Spark executors.

## Evidently Drift Reports
- **Purpose**: Continuous data quality monitoring for ML features, with HTML reports that quantify data drift.
- **Usage in repo**: The `evidently_drift_report.py` DAG compares the latest feature batch with reference distributions and drops HTML artifacts into `storage/data/ml/reports/`.
- **Why it’s notable**: Evidently is not bundled into most demo stacks, so the repo demonstrates how to operationalise it alongside MLflow/Feast to close the monitoring loop.

## Infisical Secrets Management
- **What it is**: An open-source secrets manager enabling workspace-based vaulting with end-to-end encryption.
- **How it’s wired**: Optional profile under `platform/security/infisical`; `ops/scripts/infisical_seed.sh` can bootstrap workspaces, environments, and secrets using the `.env` values `INFISICAL_*`.
- **Operational notes**: Even when Infisical is off, `.env` remains the source of truth. Turning it on lets you replace plaintext env files with dynamic secret injection for Airflow, Airbyte, or any Compose service.

## oauth2-proxy Frontends with Keycloak
- **Problem solved**: Airflow, Airbyte, and MLflow UIs normally run without auth in local demos. Here, each sits behind an `oauth2-proxy` container that delegates login to Keycloak, unifying RBAC.
- **Configuration**: Secrets such as `AIRFLOW_OIDC_CLIENT_SECRET` live in `.env`. Keycloak’s realm export (`platform/security/keycloak/realms/oner-realm.json`) preloads clients/groups so enabling the `security` profile instantly applies fine-grained access.
- **Best practice**: Rotate all seeded credentials when you clone the repo; the proxies make it straightforward to test how enterprise SSO would feel without hosting extra infrastructure.

## Liquibase for Postgres & ClickHouse
- **Reasoning**: Schema versioning in analytics sandboxes is often ad-hoc. Liquibase changelogs under `platform/versioning/liquibase/changelogs/{postgres,clickhouse}` enforce controlled evolution for both the curated warehouse and the ClickHouse mart.
- **Execution**: `make bootstrap` runs targeted Liquibase jobs automatically; advanced users can re-run the CLI commands documented in `README.md` (Schema Versioning section) to test migrations independently.

## When to Use What
- **Bronze ingestion**: Airbyte + Ceph for self-service sources, with Spark pipelines reserved for core data engineers onboarding contractual/vendor deliveries.
- **Streaming ingest**: Flink consumes Pulsar topics (CDC via Debezium or other events) and writes enriched records to downstream topics or directly into Ceph's Bronze zone.
- **Transformation/validation**: Airflow orchestrates Spark/Great Expectations tasks over the Iceberg-backed medallion zones; dbt (`platform/analytics/dbt`) publishes analyst-facing marts inside ClickHouse.
- **Serving and BI**: Metabase (ClickHouse) for ad-hoc dashboards, Trino for federated SQL exploration, Streamlit mini-app for ML model scoring.
- **Transactional streaming**: Postgres, Debezium, and Flink handle CDC + microservice workloads; keep analytical queries on ClickHouse/Iceberg to avoid noisy-neighbor issues.
- **Security & ops**: Keycloak + oauth2-proxy for IAM, Infisical for secrets, Jenkins for CI/CD automation, Grafana + Prometheus + OpenMetadata for observability/collaboration signals.

Use this document alongside `README.md` and `docs/architecture.md` whenever you encounter a component that is not mainstream in every data platform—each section points to the code paths that implement the concept locally.
