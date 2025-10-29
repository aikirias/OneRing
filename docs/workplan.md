# Workplan Checklist

## Phase 1 – Foundations
- [x] Define folder structure for services and configs.
- [x] Create environment variable template (`.env.example`).
- [x] Document architecture overview and mermaid flow.

## Phase 2 – Infrastructure Configuration
- [x] Write `docker-compose.yml` with networks, volumes, dependencies.
- [x] Provide config templates for Airflow, Airbyte, MinIO, OpenMetadata, Great Expectations, Grafana, Liquibase.
- [x] Add bootstrap scripts to automate setup tasks.

## Phase 3 – Data Pipelines & Quality
- [x] Implement Airflow DAGs for Bronze → Silver → Gold flow.
- [x] Configure Great Expectations suites and checkpoints.
- [x] Seed Liquibase changelogs for Postgres and ClickHouse.

## Phase 4 – Catalog & Observability
- [x] Configure OpenMetadata ingestion pipelines.
- [x] Add Grafana dashboards and Prometheus exporters setup.
- [ ] Register metadata/lineage reporting hooks (stubbed logging in DAG).

## Phase 5 – ML Feature & Model Lifecycle
- [x] Add Feast feature repository and sample data set.
- [x] Wire Spark ML + Hyperopt training with MLflow tracking/registry.
- [x] Package models with BentoML and expose serving endpoint.
- [x] Generate Evidently drift reports via scheduled Airflow DAG.
- [x] Provide Streamlit mini-application consuming Bento endpoint.

## Phase 5b – Analytics & BI
- [x] Add Metabase service with ClickHouse driver automation.
- [x] Provide dedicated Make target/profile for ClickHouse + Metabase.

## Phase 6 – Documentation & Packaging
- [x] Complete README with end-to-end instructions and extensions.
- [x] Add sample data and Airbyte connection templates.
- [ ] Validate bootstrap (`make bootstrap`, `docker compose up -d`).  # TODO: run once infra available
