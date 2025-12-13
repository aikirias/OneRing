#!/usr/bin/env python3
"""Simple connectivity checks for core services."""
import os
import sys
from typing import Dict

import requests

TARGETS: Dict[str, str] = {
    "Airflow": "http://localhost:8080/health",
    "Airbyte": "http://localhost:8001/api/v1/health",
    "OpenMetadata": "http://localhost:8585/api/v1/system/config",
    "Grafana": "http://localhost:3000/api/health",
    "Keycloak": f"http://localhost:{os.getenv('KEYCLOAK_HTTP_PORT', '8089')}/realms/oner/.well-known/openid-configuration",
}


def main() -> None:
    failures = []
    for name, url in TARGETS.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code >= 400:
                raise RuntimeError(f"{url} returned {response.status_code}")
            print(f"✔ {name} reachable ({url})")
        except Exception as exc:  # pylint: disable=broad-except
            print(f"✖ {name} check failed: {exc}")
            failures.append(name)
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
