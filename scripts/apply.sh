#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:-$ROOT}"

log() { printf '\033[1;32m==>\033[0m %s\n' "$*"; }
[[ -d "$TARGET/.git" ]] || { echo "Not a Git repository: $TARGET" >&2; exit 1; }

log "Applying non-destructive framework structure to $TARGET"
mkdir -p "$TARGET"/{docs,assets,scripts,templates,excel,output,examples,.github/workflows,.github/ISSUE_TEMPLATE}

for item in docs assets scripts templates excel examples .github; do
  if [[ "$TARGET" != "$ROOT" && -d "$ROOT/$item" ]]; then
    cp -Rn "$ROOT/$item/." "$TARGET/$item/"
  fi
done
log "Done. Existing files were not overwritten."
