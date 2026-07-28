#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
python3 -m py_compile app.py
find scripts assets/asset-generator -type f -name '*.sh' -print0 | xargs -0 -n1 bash -n
git diff --check
echo "Lint checks passed."
