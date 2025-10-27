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
| Secrets Vault | Infisical (server, Postgres, Redis) |
| Observability | Prometheus + Grafana |

## Prerequisites

- Docker & Docker Compose v2
- GNU Make (optional, for shortcuts)
- Python 3.9+ on the host (`python3 -m pip install -r requirements.txt` installs helper script deps)

## Getting Started

1. Copy the environment template and customize secrets as needed:
   ```bash
   cp .env.example .env
   # edit .env with unique passwords and Infisical credentials
   ```
2. Install host Python dependencies for helper scripts:
   ```bash
   python3 -m pip install -r requirements.txt
   ```
3. Bootstrap the stack (pull images, seed secrets, run migrations, register resources):
   ```bash
   make bootstrap
   ```
   > `bootstrap` orchestrates Infisical seeding, Liquibase migrations, MinIO bucket creation, Airbyte/OpenMetadata registration, and Airflow connection setup.
4. Bring everything online:
   ```bash
   docker compose up -d
   ```
5. Validate services:
   ```bash
   docker compose ps
   ```

## Demo Flow (Bronze → Silver → Gold)

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

## Observability & Catalog

- Grafana: `http://localhost:3000` (credentials from `.env`). Dashboard shows Airflow DAG metrics, MinIO requests, ClickHouse inserts.
- Prometheus: `http://localhost:9090`.
- OpenMetadata: `http://localhost:8585` (default admin `admin@open-metadata.org` / `admin`). Use the ingestion configs in `platform/catalog/openmetadata/ingestion/*.yaml` to refresh metadata via `ops/scripts/openmetadata_seed.py`.

## Secrets & Config Management

- Infisical: `http://localhost:8082` (configure workspace + machine identity, update `.env`).
- `ops/scripts/infisical_seed.sh` publishes Airflow connection URIs (`AIRFLOW_CONN_*`) and variables (`AIRFLOW_VAR_*`).
- Airflow uses `platform/orchestration/airflow/config/infisical_backend.py` to source all secrets dynamically from Infisical—metadata DB only stores placeholders.

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
2. **New Airflow DAGs**: drop DAG files into `platform/orchestration/airflow/dags/`; leverage secrets via Infisical and add GE suites under `platform/quality/great_expectations/expectations`.
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
│   ├── analytics/{clickhouse,postgres}
│   ├── storage/medallion/{bronze,silver,gold}
│   ├── versioning/liquibase
│   ├── security/infisical
│   └── observability/{grafana,prometheus}
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
- Ensure Infisical workspace credentials are correct before running bootstrap.
- If Liquibase ClickHouse update fails, download the ClickHouse Liquibase extension jar and mount it under `liquibase/drivers/`.
- Re-run `ops/scripts/seed_minio.py` to refresh Bronze sample data.

## Next Ideas

- Add streaming ingestion (e.g., Kafka + Debezium) alongside Airbyte.
- Integrate dbt for SQL-based transformations in Silver/Gold layers.
- Configure OpenLineage/OpenMetadata integration for automatic DAG lineage capture.
- Expand Grafana dashboards with Great Expectations validation results.
