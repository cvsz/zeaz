#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TOOLS="${KUBERNETES_TOOLS_DIR:-${TMPDIR:-/tmp}/zeaz-kubernetes-tools}"
EVIDENCE="${KUBERNETES_SCHEMA_EVIDENCE_FILE:-/tmp/zeaz-kubernetes-schema.sha256}"
KUBERNETES_VERSION="${KUBERNETES_SCHEMA_VERSION:-1.31.0}"

for tool in kustomize kubeconform; do
  [[ -x "$TOOLS/$tool" ]] || {
    echo "Missing $TOOLS/$tool; run scripts/ci/install-kubernetes-tools.sh first." >&2
    exit 1
  }
done

rendered="$(mktemp)"
evidence_tmp="$(mktemp)"
trap 'rm -f -- "$rendered" "$evidence_tmp"' EXIT
rm -f -- "$EVIDENCE"
"$TOOLS/kustomize" build "$ROOT/deploy/kubernetes" >"$rendered"
[[ -s "$rendered" ]] || { echo "Kustomize produced an empty manifest." >&2; exit 1; }
validation_output="$("$TOOLS/kubeconform" \
  -strict \
  -summary \
  -kubernetes-version "$KUBERNETES_VERSION" \
  <"$rendered")"
printf '%s\n' "$validation_output"
[[ "$validation_output" =~ Summary:\ ([1-9][0-9]*)\ resources\ found ]] || {
  echo "Kubeconform did not validate any rendered resources." >&2
  exit 1
}
[[ "$validation_output" =~ Invalid:\ 0,\ Errors:\ 0,\ Skipped:\ 0 ]] || {
  echo "Kubeconform did not validate every rendered resource." >&2
  exit 1
}
sha256sum "$rendered" | cut -d' ' -f1 >"$evidence_tmp"
install -m 0600 "$evidence_tmp" "$EVIDENCE"
echo "Rendered Kubernetes manifests passed strict schema validation."
