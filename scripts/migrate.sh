#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_ENV="$ROOT/.env.production"
[[ -f "$APP_ENV" ]] && { set -a; source "$APP_ENV"; set +a; }
cd "$ROOT"
python3 - <<'PY'
import app
app.initialise_database()
print(f"Database ready: {app.DB_PATH}")
PY
