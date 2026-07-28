#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_ENV="$ROOT/.env.production"
CF_ENV="$ROOT/.env.cloudflare"

[[ -f "$APP_ENV" ]] || { echo "Missing $APP_ENV" >&2; exit 1; }
[[ -f "$CF_ENV" ]] || { echo "Missing $CF_ENV" >&2; exit 1; }
check_secret_file() {
  local path="$1" mode owner
  [[ ! -L "$path" && -f "$path" ]] || {
    echo "Secret configuration must be a regular, non-symlink file: $path" >&2
    exit 1
  }
  mode="$(stat -c '%a' "$path")"
  owner="$(stat -c '%u' "$path")"
  [[ "$owner" == "$(id -u)" ]] || {
    echo "Secret configuration must be owned by uid $(id -u): $path" >&2
    exit 1
  }
  (( (8#$mode & 8#077) == 0 )) || {
    echo "Secret configuration must not be group/world accessible: $path ($mode)" >&2
    exit 1
  }
}
check_secret_file "$APP_ENV"
check_secret_file "$CF_ENV"
for optional in "$ROOT/.env.payment" "$ROOT/.env.ai"; do
  [[ ! -e "$optional" ]] || check_secret_file "$optional"
done
set -a
# shellcheck disable=SC1090
source "$APP_ENV"
[[ -f "$ROOT/.env.payment" ]] && source "$ROOT/.env.payment"
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
python3 - <<'PY'
import os
from cryptography.fernet import Fernet

try:
    Fernet(os.environ["DOCUMENT_ENCRYPTION_KEY"].encode())
except (KeyError, TypeError, ValueError) as error:
    raise SystemExit("DOCUMENT_ENCRYPTION_KEY must be a valid dedicated Fernet key") from error
PY
python3 -m py_compile "$ROOT/app.py"
check_url() {
  local url="$1" attempts=0
  while (( attempts < 10 )); do
    curl --fail --silent --show-error --max-time 10 "$url" >/dev/null && return 0
    attempts=$((attempts + 1)); sleep 1
  done
  return 1
}
check_url "http://127.0.0.1:${PORT:-8000}/api/health" || {
  echo "Local health endpoint failed" >&2; exit 1;
}
check_url "http://127.0.0.1:${PORT:-8000}/api/menu" || {
  echo "Local app health check failed; start moopiew.service first" >&2; exit 1;
}
check_url "http://127.0.0.1:8080/api/menu" || {
  echo "Local proxy health check failed; start moopiew-proxy-system@$USER.service" >&2; exit 1;
}
check_url "http://127.0.0.1:8082/api/health" || {
  echo "Local engineering dashboard failed; start moopiew-dashboard.service" >&2; exit 1;
}
check_url "https://${MOOPIEW_HOSTNAME:-moopiew.zeaz.dev}/api/menu" || {
  echo "Public tunnel health check failed" >&2; exit 1;
}
check_url "https://${PIEWDASH_HOSTNAME:-piewdash.zeaz.dev}/api/health" || {
  echo "Public engineering dashboard failed" >&2; exit 1;
}
echo "Production checks passed."
