#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/optimized"
mkdir -p "$OUT"
count=0
while IFS= read -r -d '' source; do
  relative="${source#"$ROOT/"}"
  target="$OUT/${relative%.*}"
  case "${source##*.}" in
    svg|SVG)
      if command -v svgo >/dev/null 2>&1; then mkdir -p "$(dirname "$target")"; svgo --input "$source" --output "$target.svg" >/dev/null; count=$((count+1)); fi ;;
    png|PNG|jpg|JPG|jpeg|JPEG)
      if command -v cwebp >/dev/null 2>&1; then mkdir -p "$(dirname "$target")"; cwebp -quiet "$source" -o "$target.webp"; count=$((count+1)); fi ;;
  esac
done < <(find "$ROOT" -type f \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.svg' \) -not -path "$OUT/*" -print0)
echo "Optimized $count asset(s) into $OUT; source files were preserved."
