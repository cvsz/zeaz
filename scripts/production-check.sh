#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_ENV="$ROOT/.env.production"
CF_ENV="$ROOT/.env.cloudflare"

[[ -f "$APP_ENV" ]] || { echo "Missing $APP_ENV" >&2; exit 1; }
[[ -f "$CF_ENV" ]] || { echo "Missing $CF_ENV" >&2; exit 1; }
set -a
# shellcheck disable=SC1090
source "$APP_ENV"
# shellcheck disable=SC1090
source "$CF_ENV"
set +a

[[ "${REQUIRE_ADMIN_KEY:-}" == "true" ]] || { echo "REQUIRE_ADMIN_KEY must be true" >&2; exit 1; }
[[ -n "${ADMIN_KEY:-}" && "${ADMIN_KEY}" != "change-me-before-production" ]] || { echo "ADMIN_KEY must be configured" >&2; exit 1; }
[[ -n "${EMPLOYEE_KEY:-}" && "${EMPLOYEE_KEY}" != "change-me-employee-key" ]] || { echo "EMPLOYEE_KEY must be configured" >&2; exit 1; }
[[ -n "${KITCHEN_KEY:-}" && "${KITCHEN_KEY}" != "change-me-kitchen-key" ]] || { echo "KITCHEN_KEY must be configured" >&2; exit 1; }
for key in CLOUDFLARE_API_TOKEN CLOUDFLARE_ACCOUNT_ID CLOUDFLARE_ZONE_ID CLOUDFLARE_TUNNEL_ID CLOUDFLARE_TUNNEL_TOKEN; do
  [[ -n "${!key:-}" ]] || { echo "Missing $key" >&2; exit 1; }
done
python3 -m py_compile "$ROOT/app.py"
curl --fail --silent --show-error --max-time 10 "http://127.0.0.1:${PORT:-8000}/api/health" >/dev/null || {
  echo "Local health endpoint failed" >&2; exit 1;
}
curl --fail --silent --show-error --max-time 10 "http://127.0.0.1:${PORT:-8000}/api/menu" >/dev/null || {
  echo "Local app health check failed; start moopiew.service first" >&2; exit 1;
}
curl --fail --silent --show-error --max-time 10 "http://127.0.0.1:8080/api/menu" >/dev/null || {
  echo "Local proxy health check failed; start moopiew-proxy.service first" >&2; exit 1;
}
curl --fail --silent --show-error --max-time 20 "https://${MOOPIEW_HOSTNAME:-moopiew.zeaz.dev}/api/menu" >/dev/null || {
  echo "Public tunnel health check failed" >&2; exit 1;
}
echo "Production checks passed."
