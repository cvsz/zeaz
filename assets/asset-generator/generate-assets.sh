#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
for directory in brand-kit food/ai-generated marketing product print social; do
  mkdir -p "$ROOT/$directory"
done
printf 'Asset directory structure is ready at %s\n' "$ROOT"
