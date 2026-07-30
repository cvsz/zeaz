#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"
command -v npm >/dev/null || { echo "npm is required" >&2; exit 1; }
npm ci
./apps/zerp/scripts/verify.sh
