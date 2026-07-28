#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATABASE_PATH="${DATABASE_PATH:-$ROOT/data/moopiew.sqlite3}"
BACKUP_DIR="${BACKUP_DIR:-$ROOT/output/backups}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"

[[ -f "$DATABASE_PATH" ]] || { echo "Database not found: $DATABASE_PATH" >&2; exit 1; }
if [[ "${BACKUP_REQUIRE_ENCRYPTION:-false}" == "true" && -z "${BACKUP_AGE_RECIPIENT:-}" ]]; then
  echo "Encrypted backups are required; set BACKUP_AGE_RECIPIENT" >&2
  exit 1
fi
if [[ -n "${BACKUP_AGE_RECIPIENT:-}" ]]; then
  command -v age >/dev/null || {
    echo "BACKUP_AGE_RECIPIENT is set but age is not installed" >&2
    exit 1
  }
fi
mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
target="$BACKUP_DIR/moopiew-$stamp.sqlite3"
plain="$(mktemp "$BACKUP_DIR/.moopiew-$stamp.XXXXXX.sqlite3")"
encrypted_tmp=""
cleanup() {
  rm -f -- "$plain"
  [[ -z "$encrypted_tmp" ]] || rm -f -- "$encrypted_tmp"
}
trap cleanup EXIT HUP INT TERM
python3 - "$DATABASE_PATH" "$plain" <<'PY'
import sqlite3, sys
source, target = sys.argv[1:]
with sqlite3.connect(source) as src, sqlite3.connect(target) as dst:
    src.backup(dst)
with sqlite3.connect(f"file:{target}?mode=ro", uri=True) as restored:
    result = restored.execute("PRAGMA integrity_check").fetchone()[0]
    if result != "ok":
        raise SystemExit(f"Backup integrity check failed: {result}")
PY
chmod 600 "$plain"

if [[ -n "${BACKUP_AGE_RECIPIENT:-}" ]]; then
  encrypted_tmp="$(mktemp "$BACKUP_DIR/.moopiew-$stamp.XXXXXX.age")"
  age --recipient "$BACKUP_AGE_RECIPIENT" --output "$encrypted_tmp" "$plain"
  chmod 600 "$encrypted_tmp"
  target="$target.age"
  mv -- "$encrypted_tmp" "$target"
  encrypted_tmp=""
else
  mv -- "$plain" "$target"
fi
(cd "$BACKUP_DIR" && sha256sum "$(basename "$target")") > "$target.sha256"
chmod 600 "$target.sha256"

find "$BACKUP_DIR" -maxdepth 1 -type f -name 'moopiew-*' \
  -mtime "+$BACKUP_RETENTION_DAYS" -delete
printf 'Created and verified backup: %s\n' "$target"
