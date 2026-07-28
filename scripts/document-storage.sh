#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_ENV="${MOOPIEW_ENV_FILE:-$ROOT/.env.production}"
[[ -f "$APP_ENV" ]] || { echo "Missing $APP_ENV" >&2; exit 1; }
set -a
# shellcheck disable=SC1090
source "$APP_ENV"
set +a
cd "$ROOT"
exec python3 scripts/document-storage.py "$@"
