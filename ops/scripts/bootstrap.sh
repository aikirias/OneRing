#!/usr/bin/env bash
set -euo pipefail

# Bootstrap helper to stand up core dependencies and seed configs.
# Usage: ./ops/scripts/bootstrap.sh [--skip-pull]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

SKIP_PULL=false
PROFILES_INPUT="core"

while (($#)); do
  case "$1" in
    --skip-pull)
      SKIP_PULL=true
      shift
      ;;
    --profiles)
      shift
      if [ $# -eq 0 ]; then
        echo "--profiles requires a comma-separated list (e.g. core,ingestion)" >&2
        exit 1
      fi
      PROFILES_INPUT="$1"
      shift
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

IFS=',' read -ra RAW_PROFILES <<< "$PROFILES_INPUT"
PROFILE_LIST=()
for raw in "${RAW_PROFILES[@]}"; do
  trimmed="${raw//[[:space:]]/}"
  if [ -n "$trimmed" ]; then
    PROFILE_LIST+=("$trimmed")
  fi
done

if [ ${#PROFILE_LIST[@]} -eq 0 ]; then
  PROFILE_LIST=("core")
fi

declare -A PROFILE_SEEN=()
DEDUPED_PROFILES=()
for profile in "${PROFILE_LIST[@]}"; do
  if [[ -z "${PROFILE_SEEN[$profile]:-}" ]]; then
    PROFILE_SEEN[$profile]=1
    DEDUPED_PROFILES+=("$profile")
  fi
done
PROFILE_LIST=("${DEDUPED_PROFILES[@]}")

COMPOSE_PROFILE_FLAGS=()
for profile in "${PROFILE_LIST[@]}"; do
  COMPOSE_PROFILE_FLAGS+=(--profile "$profile")
done

profile_selected() {
  local needle="$1"
  for profile in "${PROFILE_LIST[@]}"; do
    if [[ "$profile" == "$needle" ]]; then
      return 0
    fi
  done
  return 1
}

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
    container=$(docker compose "${COMPOSE_PROFILE_FLAGS[@]}" ps -q "$service")
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
        docker compose "${COMPOSE_PROFILE_FLAGS[@]}" logs "$service"
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
      docker compose "${COMPOSE_PROFILE_FLAGS[@]}" logs "$service"
      return 1
    fi
    sleep "$interval"
  done
}

if [ "$SKIP_PULL" = false ]; then
  echo "Pulling container images for profiles: ${PROFILE_LIST[*]}..."
  docker compose "${COMPOSE_PROFILE_FLAGS[@]}" pull
fi

declare -A PROFILE_BASE_SERVICES=(
  [core]="postgres redis clickhouse ceph infisical-db infisical-redis infisical"
  [ingestion]="ceph airbyte-db"
  [catalog]="openmetadata-postgres openmetadata-elasticsearch"
  [ml]="ceph mlflow-db"
  [analytics]="clickhouse"
  [streaming]="pulsar"
  [cicd]="jenkins"
  [observability]="prometheus"
)

BASE_SERVICES=()
declare -A BASE_SEEN=()
for profile in "${PROFILE_LIST[@]}"; do
  base="${PROFILE_BASE_SERVICES[$profile]:-}"
  if [ -n "$base" ]; then
    read -r -a base_array <<< "$base"
    for service in "${base_array[@]}"; do
      if [ -n "$service" ] && [[ -z "${BASE_SEEN[$service]:-}" ]]; then
        BASE_SEEN[$service]=1
        BASE_SERVICES+=("$service")
      fi
    done
  fi
done

if [ ${#BASE_SERVICES[@]} -gt 0 ]; then
  echo "Starting base services (${BASE_SERVICES[*]})..."
  docker compose "${COMPOSE_PROFILE_FLAGS[@]}" up -d "${BASE_SERVICES[@]}"
fi

if profile_selected core; then
  echo "Waiting for Infisical to become healthy..."
  if wait_for_service_health infisical 240 5; then
    if [ -n "${INFISICAL_CLIENT_ID:-}" ] && [ -n "${INFISICAL_CLIENT_SECRET:-}" ] && [ -n "${INFISICAL_WORKSPACE_ID:-}" ]; then
      echo "Seeding secrets in Infisical..."
      "$SCRIPT_DIR/infisical_seed.sh"
    else
      echo "INFISICAL_* credentials not provided; skipping automatic secret seeding." >&2
    fi
  else
    echo "Infisical failed health check. Inspect logs with 'docker compose ${COMPOSE_PROFILE_FLAGS[*]} logs infisical'." >&2
    exit 1
  fi
fi

if [[ -n "${BASE_SEEN[ceph]:-}" ]]; then
  echo "Waiting for Ceph RGW to become healthy..."
  wait_for_service_health ceph 240 5 || echo "Ceph health check timed out; continuing."
  echo "Creating Ceph buckets..."
  for bucket in "$CEPH_BUCKET_BRONZE" "$CEPH_BUCKET_SILVER" "$CEPH_BUCKET_GOLD" "$CEPH_BUCKET_MLFLOW" "$CEPH_BUCKET_STAGE" "$CEPH_BUCKET_ICEBERG" "$CEPH_BUCKET_FEATURESTORE"; do
    [ -z "$bucket" ] && continue
    docker run --rm --network "${PROJECT_NETWORK}" \
      -e MC_HOST_local="http://$CEPH_ACCESS_KEY:$CEPH_SECRET_KEY@ceph:${CEPH_RGW_PORT}" \
      minio/mc:latest mb -p "local/$bucket" >/dev/null || true
    docker run --rm --network "${PROJECT_NETWORK}" \
      -e MC_HOST_local="http://$CEPH_ACCESS_KEY:$CEPH_SECRET_KEY@ceph:${CEPH_RGW_PORT}" \
      minio/mc:latest anonymous set none "local/$bucket" >/dev/null || true
  done
  if [ -n "${CEPH_STAGE_USER:-}" ] && [ -n "${CEPH_STAGE_PASSWORD:-}" ] && [ -n "${CEPH_BUCKET_STAGE:-}" ]; then
    echo "Configuring Ceph staging policy..."
    STAGE_POLICY_NAME=${CEPH_STAGE_POLICY:-stage-policy}
    tmp_policy="$(mktemp)"
    cat <<POLICY > "$tmp_policy"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::${CEPH_BUCKET_STAGE}"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::${CEPH_BUCKET_STAGE}/*"
      ]
    }
  ]
}
POLICY
    docker run --rm --network "${PROJECT_NETWORK}" \
      -e MC_HOST_local="http://$CEPH_ACCESS_KEY:$CEPH_SECRET_KEY@ceph:${CEPH_RGW_PORT}" \
      -v "$tmp_policy:/stage-policy.json" \
      minio/mc:latest admin policy create local "$STAGE_POLICY_NAME" /stage-policy.json >/dev/null 2>&1 || true
    docker run --rm --network "${PROJECT_NETWORK}" \
      -e MC_HOST_local="http://$CEPH_ACCESS_KEY:$CEPH_SECRET_KEY@ceph:${CEPH_RGW_PORT}" \
      minio/mc:latest admin user info local "$CEPH_STAGE_USER" >/dev/null 2>&1 || \
      docker run --rm --network "${PROJECT_NETWORK}" \
        -e MC_HOST_local="http://$CEPH_ACCESS_KEY:$CEPH_SECRET_KEY@ceph:${CEPH_RGW_PORT}" \
        minio/mc:latest admin user add local "$CEPH_STAGE_USER" "$CEPH_STAGE_PASSWORD" >/dev/null 2>&1
    docker run --rm --network "${PROJECT_NETWORK}" \
      -e MC_HOST_local="http://$CEPH_ACCESS_KEY:$CEPH_SECRET_KEY@ceph:${CEPH_RGW_PORT}" \
      minio/mc:latest admin policy attach local "$STAGE_POLICY_NAME" --user "$CEPH_STAGE_USER" >/dev/null || true
    rm -f "$tmp_policy"
  fi
