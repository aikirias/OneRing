#!/usr/bin/env bash
set -euo pipefail

# Download the Metabase ClickHouse driver if it's not already present.
# The jar is required for Metabase to speak with ClickHouse.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PLUGIN_DIR="$REPO_ROOT/platform/analytics/metabase/plugins"
JAR_NAME="clickhouse.metabase-driver.jar"
TARGET="$PLUGIN_DIR/$JAR_NAME"
DEFAULT_URL="https://github.com/metabase/metabase-clickhouse-driver/releases/download/v1.2.5/$JAR_NAME"
DOWNLOAD_URL="${METABASE_CLICKHOUSE_DRIVER_URL:-$DEFAULT_URL}"

mkdir -p "$PLUGIN_DIR"

if [ -f "$TARGET" ]; then
  echo "Metabase ClickHouse driver already present at $TARGET"
  exit 0
fi

echo "Downloading Metabase ClickHouse driver from $DOWNLOAD_URL"

if command -v curl >/dev/null 2>&1; then
  if ! curl -L --fail --show-error --output "$TARGET" "$DOWNLOAD_URL"; then
    echo "Failed to download Metabase ClickHouse driver via curl." >&2
    rm -f "$TARGET"
    exit 1
  fi
elif command -v wget >/dev/null 2>&1; then
  if ! wget -O "$TARGET" "$DOWNLOAD_URL"; then
    echo "Failed to download Metabase ClickHouse driver via wget." >&2
    rm -f "$TARGET"
    exit 1
  fi
else
  echo "Neither curl nor wget is available to download the Metabase ClickHouse driver." >&2
  exit 1
fi

echo "Metabase ClickHouse driver stored at $TARGET"
