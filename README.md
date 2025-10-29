# OneRing Data Platform

Local, Docker-first medallion data platform that showcases orchestration, ingestion, cataloging, quality, versioning, secrets, and observability in a single plug-and-play stack.

## Stack

| Capability | Tooling |
| --- | --- |
| Orchestration & Batch | Apache Airflow (Celery executor) |
| Ingestion | Airbyte (server, worker, webapp, Temporal) |
| Object Storage | MinIO (S3 compatible) |
| Warehouses | ClickHouse (Silver analytics), Postgres (Gold curated & Airflow metastore) |
| Data Quality | Great Expectations |
| Metadata & Lineage | OpenMetadata (server + ingestion) |
| Schema Versioning | Liquibase (Postgres + ClickHouse changelogs) |
| Feature Store | Feast (file offline store + Redis online store) |
| Experiment Tracking & Registry | MLflow (Postgres backend + MinIO artifact store) |
| Model Serving | BentoML service & container |
| ML Monitoring | Evidently (daily drift reports) |
| Demo UI | Streamlit mini-app |
| Secrets Handling | Infisical (optional vault) + environment variables |
| Observability | Prometheus + Grafana |

## Prerequisites

- Docker & Docker Compose v2
- GNU Make (optional, for shortcuts)
- Python 3.9+ on the host (`python3 -m pip install -r requirements.txt` installs helper script deps)

## Getting Started

1. Copy the environment template and customize secrets as needed:
   ```bash
   cp .env.example .env
   # edit .env with unique passwords
   ```
2. Install host Python dependencies for helper scripts:
   ```bash
   python3 -m pip install -r requirements.txt
   ```
3. Bootstrap the stack (pull images, seed secrets, run migrations, register resources):
   ```bash
   make bootstrap
   # include extra modules, e.g.:
   # make bootstrap PROFILES="core ingestion"
   ```
   > `bootstrap` orchestrates database/bootstrap migrations, MinIO bucket creation, Airbyte/OpenMetadata registration, and Airflow connection setup. Airbyte can take a couple of minutes to expose its API during the first run.
4. Bring the desired profiles online (defaults to `core`):
   ```bash
   make up
   # examples:
   # make up PROFILES="core ingestion"
   # make up-ingestion        # shortcut == core + ingestion
   ```
5. Validate services:
   ```bash
   docker compose ps
   ```

## Profiles & Modular Startup

The Compose file is partitioned into profiles so you can start only what you need. All `make` targets accept a space-separated list via `PROFILES="..."`, or use the shortcuts (`make up-ingestion`, `make up-ml`, etc.) to bring common combinations online. Profiles are additive—combine them to compose larger scenarios.

| Profile | Key services | Purpose |
| --- | --- | --- |
| `core` | Airflow scheduler/webserver/worker/triggerer/flower, Postgres (metastore & gold), Redis, ClickHouse, MinIO, Infisical | Baseline medallion pipelines, secrets, storage |
| `ingestion` | Airbyte server/worker/webapp, Temporal & workspace Postgres, reused MinIO | Self-service ingestion into Bronze (MinIO) |
| `catalog` | OpenMetadata server, Postgres, Elasticsearch, ingestion container | Metadata, lineage, glossary demos |
| `ml` | MLflow + Postgres backend, BentoML service, Streamlit mini-app, reused MinIO | Feature + model lifecycle, serving & monitoring |
| `observability` | Prometheus, Grafana | Metrics dashboards and alerts |

Special profiles: `bootstrap` (Airflow DB init job) and `tools` (Liquibase) are used internally by scripts.

## Demo Flow (Bronze → Silver → Gold)

> Profiles to run: `core` + `ingestion` (add `catalog` to capture lineage).

1. Ensure Airbyte connection exists (created during bootstrap) and MinIO holds the seed CSV (`ops/scripts/seed_minio.py`).
2. Trigger the Airflow DAG `medallion_batch_demo` from the UI (`http://localhost:8080`) or via CLI:
   ```bash
   docker compose exec airflow-webserver airflow dags trigger medallion_batch_demo
   ```
3. DAG steps:
   - Triggers Airbyte sync via API → Bronze data lands in MinIO (`bronze/airbyte/...`).
   - Great Expectations validates Bronze dataset.
   - Transforms & filters orders into a Silver dataset, validates again.
   - Loads Silver data into ClickHouse (`analytics.orders_clean`).
   - Publishes curated snapshot to Postgres (`gold.orders_snapshot`).
   - Logs lineage hook (expand for OpenMetadata integration).
4. Inspect outputs:
   - MinIO console: `http://localhost:9001`
   - ClickHouse client: `docker compose exec clickhouse clickhouse-client -q "SELECT * FROM analytics.orders_clean"`
   - Postgres gold: `docker compose exec postgres psql -d curated -c "SELECT * FROM gold.orders_snapshot"`
   - Great Expectations validation results under `platform/quality/great_expectations/validations`.

## ML Feature & Model Lifecycle

> Profiles to run: `core` + `ml` (keep `ingestion` if you need Airbyte-source refreshes).

1. **Trigger the DAG** `feast_spark_ml_pipeline` from Airflow (UI or CLI). The workflow:
   - Applies, materialises, and exports features from the Feast repo (`platform/featurestore/feast_repo`).
   - Generates a training dataset and stores it under `storage/data/ml/outputs/`.
   - Trains a Spark ML logistic-regression model with Hyperopt, logs runs/metrics to MLflow, and registers the best model.
   - Builds a Bento bundle from the registered model and signals the BentoML service to reload.