fi

if profile_selected core; then
  echo "Initializing Airflow metadata database..."
  docker compose "${COMPOSE_PROFILE_FLAGS[@]}" --profile bootstrap run --rm airflow-init
  echo "Running Liquibase migrations for ClickHouse and Postgres..."
  docker compose --profile tools run --rm liquibase --defaultsFile=/workspace/liquibase/liquibase-postgres.properties update
  echo "Liquibase for ClickHouse (requires clickhouse driver jar)"
  docker compose --profile tools run --rm -e LIQUIBASE_CLASSPATH=/workspace/liquibase/drivers/liquibase-clickhouse-extension.jar liquibase \
    --defaultsFile=/workspace/liquibase/liquibase-clickhouse.properties update || echo "ClickHouse Liquibase update skipped (ensure driver present)."
fi

if profile_selected analytics; then
  echo "Ensuring Metabase ClickHouse driver plugin..."
  if ! "$SCRIPT_DIR/metabase_clickhouse_driver.sh"; then
    echo "Metabase ClickHouse driver download failed; Metabase may not connect to ClickHouse. See README for manual steps." >&2
  fi
fi

echo "Starting selected profiles (${PROFILE_LIST[*]})..."
docker compose "${COMPOSE_PROFILE_FLAGS[@]}" up -d

if profile_selected core; then
  echo "Waiting for Airflow webserver..."
  wait_for_service_health airflow-webserver 240 10 || echo "Airflow webserver health check timed out; continuing."
fi

if profile_selected ml; then
  echo "Waiting for MLflow tracking server..."
  wait_for_service_health mlflow 180 5 || echo "MLflow did not report healthy within timeout; check logs."
fi

if profile_selected ingestion; then
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
fi

if profile_selected catalog; then
  echo "Waiting for OpenMetadata server..."
  wait_for_service_health openmetadata-server 300 5 || echo "OpenMetadata server health check timed out; continuing."
  echo "Seeding OpenMetadata ingestion pipelines..."
  python3 "$SCRIPT_DIR/openmetadata_seed.py"
fi

if profile_selected streaming; then
  echo "Waiting for Pulsar broker..."
  wait_for_service_health pulsar 240 10 || echo "Pulsar health check timed out; inspect logs if issues persist."
fi

if profile_selected cicd; then
  echo "Waiting for Jenkins UI..."
  wait_for_service_health jenkins 300 10 || echo "Jenkins health check timed out; the UI may still be initializing."
fi

if profile_selected core; then
  echo "Injecting Airflow connections and variables..."
  python3 "$SCRIPT_DIR/airflow_setup.py"
fi

echo "Bootstrap completed for profiles: ${PROFILE_LIST[*]}. Review README for next steps."
