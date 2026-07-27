#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="${1:?Usage: generate.sh CONFIG.yaml OUTPUT_DIR}"
OUT="${2:?Usage: generate.sh CONFIG.yaml OUTPUT_DIR}"
[[ -f "$CONFIG" ]] || { echo "Config not found: $CONFIG" >&2; exit 1; }

value() { awk -F': *' -v key="$1" '$1 == key {sub(/^[^:]*: */, ""); print; exit}' "$CONFIG"; }
NAME="$(value business_name)"; CATEGORY="$(value category)"; LOCATION="$(value location)"; CUSTOMER="$(value target_customer)"
for field in NAME CATEGORY LOCATION CUSTOMER; do [[ -n "${!field}" ]] || { echo "Missing ${field,,} in $CONFIG" >&2; exit 1; }; done
for field in NAME CATEGORY LOCATION CUSTOMER; do [[ "${!field}" != *'&'* && "${!field}" != *'|'* && "${!field}" != *'/'* ]] || { echo "Unsupported character in ${field,,}" >&2; exit 1; }; done
[[ ! -e "$OUT" ]] || { echo "Refusing to overwrite existing output: $OUT" >&2; exit 1; }

mkdir -p "$OUT"/{docs,finance,assets}
replace() { sed -e "s|{{BUSINESS_NAME}}|$NAME|g" -e "s|{{CATEGORY}}|$CATEGORY|g" -e "s|{{LOCATION}}|$LOCATION|g" -e "s|{{TARGET_CUSTOMER}}|$CUSTOMER|g" "$1" > "$2"; }
replace "$ROOT/templates/business-kit.en.md" "$OUT/docs/business-kit.en.md"
replace "$ROOT/templates/business-kit.th.md" "$OUT/docs/business-kit.th.md"
cp "$ROOT/excel/financial-model.csv" "$OUT/finance/financial-model.csv"
cp "$ROOT/assets/logo.svg" "$ROOT/assets/banner.svg" "$OUT/assets/"
cp "$CONFIG" "$OUT/business.yaml"
printf 'Generated business kit: %s\n' "$OUT"
