#!/usr/bin/env bash
# Reorders a local payment environment file using the reviewed template without
# printing its values. It writes a same-permission backup before replacement.
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:-$ROOT/.env.payment}"
TEMPLATE="$ROOT/.env.payment.example"

[[ -f "$TARGET" && -f "$TEMPLATE" ]] || { echo "Missing payment environment file or template" >&2; exit 1; }

declare -A values
while IFS= read -r line || [[ -n "$line" ]]; do
  if [[ "$line" =~ ^([A-Z][A-Z0-9_]*)=(.*)$ ]]; then
    key="${BASH_REMATCH[1]}"
    case "$key" in SCB_ACCESS_TOKEN|SCB_REFRESH_TOKEN|SCB_RESOURCE_OWNER_ID) continue;; esac
    values["$key"]="${BASH_REMATCH[2]}"
  fi
done < "$TARGET"

backup="$(mktemp "${TARGET}.backup.XXXXXX")"
tmp="$(mktemp "${TARGET}.tmp.XXXXXX")"
trap 'rm -f "$tmp"' EXIT
cp --preserve=mode "$TARGET" "$backup"
chmod --reference="$TARGET" "$tmp"

while IFS= read -r line || [[ -n "$line" ]]; do
  if [[ "$line" =~ ^([A-Z][A-Z0-9_]*)= ]]; then
    key="${BASH_REMATCH[1]}"
    if [[ -v "values[$key]" ]]; then
      printf '%s=%s\n' "$key" "${values[$key]}" >> "$tmp"
      unset 'values[$key]'
    fi
  else
    printf '%s\n' "$line" >> "$tmp"
  fi
done < "$TEMPLATE"

if ((${#values[@]})); then
  printf '\n# Local-only values retained from the previous configuration.\n' >> "$tmp"
  while IFS= read -r key; do printf '%s=%s\n' "$key" "${values[$key]}" >> "$tmp"; done < <(printf '%s\n' "${!values[@]}" | LC_ALL=C sort)
fi

mv "$tmp" "$TARGET"
trap - EXIT
echo "Normalized $(basename "$TARGET"); backup: $(basename "$backup")"
