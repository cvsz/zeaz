#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/cloudflare-terraform-env.sh
source "$SCRIPT_DIR/lib/cloudflare-terraform-env.sh"

usage() {
  cat <<'EOF'
Usage:
  ./scripts/cloudflare-apply.sh [options]

Creates a reviewed Cloudflare Terraform plan. DNS records that already exist
are imported into state before planning, preventing Cloudflare error 81053.
The default mode never applies changes.

Options:
  --apply          Apply the saved plan after it is displayed. Applying a saved
                   Terraform plan does not ask for an additional confirmation.
  --skip-import    Do not run the DNS import/reconciliation step.
  --all-dns        Reconcile all managed DNS records instead of zai/auth/zdash.
  --plan-file PATH Save the plan at PATH. Default: Terraform stack/tfplan.
  -h, --help

Examples:
  ./scripts/cloudflare-apply.sh
  ./scripts/cloudflare-apply.sh --apply
  ./scripts/cloudflare-apply.sh --all-dns
EOF
}

apply_plan=false
reconcile_dns=true
all_dns=false
plan_file=""

while (($#)); do
  case "$1" in
    --apply)
      apply_plan=true
      ;;
    --skip-import)
      reconcile_dns=false
      ;;
    --all-dns)
      all_dns=true
      ;;
    --plan-file)
      shift
      [[ $# -gt 0 ]] || {
        echo "--plan-file requires a path" >&2
        exit 2
      }
      plan_file="$1"
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

cloudflare_require_command curl
cloudflare_require_command jq
cloudflare_load_terraform_env
cloudflare_terraform_init

if [[ -z "$plan_file" ]]; then
  plan_file="$CLOUDFLARE_STACK/tfplan"
elif [[ "$plan_file" != /* ]]; then
  plan_file="$CLOUDFLARE_ROOT/$plan_file"
fi

if [[ "$reconcile_dns" == true ]]; then
  if [[ "$all_dns" == true ]]; then
    "$SCRIPT_DIR/cloudflare-import-dns.sh" --all
  else
    "$SCRIPT_DIR/cloudflare-import-dns.sh" zai auth zdash
  fi
fi

"$CLOUDFLARE_TF_BIN" -chdir="$CLOUDFLARE_STACK" fmt -check -recursive
"$CLOUDFLARE_TF_BIN" -chdir="$CLOUDFLARE_STACK" validate

if [[ "${MANAGE_TUNNEL_CONFIG:-false}" == "true" ]]; then
  if ! "$CLOUDFLARE_TF_BIN" -chdir="$CLOUDFLARE_STACK" state list 2>/dev/null |
    grep -Fxq 'cloudflare_zero_trust_tunnel_cloudflared_config.moopiew[0]'; then
    cat >&2 <<'EOF'
Refusing to manage the tunnel configuration because the existing remote tunnel
configuration is not present in Terraform state.

Import and review the live tunnel configuration first, or set:
  MANAGE_TUNNEL_CONFIG=false

This guard prevents unrelated ingress routes from being replaced.
EOF
    exit 1
  fi
fi

backup_dir="$CLOUDFLARE_ROOT/backups/cloudflare"
mkdir -p "$backup_dir"
state_backup="$backup_dir/terraform-state-before-plan-$(date -u +%Y%m%dT%H%M%SZ).json"
"$CLOUDFLARE_TF_BIN" -chdir="$CLOUDFLARE_STACK" state pull >"$state_backup"
chmod 600 "$state_backup"
echo "Terraform state backup: $state_backup"

mkdir -p "$(dirname "$plan_file")"
rm -f "$plan_file"
"$CLOUDFLARE_TF_BIN" -chdir="$CLOUDFLARE_STACK" plan -out="$plan_file"
chmod 600 "$plan_file"

echo
echo "================ Terraform plan ================"
"$CLOUDFLARE_TF_BIN" -chdir="$CLOUDFLARE_STACK" show -no-color "$plan_file"
echo "=================================================="
echo "Saved plan: $plan_file"

if [[ "$apply_plan" != true ]]; then
  echo
  echo "Plan only. Review it, then run:"
  echo "  ./scripts/cloudflare-apply.sh --apply"
  exit 0
fi

echo
echo "Applying the saved Terraform plan..."
"$CLOUDFLARE_TF_BIN" -chdir="$CLOUDFLARE_STACK" apply "$plan_file"

echo
echo "Cloudflare apply completed."

zdash_origin="${ZDASH_ORIGIN:-http://127.0.0.1:18080}"
zdash_hostname="${ZDASH_HOSTNAME:-zdash.zeaz.dev}"

if curl --fail --silent --show-error "$zdash_origin/gateway-health" >/dev/null; then
  echo "zDash origin healthy: $zdash_origin/gateway-health"
else
  echo "WARNING: zDash origin health check failed: $zdash_origin/gateway-health" >&2
fi

remote_status="$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' \
  --head "https://$zdash_hostname" || true)"
if [[ -n "$remote_status" ]]; then
  echo "Remote zDash HTTP status: $remote_status"
fi
