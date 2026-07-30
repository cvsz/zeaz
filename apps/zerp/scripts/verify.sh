#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"

npm run typecheck --workspace @moopiew/zerp
npm run build --workspace @moopiew/zerp
git diff --check -- apps/zerp

if rg -n --hidden \
  '(sk-[A-Za-z0-9_-]{12,}|AIza[A-Za-z0-9_-]{20,}|PLACEHOLDER|TODO|FIXME)' \
  apps/zerp/src apps/zerp/config apps/zerp/index.html apps/zerp/package.json; then
  echo "zERP verification failed: secret or unfinished marker found" >&2
  exit 1
fi

echo "zERP verification passed"
