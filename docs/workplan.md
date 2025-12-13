# Workplan Checklist

## Phase 1 – Foundations
- [x] Define folder structure for services and configs.
- [x] Create environment variable template (`.env.example`).
- [x] Document architecture overview and mermaid flow.

## Phase 2 – Infrastructure Configuration
- [x] Write `docker-compose.yml` with networks, volumes, dependencies.
- [x] Provide config templates for Airflow, Airbyte, Ceph RGW, OpenMetadata, Great Expectations, Grafana, Liquibase.
- [x] Add bootstrap scripts to automate setup tasks.

## Phase 3 – Data Pipelines & Quality
- [x] Implement Airflow DAGs for Bronze → Silver → Gold flow.
- [x] Configure Great Expectations suites and checkpoints.
- [x] Seed Liquibase changelogs for Postgres and ClickHouse.
- [x] Provision Spark & Flink clusters alongside ingestion services.

## Phase 4 – Catalog & Observability
- [x] Configure OpenMetadata ingestion pipelines.
- [x] Add Grafana dashboards and Prometheus exporters setup.
- [ ] Register metadata/lineage reporting hooks (replace the `notify_lineage` log stub in `medallion_batch.py` with a real OpenLineage/OpenMetadata emitter).

## Phase 5 – ML Feature & Model Lifecycle
- [x] Add Feast feature repository and sample data set (Ceph-backed offline store + Redis online store).
- [x] Wire Spark ML + Hyperopt training with MLflow tracking/registry.
- [x] Wire Streamlit scoring UI to load models directly from MLflow.
- [x] Generate Evidently drift reports via scheduled Airflow DAG.
- [ ] Document Feast/MLflow integration steps (Feast apply/materialize via Airflow, Redis online store expectations, MLflow usage).  # capture recent clarifications in README

## Phase 5b – Analytics & BI
- [x] Add Metabase service with ClickHouse driver automation.
- [x] Provide dedicated Make target/profile for ClickHouse + Metabase.
- [ ] Enforce analyst-only ClickHouse connectivity (docs mention Keycloak + oauth2-proxy but add verification task if needed).

## Phase 5c – Messaging & CI/CD
- [x] Integrate Apache Pulsar standalone broker with dedicated profile.
- [x] Add Jenkins LTS service with JCasC-ready mounts.

## Phase 6 – Documentation & Packaging
- [x] Complete README with end-to-end instructions and extensions.
- [x] Add sample data and Airbyte connection templates.
- [x] Add glossary for advanced concepts (Ceph RGW, Iceberg REST, Feast, Infisical, etc.) under `docs/concepts.md`.
- [x] Add Feast + Keycloak/oath2-proxy documentation details to README/architecture.
- [ ] Validate bootstrap (`make bootstrap`, `docker compose up -d`) and capture the run log for regression.  # TODO: run once infra available
