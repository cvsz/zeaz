#!/usr/bin/env bash
set -Eeuo pipefail

BASE_URL="${ZERP_HEALTH_URL:-http://127.0.0.1:${ZERP_PORT:-3001}}"
curl --fail --silent --show-error --location --max-time 10 "${BASE_URL}/" >/dev/null
echo "zERP web health: ok (${BASE_URL})"
