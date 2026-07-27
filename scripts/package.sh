#!/usr/bin/env bash
set -Eeuo pipefail

SOURCE="${1:?Usage: package.sh OUTPUT_DIR [archive.zip]}"
[[ -d "$SOURCE" ]] || { echo "Directory not found: $SOURCE" >&2; exit 1; }
ARCHIVE="${2:-${SOURCE%/}.zip}"
command -v zip >/dev/null || { echo "Missing dependency: zip" >&2; exit 1; }
[[ ! -e "$ARCHIVE" ]] || { echo "Refusing to overwrite: $ARCHIVE" >&2; exit 1; }
SOURCE_ABS="$(cd "$SOURCE" && pwd)"
ARCHIVE_ABS="$(cd "$(dirname "$ARCHIVE")" && pwd)/$(basename "$ARCHIVE")"
(cd "$(dirname "$SOURCE_ABS")" && zip -qr "$ARCHIVE_ABS" "$(basename "$SOURCE_ABS")")
printf 'Created %s\n' "$ARCHIVE"
