#!/usr/bin/env python3
"""Run OpenMetadata ingestion configs to register services and capture metadata."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_BASE = ROOT / "platform" / "catalog" / "openmetadata" / "ingestion"
CONFIGS = [
    CONFIG_BASE / "airflow.yaml",
    CONFIG_BASE / "airbyte.yaml",
    CONFIG_BASE / "clickhouse.yaml",
    CONFIG_BASE / "postgres.yaml",
]


def run_ingestion(config: Path) -> None:
    if not config.exists():
        raise FileNotFoundError(f"Missing ingestion config: {config}")
    print(f"Running OpenMetadata ingestion for {config}...")
    subprocess.run(
        [
            "docker",
            "compose",
            "run",
            "--rm",
            "openmetadata-ingestion",
            "openmetadata-ingestion",
            "ingest",
            "-c",
            str(config),
        ],
        check=True,
        cwd=ROOT,
    )


def main() -> None:
    for config in CONFIGS:
        run_ingestion(config)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print(f"OpenMetadata ingestion failed: {exc}", file=sys.stderr)
        sys.exit(exc.returncode)
    except Exception as exc:  # pylint: disable=broad-except
        print(f"Error during OpenMetadata seed: {exc}", file=sys.stderr)
        sys.exit(1)
