#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_ENV="$ROOT/.env.production"
PAYMENT_ENV="$ROOT/.env.payment"

[[ -f "$APP_ENV" ]] || { echo "Missing $APP_ENV" >&2; exit 1; }
[[ -f "$PAYMENT_ENV" ]] || { echo "Missing $PAYMENT_ENV" >&2; exit 1; }
set -a
# shellcheck disable=SC1090
source "$APP_ENV"
# shellcheck disable=SC1090
source "$PAYMENT_ENV"
set +a

required=(SCB_API_KEY SCB_API_SECRET SCB_BILLER_ID SCB_QR_CREATE_ENDPOINT SCB_QR_INQUIRY_ENDPOINT SCB_TOKEN_ENCRYPTION_KEY SCB_PAYMENT_CONFIRMATION_URL)
for key in "${required[@]}"; do
  [[ -n "${!key:-}" ]] || { echo "Missing required SCB value: $key" >&2; exit 1; }
done

[[ "${PAYMENT_ENVIRONMENT:-}" == "sandbox" || "${PAYMENT_ENVIRONMENT:-}" == "production" ]] || { echo "PAYMENT_ENVIRONMENT must be sandbox or production" >&2; exit 1; }
[[ "${SCB_PRODUCT:-}" == "qr_api" ]] || { echo "SCB_PRODUCT must be qr_api for Mae Manee QR" >&2; exit 1; }
[[ "${SCB_OAUTH_MODE:-}" == "authorization_code" ]] || { echo "SCB_OAUTH_MODE must be authorization_code" >&2; exit 1; }
[[ "${SCB_PAYMENT_OAUTH_MODE:-client_credentials}" == "authorization_code" || "${SCB_PAYMENT_OAUTH_MODE:-client_credentials}" == "client_credentials" ]] || { echo "SCB_PAYMENT_OAUTH_MODE must be authorization_code or client_credentials" >&2; exit 1; }

if [[ "${SCB_MTLS_REQUIRED:-false}" == "true" ]]; then
  [[ -r "${SCB_CLIENT_CERT_FILE:-}" && -r "${SCB_CLIENT_KEY_FILE:-}" ]] || { echo "SCB mTLS requires readable certificate and private-key files" >&2; exit 1; }
fi

if [[ "${SCB_DIRECT_DEBIT_ENABLED:-false}" == "true" ]]; then
  direct_required=(SCB_DIRECT_DEBIT_MERCHANT_ID SCB_DIRECT_DEBIT_SUB_ACCOUNT_ID SCB_DIRECT_DEBIT_MERCHANT_ACCOUNT SCB_DIRECT_DEBIT_ENCRYPTION_PUBLIC_KEY_FILE)
  for key in "${direct_required[@]}"; do
    [[ -n "${!key:-}" ]] || { echo "Missing required Direct Debit value: $key" >&2; exit 1; }
  done
  [[ -s "$SCB_DIRECT_DEBIT_ENCRYPTION_PUBLIC_KEY_FILE" ]] || { echo "Missing Direct Debit public-key file" >&2; exit 1; }
fi

if [[ "${SCB_PAYMENT_OAUTH_MODE:-client_credentials}" == "authorization_code" ]]; then
  status=$(curl --silent --show-error --fail --max-time 10 "http://127.0.0.1:${PORT:-8000}/api/admin/scb/auth/status" -H "X-Admin-Key: ${ADMIN_KEY}")
  STATUS_JSON="$status" python3 - <<'PY'
import json, os
from datetime import datetime, timezone

data=json.loads(os.environ['STATUS_JSON'])
if not data.get('connected'):
    raise SystemExit('SCB payment authorization is missing. Complete Owner dashboard authorization first.')
expires=datetime.fromisoformat(data['access_expires_at'])
if expires <= datetime.now(timezone.utc):
    raise SystemExit('SCB payment access token is expired. Reconnect SCB EASY before enabling payments.')
print('SCB payment authorization: ready')
PY
else
  echo "SCB payment authentication: Client Credentials configured"
fi

if [[ "${PAYMENTS_ENABLED:-false}" != "true" || "${SCB_ENABLED:-false}" != "true" ]]; then
  echo "SCB configuration is valid, but payments remain safely disabled."
  exit 0
fi

echo "SCB live payment configuration is ready."
