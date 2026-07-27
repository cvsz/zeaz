# scripts/apply.sh
#!/usr/bin/env bash

set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATES="$ROOT/templates"
TARGET="${1:-$ROOT}"

log() {
    printf "\033[1;32m==>\033[0m %s\n" "$*"
}

require() {
    command -v "$1" >/dev/null 2>&1 || {
        echo "Missing dependency: $1"
        exit 1
    }
}

copy_if_missing() {
    local src="$1"
    local dst="$2"

    mkdir -p "$(dirname "$dst")"

    if [[ ! -e "$dst" ]]; then
        cp -R "$src" "$dst"
        log "Created: ${dst#$ROOT/}"
    else
        log "Skip: ${dst#$ROOT/}"
    fi
}

require git

[[ -d "$TARGET/.git" ]] || {
    echo "Not a git repository."
    exit 1
}

log "Applying project structure..."

mkdir -p \
    "$TARGET/docs" \
    "$TARGET/assets" \
    "$TARGET/scripts" \
    "$TARGET/templates" \
    "$TARGET/excel" \
    "$TARGET/output"

for file in roadmap.th.md roadmap.en.md README.md; do
    if [[ -f "$TEMPLATES/$file" ]]; then
        copy_if_missing "$TEMPLATES/$file" "$TARGET/docs/$file"
    fi
done

if [[ -f "$TEMPLATES/.gitignore" ]]; then
    copy_if_missing "$TEMPLATES/.gitignore" "$TARGET/.gitignore"
fi

if [[ -f "$TEMPLATES/LICENSE" ]]; then
    copy_if_missing "$TEMPLATES/LICENSE" "$TARGET/LICENSE"
fi

log "Done."
