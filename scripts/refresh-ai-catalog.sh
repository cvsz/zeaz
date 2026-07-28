#!/usr/bin/env bash
# Refresh the ignored runtime credentials, inspect provider health, then prove
# that each configured free-model provider can complete one short request.
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

./scripts/sync-ai-credentials.sh
./scripts/check-ai-provider-keys.sh
systemctl --user restart moopiew.service
for attempt in 1 2 3 4 5; do
    systemctl --user is-active --quiet moopiew.service && break
    sleep 1
done
systemctl --user is-active --quiet moopiew.service || { echo "MooPiew service did not start." >&2; exit 1; }
./scripts/ai-preflight.sh --smoke
echo "ZEAZ AI catalog refresh completed."
