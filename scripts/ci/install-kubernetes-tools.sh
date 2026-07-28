#!/usr/bin/env bash
set -Eeuo pipefail

DESTINATION="${1:-${TMPDIR:-/tmp}/zeaz-kubernetes-tools}"
KUSTOMIZE_VERSION="5.8.1"
KUBECONFORM_VERSION="0.8.0"

case "$(uname -m)" in
  x86_64|amd64)
    architecture="amd64"
    kustomize_sha="029a7f0f4e1932c52a0476cf02a0fd855c0bb85694b82c338fc648dcb53a819d"
    kubeconform_sha="9bc2bffbf71f261128533edaf912153948b7ff238f9a531ae6d34466ec287883"
    ;;
  aarch64|arm64)
    architecture="arm64"
    kustomize_sha="0953ea3e476f66d6ddfcd911d750f5167b9365aa9491b2326398e289fef2c142"
    kubeconform_sha="1f53fc8e81258197a35e8603054162a5af1de8c5af13746c71ab680d9534ed87"
    ;;
  *)
    echo "Unsupported architecture: $(uname -m)" >&2
    exit 1
    ;;
esac

work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
mkdir -p "$DESTINATION"

kustomize_archive="kustomize_v${KUSTOMIZE_VERSION}_linux_${architecture}.tar.gz"
kubeconform_archive="kubeconform-linux-${architecture}.tar.gz"
curl --proto '=https' --tlsv1.2 --fail --silent --show-error --location \
  "https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize/v${KUSTOMIZE_VERSION}/${kustomize_archive}" \
  --output "$work/$kustomize_archive"
curl --proto '=https' --tlsv1.2 --fail --silent --show-error --location \
  "https://github.com/yannh/kubeconform/releases/download/v${KUBECONFORM_VERSION}/${kubeconform_archive}" \
  --output "$work/$kubeconform_archive"

printf '%s  %s\n' "$kustomize_sha" "$work/$kustomize_archive" | sha256sum --check --status
printf '%s  %s\n' "$kubeconform_sha" "$work/$kubeconform_archive" | sha256sum --check --status
tar -xzf "$work/$kustomize_archive" -C "$work" kustomize
tar -xzf "$work/$kubeconform_archive" -C "$work" kubeconform
install -m 0755 "$work/kustomize" "$DESTINATION/kustomize"
install -m 0755 "$work/kubeconform" "$DESTINATION/kubeconform"
printf 'Installed kustomize %s and kubeconform %s in %s\n' \
  "$KUSTOMIZE_VERSION" "$KUBECONFORM_VERSION" "$DESTINATION"
