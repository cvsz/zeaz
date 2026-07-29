#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
python3 -m compileall -q app.py dashboard tests scripts/ci/evidence.py
find scripts assets/asset-generator -type f -name '*.sh' -print0 | xargs -0 -n1 bash -n
git ls-files -z '*.js' | xargs -0 -r -n1 node --check
node --check dashboard/assets/app.js
if grep -RInI -E '\b(TODO|FIXME|XXX|HACK|PLACEHOLDER|STUB|TEMPORARY)\b' \
  --exclude='lint.sh' --exclude-dir='__pycache__' --exclude-dir='.turbo' --exclude-dir='node_modules' --exclude-dir='.venv' --exclude-dir='dist' --exclude-dir='build' \
  app.py apps packages scripts tests web infrastructure deploy dashboard; then
  echo "Implementation markers are not allowed in production source." >&2
  exit 1
fi
git diff --check
echo "Lint checks passed."
