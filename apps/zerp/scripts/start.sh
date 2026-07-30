#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"
npm run build --workspace @moopiew/zerp
exec npm run preview --workspace @moopiew/zerp -- --host 127.0.0.1 --port "${ZERP_PORT:-3001}"
