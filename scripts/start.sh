#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$ROOT/.venv/bin/python"
[[ -x "$PYTHON" ]] || {
  echo "Missing $PYTHON. Create the pinned runtime first:" >&2
  echo "  python3 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt" >&2
  exit 1
}
exec "$PYTHON" "$ROOT/app.py"
