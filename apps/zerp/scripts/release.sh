#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"
./apps/zerp/scripts/verify.sh
echo "zERP release artifact is apps/zerp/dist; deploy it through the reviewed systemd/Caddy path."
