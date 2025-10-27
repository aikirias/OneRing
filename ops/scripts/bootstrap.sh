#!/usr/bin/env bash
set -euo pipefail

# Bootstrap helper to stand up core dependencies and seed configs.
# Usage: ./ops/scripts/bootstrap.sh [--skip-pull]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

SKIP_PULL=false
while (($#)); do
  case "$1" in
    --skip-pull)
      SKIP_PULL=true
      ;;
    *)
      echo "Unknown option: $1" >&2
      ;;
  esac
  shift
done

if [ -f .env ]; then
  echo "Loading environment variables from .env"
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
else
  echo "No .env file found. Copy .env.example to .env and update secrets." >&2
  exit 1
fi

if [ "$SKIP_PULL" = false ]; then
  echo "Pulling container images..."
  docker compose pull
fi

echo "Starting core infrastructure (databases, secrets, storage)..."
docker compose up -d infisical-db infisical-redis infisical postgres redis minio clickhouse airbyte-db openmetadata-postgres openmetadata-elasticsearch prometheus

echo "Waiting for Infisical to become healthy..."
docker compose wait infisical || true

if ! docker compose ps infisical | grep -q healthy; then
  echo "Infisical is not healthy yet. Check logs with 'docker compose logs infisical'" >&2
fi

if [ -z "${INFISICAL_CLIENT_ID:-}" ] || [ -z "${INFISICAL_CLIENT_SECRET:-}" ] || [ -z "${INFISICAL_WORKSPACE_ID:-}" ]; then
  echo "Infisical machine credentials are missing. Populate INFISICAL_* variables before continuing." >&2
else
  echo "Seeding secrets in Infisical..."
  "$SCRIPT_DIR/infisical_seed.sh"
fi

echo "Initializing Airflow metadata database..."
docker compose --profile bootstrap run --rm airflow-init

echo "Creating MinIO buckets..."
docker compose --profile bootstrap run --rm minio-client || true

echo "Running Liquibase migrations for ClickHouse and Postgres..."
docker compose --profile tools run --rm liquibase --defaultsFile=platform/versioning/liquibase/liquibase-postgres.properties update
# ClickHouse plugin may not ship with Liquibase image; command provided for manual execution if driver is available.
echo "Liquibase for ClickHouse (requires clickhouse driver jar)"
docker compose --profile tools run --rm -e LIQUIBASE_CLASSPATH=/liquibase/drivers/liquibase-clickhouse-extension.jar liquibase \
  --defaultsFile=platform/versioning/liquibase/liquibase-clickhouse.properties update || echo "ClickHouse Liquibase update skipped (ensure driver present)."

echo "Starting remaining services..."
docker compose up -d

echo "Registering Airbyte resources..."
python3 "$SCRIPT_DIR/bootstrap_airbyte.py"

echo "Seeding OpenMetadata ingestion pipelines..."
python3 "$SCRIPT_DIR/openmetadata_seed.py"

echo "Injecting Airflow connections and variables..."
python3 "$SCRIPT_DIR/airflow_setup.py"

echo "Bootstrap completed. Review README for next steps."