2. **Inspect experiments** at `http://localhost:5000` (MLflow UI). Credentials inherit from `.env` (no auth by default).
3. **Invoke the serving endpoint** exposed by BentoML at `http://localhost:3001/predict`:
   ```bash
   curl -X POST http://localhost:3001/predict \
     -H 'Content-Type: application/json' \
     -d '{"instances": [{"total_transactions": 25, "total_spend": 760.0, "avg_transaction_value": 30.4, "spend_last_30d": 180.0}]}'
   ```
4. **Optional mini-app**: open the Streamlit UI at `http://localhost:8501` to score customers interactively.
5. **Daily monitoring**: the `evidently_drift_report` DAG runs a drift report with Evidently, storing HTML outputs in `storage/data/ml/reports/`. Review the latest report after the DAG finishes.

## Observability & Catalog

> Profiles to run: `core` + `observability` (+ `catalog` for OpenMetadata).

- Grafana: `http://localhost:3000` (credentials from `.env`). Dashboard shows Airflow DAG metrics, MinIO requests, ClickHouse inserts.
- Prometheus: `http://localhost:9090`.
- OpenMetadata: `http://localhost:8585` (default admin `admin@open-metadata.org` / `admin`). Use the ingestion configs in `platform/catalog/openmetadata/ingestion/*.yaml` to refresh metadata via `ops/scripts/openmetadata_seed.py`.
- MLflow Tracking: `http://localhost:5000` – compare runs, metrics, and registered models coming from the Spark/Hyperopt pipeline.
- Evidently drift reports: generated HTML files reside in `storage/data/ml/reports/`; host them in Grafana or share directly.

## Secrets & Config Management

- Secrets are sourced from `.env` by default; the stack also includes Infisical (`http://localhost:8082`) so you can wire in a vault if desired. Populate `INFISICAL_*` variables (use base64-encoded 32-byte values for `INFISICAL_ENCRYPTION_KEY` and `INFISICAL_AUTH_SECRET`) and rerun `make bootstrap` to seed secrets automatically via `ops/scripts/infisical_seed.sh`.

## Schema Versioning

- Liquibase changelogs for Postgres (`platform/versioning/liquibase/changelogs/postgres`) and ClickHouse (`platform/versioning/liquibase/changelogs/clickhouse`).
- Run updates manually as needed:
  ```bash
  docker compose --profile tools run --rm liquibase --defaultsFile=platform/versioning/liquibase/liquibase-postgres.properties update
  docker compose --profile tools run --rm -e LIQUIBASE_CLASSPATH=/liquibase/drivers/liquibase-clickhouse-extension.jar \
    liquibase --defaultsFile=platform/versioning/liquibase/liquibase-clickhouse.properties update
  ```

## Extending the Platform

1. **Add new Airbyte connectors**: update `ops/scripts/bootstrap_airbyte.py` or use the Airbyte UI; then rerun the script to register additional connections.
2. **New Airflow DAGs**: drop DAG files into `platform/orchestration/airflow/dags/`; add GE suites under `platform/quality/great_expectations/expectations`.
3. **Additional Great Expectations suites**: create expectation JSON files and reference them via checkpoints or DAG tasks inside `platform/quality/great_expectations`.
4. **Database schema changes**: author new Liquibase changelog files (incremental IDs) under `platform/versioning/liquibase` and rerun updates.
5. **Metadata ingestion**: add YAML configs in `platform/catalog/openmetadata/ingestion/` and append them to `ops/scripts/openmetadata_seed.py`.

## Folder Layout (excerpt)

```
.
├── ops/scripts/
│   ├── bootstrap.sh
│   ├── bootstrap_airbyte.py
│   ├── infisical_seed.sh
│   ├── openmetadata_seed.py
│   ├── airflow_setup.py
│   └── seed_minio.py
├── platform/
│   ├── orchestration/airflow/{dags,config,include,tests}
│   ├── ingestion/airbyte/config
│   ├── quality/great_expectations/{expectations,checkpoints}
│   ├── catalog/openmetadata/ingestion
│   ├── featurestore/feast_repo
│   ├── analytics/{clickhouse,postgres}
│   ├── storage/medallion/{bronze,silver,gold}
│   ├── ml/{training,bento_service}
│   ├── versioning/liquibase
│   ├── security/infisical
│   └── observability/{grafana,prometheus}
├── storage/data/ml
└── docker-compose.yml
```

## Data Flow Diagram

```mermaid
flowchart LR
    subgraph Bronze
        Airbyte((Airbyte Source)) -->|JSONL| MinIO[(MinIO Bronze)]
    end
    subgraph Silver
        MinIO -->|Airflow Transform| ClickHouse[(ClickHouse Silver)]
        ClickHouse -->|Great Expectations| GE[Great Expectations]
    end
    subgraph Gold
        ClickHouse -->|Airflow Publish| Postgres[(Postgres Gold)]
    end
    Airflow --> OpenMetadata
    Airbyte --> OpenMetadata
    GE --> OpenMetadata
    MinIO --> Grafana
    ClickHouse --> Grafana
    Postgres --> Grafana
```

## Troubleshooting

- `docker compose logs <service>` for detailed service logs.
- Ensure Airbyte containers are healthy (`docker compose ps`) if bootstrap waits on the API.
- If Liquibase ClickHouse update fails, download the ClickHouse Liquibase extension jar and mount it under `liquibase/drivers/`.
- Re-run `ops/scripts/seed_minio.py` to refresh Bronze sample data.

## Next Ideas

- Add streaming ingestion (e.g., Kafka + Debezium) alongside Airbyte.
- Integrate dbt for SQL-based transformations in Silver/Gold layers.
- Configure OpenLineage/OpenMetadata integration for automatic DAG lineage capture.
- Expand Grafana dashboards with Great Expectations validation results.
