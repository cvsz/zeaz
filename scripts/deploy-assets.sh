#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ASSET_S3_URI="${ASSET_S3_URI:?Set ASSET_S3_URI, for example s3://cdn.example.com/moopiew-assets}"
[[ "$ASSET_S3_URI" == s3://* ]] || { echo "ASSET_S3_URI must start with s3://" >&2; exit 1; }
command -v aws >/dev/null 2>&1 || { echo "Missing dependency: aws" >&2; exit 1; }
"$ROOT/assets/asset-generator/validate-assets.sh"

args=(s3 sync "$ROOT/assets" "$ASSET_S3_URI" --exclude 'asset-generator/*' --exclude '*.psd')
if [[ "${ASSET_SYNC_DELETE:-false}" == "true" ]]; then args+=(--delete); fi
aws "${args[@]}"
echo "Assets deployed to $ASSET_S3_URI"
