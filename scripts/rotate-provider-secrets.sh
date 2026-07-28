#!/usr/bin/env bash
# Inventory and orchestrate provider-secret rotation without exposing values.
#
# This command is intentionally a dry-run by default. Provider revocation APIs
# differ and must be implemented as reviewed hooks in ROTATION_HOOK_DIR. The
# orchestrator never sources an env file and never prints secret values.
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOK_DIR="${ROTATION_HOOK_DIR:-$ROOT/scripts/provider-rotation.d}"
OUT_DIR="${ROTATION_OUT_DIR:-$ROOT/output/secret-rotation}"
EXECUTE=0
APPROVED="${ROTATION_APPROVED:-}"

usage() {
  cat <<'EOF'
Usage: scripts/rotate-provider-secrets.sh [--dry-run] [--execute]

Dry-run is the default and prints only file names, permissions and variable
names. --execute runs reviewed executable hooks from ROTATION_HOOK_DIR after
ROTATION_APPROVED=YES is supplied; it does not invent or print new secrets.
EOF
}

for arg in "$@"; do
  case "$arg" in
    --dry-run) EXECUTE=0 ;;
    --execute) EXECUTE=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $arg" >&2; usage >&2; exit 2 ;;
  esac
done

mapfile -t ENV_FILES < <(find "$ROOT" /home/cvsz/zeaz-provider -maxdepth 2 -type f \
  \( -name '.env' -o -name '.env.*' -o -name '*.env' \) \
  ! -name '*.example' -print 2>/dev/null | sort -u)

if (( EXECUTE )); then
  [[ "$APPROVED" == "YES" ]] || { echo "Refusing execute: set ROTATION_APPROVED=YES after reviewing the dry-run." >&2; exit 3; }
  mkdir -p "$OUT_DIR"; chmod 700 "$OUT_DIR"
fi

echo "Secret rotation inventory (values intentionally hidden)"
printf '%-3s %-3s %s\n' "MODE" "PERM" "FILE"
for file in "${ENV_FILES[@]}"; do
  [[ -f "$file" ]] || continue
  perm=$(stat -c '%a' "$file")
  (( EXECUTE )) && { [[ "$perm" == "600" ]] || chmod 600 "$file"; }
  printf '%-3s %-3s %s\n' "$([[ "$perm" == "600" ]] && echo OK || echo WARN)" "$perm" "$file"
  awk -F= '/^[[:space:]]*(export[[:space:]]+)?[A-Za-z_][A-Za-z0-9_]*[[:space:]]*=/{line=$0; sub(/^[[:space:]]*(export[[:space:]]+)?/,"",line); sub(/[[:space:]]*=.*/,"",line); print "  " line}' "$file" | sort -u
done

if (( ! EXECUTE )); then
  echo "Dry-run only. No credentials were changed or revoked."
  exit 0
fi

[[ -d "$HOOK_DIR" ]] || { echo "No rotation hooks found at $HOOK_DIR; inventory complete."; exit 0; }
for hook in "$HOOK_DIR"/*.sh; do
  [[ -x "$hook" ]] || continue
  echo "Running reviewed rotation hook: $(basename "$hook")"
  ROTATION_ROOT="$ROOT" ROTATION_OUT_DIR="$OUT_DIR" "$hook"
done
echo "Rotation hooks completed. Verify provider dashboards, restart services, and run production checks."
