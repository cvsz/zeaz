#!/usr/bin/env bash
set -Eeuo pipefail

BASE_URL="${API_MONITOR_URL:-https://moopiew.zeaz.dev}"
BASE_URL="${BASE_URL%/}"
for endpoint in /api/health /api/ready /api/menu /api/status; do
  result="$(curl --silent --show-error --fail --max-time 15 --output /dev/null --write-out '%{http_code} %{time_total}' "$BASE_URL$endpoint")"
  printf '%-18s %s\n' "$endpoint" "$result"
done
