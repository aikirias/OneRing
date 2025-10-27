#!/usr/bin/env bash
set -euo pipefail

: "${INFISICAL_SERVER_URL:?Set INFISICAL_SERVER_URL in .env}"
: "${INFISICAL_CLIENT_ID:?Set INFISICAL_CLIENT_ID in .env}"
: "${INFISICAL_CLIENT_SECRET:?Set INFISICAL_CLIENT_SECRET in .env}"
: "${INFISICAL_WORKSPACE_ID:?Set INFISICAL_WORKSPACE_ID in .env}"
: "${INFISICAL_ENVIRONMENT:?Set INFISICAL_ENVIRONMENT in .env}"

API_BASE="$INFISICAL_SERVER_URL/api/v3"
LOGIN_ENDPOINT="$INFISICAL_SERVER_URL/api/v1/auth/universal-auth/login"

response=$(curl -sS -X POST "$LOGIN_ENDPOINT" \
  -H 'Content-Type: application/json' \
  -d "{\"clientId\":\"$INFISICAL_CLIENT_ID\",\"clientSecret\":\"$INFISICAL_CLIENT_SECRET\"}")

token=$(echo "$response" | python3 - <<'PY'
import json,sys
try:
    data=json.load(sys.stdin)
    print(data.get('accessToken',''))
except Exception:
    print('')
PY
)
if [[ -z "$token" ]]; then
  echo "Failed to retrieve Infisical access token. Response: $response" >&2
  exit 1
fi

echo "Publishing baseline secrets to Infisical workspace $INFISICAL_WORKSPACE_ID ($INFISICAL_ENVIRONMENT)..."

bronze_bucket=${MINIO_BUCKET_BRONZE:-bronze}
silver_bucket=${MINIO_BUCKET_SILVER:-silver}
postgres_uri="postgresql+psycopg2://${CURATED_PG_USER:-curated_user}:${CURATED_PG_PASSWORD:-curatedpass}@postgres:5432/curated"
clickhouse_uri="clickhouse://${CLICKHOUSE_USER:-default}:${CLICKHOUSE_PASSWORD:-clickpass}@clickhouse:8123/analytics"
minio_uri="aws://?aws_access_key_id=${MINIO_ROOT_USER:-minioadmin}&aws_secret_access_key=${MINIO_ROOT_PASSWORD:-minioadmin}&region_name=us-east-1&endpoint_url=http://minio:9000"
airbyte_uri="http://airbyte-server:8001/api/v1"

cat <<JSON | curl -sS -X PUT "$API_BASE/secrets/batch" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $token" \
  -d @-
{
  "workspaceId": "$INFISICAL_WORKSPACE_ID",
  "environment": "$INFISICAL_ENVIRONMENT",
  "secrets": [
    {"secretName": "AIRFLOW_CONN_POSTGRES_CURATED", "secretValue": "$postgres_uri"},
    {"secretName": "AIRFLOW_CONN_CLICKHOUSE_DEFAULT", "secretValue": "$clickhouse_uri"},
    {"secretName": "AIRFLOW_CONN_MINIO_DEFAULT", "secretValue": "$minio_uri"},
    {"secretName": "AIRFLOW_CONN_AIRBYTE_API", "secretValue": "$airbyte_uri"},
    {"secretName": "AIRFLOW_VAR_BRONZE_BUCKET", "secretValue": "$bronze_bucket"},
    {"secretName": "AIRFLOW_VAR_SILVER_BUCKET", "secretValue": "$silver_bucket"},
    {"secretName": "AIRFLOW_VAR_GOLD_SCHEMA", "secretValue": "gold"}
  ]
}
JSON

echo "Secrets uploaded."
