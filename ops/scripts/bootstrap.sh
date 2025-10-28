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

wait_for_service_health() {
  local service="$1"
  local timeout="${2:-180}"
  local interval="${3:-5}"
  local start time_now elapsed container status

  start=$(date +%s)
  while true; do
    container=$(docker compose ps -q "$service")
    if [[ -z "$container" ]]; then
      echo "Waiting for container id for service '$service'..."
      sleep "$interval"
      continue
    fi
    status=$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container" 2>/dev/null || echo "unknown")
    case "$status" in
      healthy|running)
        echo "Service '$service' is healthy."
        return 0
        ;;
      unhealthy|exited)
        echo "Service '$service' reported status '$status'."
        docker compose logs "$service"
        return 1
        ;;
      starting|restarting)
        ;;
      *)
        echo "Service '$service' status: $status (continuing to wait)"
        ;;
    esac
    time_now=$(date +%s)
    elapsed=$((time_now - start))
    if (( elapsed >= timeout )); then
      echo "Timed out after ${elapsed}s waiting for '$service' to become healthy." >&2
      docker compose logs "$service"
      return 1
    fi
    sleep "$interval"
  done
}

if [ "$SKIP_PULL" = false ]; then
  echo "Pulling container images..."
  docker compose pull
fi

echo "Starting core infrastructure (databases, secrets, storage)..."
docker compose up -d infisical-db infisical-redis infisical postgres redis minio clickhouse airbyte-db openmetadata-postgres openmetadata-elasticsearch prometheus

echo "Waiting for Infisical to become healthy..."
if wait_for_service_health infisical 240 5; then
  if [ -n "${INFISICAL_CLIENT_ID:-}" ] && [ -n "${INFISICAL_CLIENT_SECRET:-}" ] && [ -n "${INFISICAL_WORKSPACE_ID:-}" ]; then
    echo "Seeding secrets in Infisical..."
    "$SCRIPT_DIR/infisical_seed.sh"
  else
    echo "INFISICAL_* credentials not provided; skipping automatic secret seeding." >&2
  fi
else
  echo "Infisical failed health check. Inspect logs with 'docker compose logs infisical'." >&2
  exit 1
fi

echo "Initializing Airflow metadata database..."
docker compose --profile bootstrap run --rm airflow-init

echo "Creating MinIO buckets..."
for bucket in "$MINIO_BUCKET_BRONZE" "$MINIO_BUCKET_SILVER" "$MINIO_BUCKET_GOLD"; do
  docker run --rm --network "${PROJECT_NETWORK}" \
    -e MC_HOST_local="http://$MINIO_ROOT_USER:$MINIO_ROOT_PASSWORD@minio:9000" \
    minio/mc:latest mb -p "local/$bucket" >/dev/null || true
done

echo "Running Liquibase migrations for ClickHouse and Postgres..."
docker compose --profile tools run --rm liquibase --defaultsFile=/workspace/liquibase/liquibase-postgres.properties update
# ClickHouse plugin may not ship with Liquibase image; command provided for manual execution if driver is available.
echo "Liquibase for ClickHouse (requires clickhouse driver jar)"
docker compose --profile tools run --rm -e LIQUIBASE_CLASSPATH=/workspace/liquibase/drivers/liquibase-clickhouse-extension.jar liquibase \
  --defaultsFile=/workspace/liquibase/liquibase-clickhouse.properties update || echo "ClickHouse Liquibase update skipped (ensure driver present)."

echo "Starting remaining services..."
docker compose up -d

echo "Waiting for Airbyte API to become reachable..."
AIRBYTE_HEALTH_URL="${AIRBYTE_API_URL:-http://localhost:8001/api}/v1/health"
airbyte_ready=false
for attempt in $(seq 1 120); do
  if curl -sf "$AIRBYTE_HEALTH_URL" >/dev/null 2>&1; then
    airbyte_ready=true
    break
  fi
  sleep 5
done

if [ "$airbyte_ready" != true ]; then
  echo "Airbyte API did not become ready in time" >&2
  exit 1
fi

echo "Registering Airbyte resources..."
python3 "$SCRIPT_DIR/bootstrap_airbyte.py"

echo "Seeding OpenMetadata ingestion pipelines..."
python3 "$SCRIPT_DIR/openmetadata_seed.py"

echo "Injecting Airflow connections and variables..."
python3 "$SCRIPT_DIR/airflow_setup.py"

echo "Bootstrap completed. Review README for next steps."
