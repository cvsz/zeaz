#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="$ROOT/apps/web/dist"
TARGET="$ROOT/web/platform"

[[ -f "$SOURCE/index.html" && -d "$SOURCE/assets" ]] || {
  echo "Missing apps/web production build. Run npm run build first." >&2
  exit 1
}
[[ -d "$TARGET" ]] || {
  echo "Missing publish target: $TARGET" >&2
  exit 1
}
command -v rsync >/dev/null 2>&1 || {
  echo "Missing dependency: rsync" >&2
  exit 1
}

# web/platform is the exact static artifact served at /platform/. --delete is
# constrained to this known generated-output directory so obsolete hashed
# bundles cannot remain publicly reachable after a new build.
rsync -a --delete "$SOURCE/" "$TARGET/"
echo "Published apps/web/dist to web/platform."
