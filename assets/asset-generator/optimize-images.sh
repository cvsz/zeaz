#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if ! command -v cwebp >/dev/null 2>&1 && ! command -v svgo >/dev/null 2>&1; then
  echo "No image optimizer installed. Install cwebp and/or svgo to optimize images." >&2
  exit 0
fi
find "$ROOT" -type f \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.svg' \) -print
echo "Review the listed files, then run your approved image optimization workflow. Source assets are never overwritten by this script."
