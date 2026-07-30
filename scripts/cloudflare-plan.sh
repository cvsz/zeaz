#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${CLOUDFLARE_ENV_FILE:-$ROOT/.env.cloudflare}"
STACK="$ROOT/infrastructure/terraform/cloudflare"

[[ -f "$ENV_FILE" && ! -L "$ENV_FILE" ]] || {
  echo "Cloudflare environment must be a regular file: $ENV_FILE" >&2
  exit 1
}
mode="$(stat -c '%a' "$ENV_FILE")"
(( (8#$mode & 8#077) == 0 )) || {
  echo "Cloudflare environment must not be group/world accessible: $ENV_FILE" >&2
  exit 1
}
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

for key in CLOUDFLARE_API_TOKEN CLOUDFLARE_ACCOUNT_ID CLOUDFLARE_ZONE_ID CLOUDFLARE_TUNNEL_ID; do
  [[ -n "${!key:-}" ]] || { echo "Missing $key in $ENV_FILE" >&2; exit 1; }
done
[[ -n "${PIEWDASH_ACCESS_ALLOWED_EMAILS:-}" ]] || {
  echo "Missing PIEWDASH_ACCESS_ALLOWED_EMAILS JSON array in $ENV_FILE" >&2
  exit 1
}

TF_BIN="${TERRAFORM_BIN:-$ROOT/tools/bin/terraform}"
command -v "$TF_BIN" >/dev/null || { echo "Terraform not found. See infrastructure/terraform/cloudflare/README.md" >&2; exit 1; }

export TF_IN_AUTOMATION=1 TF_INPUT=0
export TF_VAR_cloudflare_api_token="$CLOUDFLARE_API_TOKEN"
export TF_VAR_cloudflare_account_id="$CLOUDFLARE_ACCOUNT_ID"
export TF_VAR_cloudflare_zone_id="$CLOUDFLARE_ZONE_ID"
export TF_VAR_cloudflare_tunnel_id="$CLOUDFLARE_TUNNEL_ID"
export TF_VAR_moopiew_hostname="${MOOPIEW_HOSTNAME:-moopiew.zeaz.dev}"
export TF_VAR_moopiew_origin="${MOOPIEW_ORIGIN:-http://127.0.0.1:8080}"
export TF_VAR_piewdash_hostname="${PIEWDASH_HOSTNAME:-piewdash.zeaz.dev}"
export TF_VAR_piewdash_origin="${PIEWDASH_ORIGIN:-http://127.0.0.1:80}"
export TF_VAR_zerp_hostname="${ZERP_HOSTNAME:-zerp.zeaz.dev}"
export TF_VAR_zerp_origin="${ZERP_ORIGIN:-http://127.0.0.1:80}"
export TF_VAR_cmeerp_hostname="${CMEERP_HOSTNAME:-cme.zeaz.dev}"
export TF_VAR_cmeerp_origin="${CMEERP_ORIGIN:-http://127.0.0.1:8001}"
export TF_VAR_piewdash_access_allowed_emails="$PIEWDASH_ACCESS_ALLOWED_EMAILS"

"$TF_BIN" -chdir="$STACK" fmt -check -recursive
if [[ "${TERRAFORM_BACKEND_TYPE:-local}" == "r2" ]]; then
  "$ROOT/scripts/cloudflare-state.sh" init
else
  "$TF_BIN" -chdir="$STACK" init
fi
"$TF_BIN" -chdir="$STACK" validate
"$TF_BIN" -chdir="$STACK" plan -out=tfplan
"$TF_BIN" -chdir="$STACK" show -no-color tfplan
