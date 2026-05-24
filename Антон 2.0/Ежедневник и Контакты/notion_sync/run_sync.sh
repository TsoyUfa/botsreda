#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_PATH="$SCRIPT_DIR/config.json"
PYTHON_BIN="${PYTHON_BIN:-python3}"

"$PYTHON_BIN" "$SCRIPT_DIR/sync.py" --config "$CONFIG_PATH" sync
