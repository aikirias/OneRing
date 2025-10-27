"""Custom Airflow secrets backend that reads secrets from Infisical."""
from __future__ import annotations

import json
import os
import time
from typing import Any

import requests
from airflow.secrets import BaseSecretsBackend


class InfisicalSecretsBackend(BaseSecretsBackend):
    """Retrieve Airflow secrets from Infisical using machine identity credentials."""

    def __init__(
        self,
        url: str | None = None,
        workspace_id: str | None = None,
        environment: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        cache_ttl: int = 300,
    ) -> None:
        super().__init__()
        self.url = (url or os.environ.get("INFISICAL_SERVER_URL", "http://infisical:8080")).rstrip("/")
        self.workspace_id = workspace_id or os.environ.get("INFISICAL_WORKSPACE_ID")
        self.environment = environment or os.environ.get("INFISICAL_ENVIRONMENT", "dev")
        self.client_id = client_id or os.environ.get("INFISICAL_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("INFISICAL_CLIENT_SECRET")
        self.cache_ttl = cache_ttl
        self._token: str | None = None
        self._token_expiry: float = 0.0
        self._cache: dict[str, tuple[str | None, float]] = {}

    # -- public API ---------------------------------------------------------
    def get_conn_uri(self, conn_id: str) -> str | None:
        key = f"AIRFLOW_CONN_{conn_id.upper()}"
        return self._get_secret(key)

    def get_variable(self, key: str) -> Any:
        secret = self._get_secret(f"AIRFLOW_VAR_{key.upper()}")
        if secret is None:
            return None
        try:
            return json.loads(secret)
        except json.JSONDecodeError:
            return secret

    def get_config(self, key: str) -> str | None:
        return self._get_secret(f"AIRFLOW_CONFIG_{key.upper()}")

    # -- internal -----------------------------------------------------------
    def _get_secret(self, name: str) -> str | None:
        if name in self._cache:
            value, expiry = self._cache[name]
            if time.time() < expiry:
                return value

        if not all([self.workspace_id, self.client_id, self.client_secret]):
            return None

        payload = {
            "workspaceId": self.workspace_id,
            "environment": self.environment,
            "secretName": name,
        }
        response = requests.post(
            f"{self.url}/api/v3/secrets/get",
            headers=self._headers,
            json=payload,
            timeout=10,
        )
        if response.status_code == 404:
            self._cache[name] = (None, time.time() + self.cache_ttl)
            return None
        response.raise_for_status()
        data = response.json()
        value = None
        if isinstance(data, dict):
            secret_obj = data.get("secret") if isinstance(data.get("secret"), dict) else data
            value = secret_obj.get("secretValue")
        self._cache[name] = (value, time.time() + self.cache_ttl)
        return value

    @property
    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._get_token()}", "Content-Type": "application/json"}

    def _get_token(self) -> str:
        if self._token and time.time() < self._token_expiry:
            return self._token

        if not self.client_id or not self.client_secret:
            raise RuntimeError("Infisical client credentials are not configured")

        response = requests.post(
            f"{self.url}/api/v1/auth/universal-auth/login",
            json={
                "clientId": self.client_id,
                "clientSecret": self.client_secret,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        token = data.get("accessToken")
        expires_in = data.get("expiresIn", 300)
        if not token:
            raise RuntimeError("Infisical login succeeded without access token")
        self._token = token
        self._token_expiry = time.time() + int(expires_in) - 30
        return token
