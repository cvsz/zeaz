#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_ENV="$ROOT/.env.production"
[[ -f "$APP_ENV" ]] && { set -a; source "$APP_ENV"; set +a; }
PAYMENT_ENV="$ROOT/.env.payment"
[[ -f "$PAYMENT_ENV" ]] && { set -a; source "$PAYMENT_ENV"; set +a; }
origin="http://127.0.0.1:${PORT:-8000}"
curl --fail --silent --show-error --max-time 10 "$origin/api/health"
curl --fail --silent --show-error --max-time 10 "$origin/api/ready"
printf '\nPlatform health checks passed.\n'
