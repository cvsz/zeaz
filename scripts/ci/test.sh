#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python3 -m py_compile "$ROOT/app.py"
node --check "$ROOT/web/app.js"
node --check "$ROOT/web/admin.js"
node --check "$ROOT/web/ops.js"
if [[ -d "$ROOT/node_modules" ]]; then (cd "$ROOT" && npm run typecheck); fi
echo "Platform checks passed."
