# OneRing Data Platform Architecture

## Overview
- **Purpose**: Local medallion-style data platform for demos and advisory engagements.
- **Paradigm**: Batch-first flows orchestrated via Airflow, with medallion layers stored across MinIO, ClickHouse, and Postgres.

## Core Components
1. **Airflow** orchestrates ingestion, validation, and transformations.
2. **Airbyte** enables self-service ingestion to Bronze (MinIO).
3. **Apache Pulsar** acts as the distributed messaging and streaming backbone.
4. **Apache Spark** provides distributed batch processing for ingestion and ML workloads.
5. **Apache Flink** powers streaming-oriented demos and CEP experiments.
6. **MinIO** stores data lake zones (Bronze/Silver/Gold) with S3 compatibility.
7. **Great Expectations** validates data quality during DAG execution.
8. **Liquibase** versions schemas for Postgres and ClickHouse targets.
9. **OpenMetadata** centralizes catalog, lineage, and quality signals.
10. **Grafana** visualizes operational metrics and validation outcomes.
11. **Feast** manages feature views (file offline store + Redis online store).
12. **MLflow** tracks experiments, metrics, and registers Spark models (backed by Postgres + MinIO artifacts).
13. **BentoML** packages MLflow models for serving and exposes an HTTP endpoint.
14. **Evidently** runs scheduled drift reports through Airflow.
15. **Streamlit** offers an optional mini UI consuming the Bento endpoint.
16. **Metabase** provides ad-hoc analytics on ClickHouse/Postgres (requires ClickHouse driver plugin).
17. **Jenkins** delivers CI/CD automation via JCasC-ready configuration.

## High-Level Flow
```mermaid
flowchart LR
    subgraph Bronze
        AB[Airbyte Connector]
        AB -->|Write| MIO[(MinIO Bronze Bucket)]
        Spark[[Spark Jobs]] -->|Load/Transform| MIO
        Flink[[Flink Jobs]] -->|Stream| MIO
        Pulsar(((Pulsar Topics))) -->|Bronze Stream| MIO
    end

    subgraph Silver
        AF[[Airflow DAG Transform]] -->|Load| CH[(ClickHouse Silver DB)]
        MIO -->|Read| AF
        AF -->|Validate| GE[Great Expectations]
    end

    subgraph Gold
        CH -->|Curated Views| AF2[[Airflow Publish Task]]
        AF2 -->|Write| PG[(Postgres Gold Schema)]
    end

    GE -->|Quality Events| OM[OpenMetadata]
    AF --> OM
    Spark --> AF
    Spark --> Pulsar
    Flink --> Pulsar
    Flink --> OM
    AB --> OM

    OM -->|Metadata Feeds| GF[Grafana Dashboards]
    CH --> GF
    PG --> GF
    CH -->|BI Queries| MB[Metabase]
    PG --> MB
    Pulsar --> GF
    Pulsar --> MB
    Jenkins[[Jenkins CI/CD]] --> GF

    subgraph ML_Pipeline
        FS[[Feast Feature Repo]]
        MIO -->|Historical Snapshot| FS
        AF3[[Airflow ML DAG]] -->|Feature Retrieval| FS
        AF3 -->|Training Metrics| MLW[MLflow Tracking Server]
        MLW -->|Registered Model| Bento[BentoML Service]
        Bento -->|Predictions| App[Streamlit Mini-App]
        AF3 -->|Daily Drift| Evidently[Evidently Reports]
        Evidently --> OM
        MLW --> GF
    end
```

## Networking & Security
- Single Docker network `${PROJECT_NETWORK}` with service-specific subnets (defined in compose).
- Secrets managed locally via environment variables (`.env`); plug in your preferred vault if needed.

## Storage & Volumes
- Persistent named volumes for databases and message brokers.
- Bind mounts for configuration directories to ease iteration.
- Domain-driven workspace layout:
  - `platform/orchestration/airflow` – DAGs, config, plugins, and tests.
  - `platform/ingestion/airbyte` – connection templates and ingestion assets.
  - `platform/quality/great_expectations` – suites, checkpoints, runtime data.
  - `platform/catalog/openmetadata` – server and ingestion configs.
  - `platform/analytics/{clickhouse,postgres}` – DDL, init SQL, curated seeds.
  - `platform/analytics/metabase` – Metabase plugins (ClickHouse driver) and related assets.
  - `platform/storage/medallion` – local Bronze/Silver/Gold samples.
  - `platform/featurestore/feast_repo` – Feast project configuration and feature views.
  - `platform/ml/{training,bento_service}` – Spark ML pipeline code and Bento service assets.
  - `platform/versioning/liquibase` – changelogs and property files.
  - `platform/security/infisical` – vault configuration & onboarding scripts (`INFISICAL_*` settings).
  - `platform/observability/{grafana,prometheus}` – dashboards, scrape configs.
  - `ops/scripts` – bootstrap and operational automation.
