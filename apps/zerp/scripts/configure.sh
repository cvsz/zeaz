#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
ENV_FILE="${ROOT}/apps/zerp/.env"
if [[ -e "$ENV_FILE" ]]; then
  echo "Refusing to overwrite ${ENV_FILE}; review it manually." >&2
  exit 1
fi
cp "${ROOT}/apps/zerp/.env.example" "$ENV_FILE"
chmod 600 "$ENV_FILE"
echo "Created ${ENV_FILE}; set only non-secret local configuration values."
