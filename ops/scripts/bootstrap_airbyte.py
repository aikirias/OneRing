#!/usr/bin/env python3
"""Register demo Airbyte source, destination, and connection for Bronze ingestion."""
import os
import sys
import time
from typing import Any, Dict

import requests
from requests import exceptions

API_URL = os.getenv("AIRBYTE_API_URL", "http://localhost:8001/api").rstrip("/")
REQUEST_TIMEOUT = int(os.getenv("AIRBYTE_API_TIMEOUT", "180"))
SOURCE_NAME = os.getenv("AIRBYTE_DEMO_SOURCE", "Demo Faker Orders")
SOURCE_DEFINITION_NAME = os.getenv("AIRBYTE_DEMO_SOURCE_DEFINITION", "Sample Data (Faker)")
DESTINATION_NAME = os.getenv("AIRBYTE_DEMO_DESTINATION", "Demo MinIO Bronze")
DESTINATION_DEFINITION_NAME = os.getenv("AIRBYTE_DEMO_DESTINATION_DEFINITION", "S3")
CONNECTION_NAME = os.getenv("AIRBYTE_DEMO_CONNECTION", "Faker Orders to Bronze")
BRONZE_BUCKET = os.getenv("MINIO_BUCKET_BRONZE", "bronze")
ACCESS_KEY = os.getenv("MINIO_ROOT_USER")
SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD")
MINIO_ENDPOINT = os.getenv("AIRBYTE_MINIO_ENDPOINT", "http://minio:9000")

session = requests.Session()


def _post(path: str, payload: Dict[str, Any], *, timeout: int = REQUEST_TIMEOUT, retries: int = 3) -> Dict[str, Any]:
    url = f"{API_URL}{path}"
    for attempt in range(1, retries + 1):
        try:
            resp = session.post(url, json=payload, timeout=timeout)
            if resp.status_code >= 400:
                raise RuntimeError(f"Airbyte API call {path} failed: {resp.status_code} {resp.text}")
            return resp.json()
        except (exceptions.Timeout, exceptions.ConnectionError) as exc:
            if attempt == retries:
                raise RuntimeError(f"Airbyte API call {path} failed after {retries} attempts: {exc}") from exc
            time.sleep(5)
    raise RuntimeError(f"Airbyte API call {path} exhausted retries")


def _get_workspace_id() -> str:
    resp = _post("/v1/workspaces/list", {})
    workspaces = resp.get("workspaces", [])
    if not workspaces:
        raise RuntimeError("No Airbyte workspaces found. Ensure Airbyte is running.")
    return workspaces[0]["workspaceId"]


def _find_existing(path: str, payload: Dict[str, Any], name_key: str, target_name: str) -> Dict[str, Any] | None:
    resp = _post(path, payload)
    for item in resp.get(path.split("/")[-1], []):
        if item.get(name_key) == target_name:
            return item
    return None


def _lookup_source_definition_id(name: str) -> str:
    resp = _post("/v1/source_definitions/list", {})
    for definition in resp.get("sourceDefinitions", []):
        if definition.get("name", "").lower() == name.lower():
            return definition["sourceDefinitionId"]
    raise RuntimeError(f"Source definition '{name}' not found in Airbyte registry.")


def _lookup_destination_definition_id(name: str) -> str:
    resp = _post("/v1/destination_definitions/list", {})
    for definition in resp.get("destinationDefinitions", []):
        if definition.get("name", "").lower() == name.lower():
            return definition["destinationDefinitionId"]
    raise RuntimeError(f"Destination definition '{name}' not found in Airbyte registry.")


def ensure_source(workspace_id: str) -> str:
    existing = _find_existing("/v1/sources/list", {"workspaceId": workspace_id}, "name", SOURCE_NAME)
    if existing:
        return existing["sourceId"]

    source_definition_id = _lookup_source_definition_id(SOURCE_DEFINITION_NAME)

    payload = {
        "name": SOURCE_NAME,
        "sourceDefinitionId": source_definition_id,
        "workspaceId": workspace_id,
        "connectionConfiguration": {
            "count": 100,
            "records_per_sync": 100,
            "seed": 42,
            "parallelism": 1,
            "schema": "orders"
        }
    }
    resp = _post("/v1/sources/create", payload)
    return resp["sourceId"]


def ensure_destination(workspace_id: str) -> str:
    if not ACCESS_KEY or not SECRET_KEY:
        raise RuntimeError("MINIO_ROOT_USER and MINIO_ROOT_PASSWORD must be set in environment before seeding Airbyte.")

    existing = _find_existing("/v1/destinations/list", {"workspaceId": workspace_id}, "name", DESTINATION_NAME)
    if existing:
        return existing["destinationId"]

    destination_definition_id = _lookup_destination_definition_id(DESTINATION_DEFINITION_NAME)

    payload = {
        "name": DESTINATION_NAME,
        "destinationDefinitionId": destination_definition_id,
        "workspaceId": workspace_id,
        "connectionConfiguration": {
            "s3_bucket_name": BRONZE_BUCKET,
            "s3_bucket_region": "us-east-1",
            "s3_bucket_path": "raw/orders",
            "s3_path_format": "{namespace}/{stream}/{year}-{month}-{day}",
            "s3_endpoint": MINIO_ENDPOINT,
            "access_key_id": ACCESS_KEY,
            "secret_access_key": SECRET_KEY,
            "file_name_pattern": "{timestamp}",
            "format": {
                "format_type": "JSONL",
                "compression": {"compression_type": "No Compression"},
                "flattening": "No flattening"
            }
        }
    }
    resp = _post("/v1/destinations/create", payload)
    return resp["destinationId"]


def ensure_connection(source_id: str, destination_id: str, workspace_id: str) -> str:
    connections = _post("/v1/connections/list", {"workspaceId": workspace_id}).get("connections", [])
    for conn in connections:
        if conn.get("name") == CONNECTION_NAME:
            return conn["connectionId"]

    payload = {
        "name": CONNECTION_NAME,
        "sourceId": source_id,
        "destinationId": destination_id,
        "syncCatalog": {
            "streams": [
                {
                    "stream": {
                        "name": "orders",
                        "jsonSchema": {},
                        "supportedSyncModes": ["full_refresh"],
                        "defaultCursorField": [],
                        "sourceDefinedCursor": False,
                        "sourceDefinedPrimaryKey": []
                    },
                    "config": {
                        "syncMode": "full_refresh",
                        "destinationSyncMode": "append",
                        "selected": True
                    }
                }
            ]
        },
        "scheduleType": "manual",
        "status": "active"
    }
    resp = _post("/v1/connections/create", payload)
    return resp["connectionId"]


def main() -> None:
    workspace_id = _get_workspace_id()
    source_id = ensure_source(workspace_id)
    destination_id = ensure_destination(workspace_id)
    connection_id = ensure_connection(source_id, destination_id, workspace_id)
    print(f"Airbyte connection ready: {connection_id}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pylint: disable=broad-except
        print(f"Failed to bootstrap Airbyte: {exc}", file=sys.stderr)
        sys.exit(1)
