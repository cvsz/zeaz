#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATABASE_PATH="${DATABASE_PATH:-$ROOT/data/moopiew.sqlite3}"
BACKUP_DIR="${BACKUP_DIR:-$ROOT/output/backups}"

[[ -f "$DATABASE_PATH" ]] || { echo "Database not found: $DATABASE_PATH" >&2; exit 1; }
mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
target="$BACKUP_DIR/moopiew-$stamp.sqlite3"
python3 - "$DATABASE_PATH" "$target" <<'PY'
import sqlite3, sys
source, target = sys.argv[1:]
with sqlite3.connect(source) as src, sqlite3.connect(target) as dst:
    src.backup(dst)
PY
chmod 600 "$target"
printf 'Created backup: %s\n' "$target"
