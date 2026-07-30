#!/usr/bin/env bash
set -Eeuo pipefail

cat >&2 <<'EOF'
zERP has no independent persistent state. Back up the MooPiew SQLite database,
uploaded-document storage, and deployment configuration using the repository
root backup runbook. This command intentionally refuses to create an incomplete
or misleading frontend-only backup.
EOF
exit 2
