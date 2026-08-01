#!/usr/bin/env bash
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export ZEAZ_HOME="$ROOT"
cd "$ROOT"
if [ -f "$ROOT/.venv/bin/python" ]; then
  exec "$ROOT/.venv/bin/python" -m app "$@"
else
  exec python3 -m app "$@"
fi
