#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[[ $# -eq 1 ]] || {
  echo "Usage: $0 <backup.sqlite3|backup.sqlite3.age>" >&2
  exit 64
}
backup="$1"
"$ROOT/scripts/verify-backup.sh" "$backup"

workspace="$(mktemp -d "${TMPDIR:-/tmp}/moopiew-restore-drill.XXXXXX")"
candidate="$workspace/moopiew.sqlite3"
cleanup() {
  rm -rf -- "$workspace"
}
trap cleanup EXIT HUP INT TERM

if [[ "$backup" == *.age ]]; then
  age --decrypt --identity "$BACKUP_AGE_IDENTITY" --output "$candidate" "$backup"
else
  cp -- "$backup" "$candidate"
fi
chmod 600 "$candidate"

DATA_DIR="$workspace" DATABASE_PATH="$candidate" PYTHONPATH="$ROOT" python3 - <<'PY'
import sqlite3

import app

app.initialise_database()
with sqlite3.connect(app.DB_PATH) as connection:
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        raise SystemExit(f"Restored database integrity check failed: {integrity}")
    violations = connection.execute("PRAGMA foreign_key_check").fetchall()
    if violations:
        raise SystemExit(f"Restored database has foreign-key violations: {violations}")
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    required = {"orders", "inventory_items", "schema_migrations", "settings"}
    missing = sorted(required - tables)
    if missing:
        raise SystemExit(f"Restored database is missing core tables: {missing}")
print("Restore drill passed on an isolated migrated copy.")
PY
