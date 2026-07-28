#!/usr/bin/env bash
set -Eeuo pipefail

[[ $# -eq 1 ]] || {
  echo "Usage: $0 <backup.sqlite3|backup.sqlite3.age>" >&2
  exit 64
}
backup="$1"
[[ -f "$backup" && ! -L "$backup" ]] || {
  echo "Backup must be a regular, non-symlink file: $backup" >&2
  exit 1
}
if [[ -f "$backup.sha256" ]]; then
  (cd "$(dirname "$backup")" && sha256sum --check "$(basename "$backup.sha256")")
fi
candidate="$backup"
temporary=""
cleanup() {
  [[ -z "$temporary" ]] || rm -f -- "$temporary"
}
trap cleanup EXIT HUP INT TERM
if [[ "$backup" == *.age ]]; then
  command -v age >/dev/null || { echo "age is required to verify $backup" >&2; exit 1; }
  [[ -n "${BACKUP_AGE_IDENTITY:-}" && -f "$BACKUP_AGE_IDENTITY" ]] || {
    echo "Set BACKUP_AGE_IDENTITY to the age identity file" >&2
    exit 1
  }
  temporary="$(mktemp "${TMPDIR:-/tmp}/moopiew-restore.XXXXXX.sqlite3")"
  chmod 600 "$temporary"
  age --decrypt --identity "$BACKUP_AGE_IDENTITY" --output "$temporary" "$backup"
  candidate="$temporary"
fi
python3 - "$candidate" <<'PY'
import sqlite3
import sys

with sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True) as connection:
    result = connection.execute("PRAGMA integrity_check").fetchone()[0]
    if result != "ok":
        raise SystemExit(f"Backup integrity check failed: {result}")
    tables = connection.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
    ).fetchone()[0]
    if tables == 0:
        raise SystemExit("Backup contains no tables")
print("Backup checksum and SQLite integrity checks passed.")
PY
