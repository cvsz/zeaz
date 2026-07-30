#!/usr/bin/env bash
set -Eeuo pipefail

cat >&2 <<'EOF'
zERP has no independent persistent state. Restore the MooPiew database,
uploaded-document storage, and deployment configuration using the repository
root restore runbook before starting zERP.
EOF
exit 2
