#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
command -v git >/dev/null || { echo "Missing dependency: git" >&2; exit 1; }
"$ROOT/scripts/apply.sh" "$ROOT"
printf 'Framework is ready. Try: ./scripts/generate.sh examples/cafe.yaml output/cafe\n'
