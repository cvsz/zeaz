# Moopiew Central Asset Repository

This directory contains the approved visual, brand and media assets used by the
Moopiew customer web, operations dashboards and future merchant applications.

## Usage policy

All assets are confidential and proprietary to Moopiew. They may be used only
in official Moopiew products, approved campaigns and partner integrations.
Do not redistribute assets or use them for unrelated third-party projects.

## Asset pipeline

The scripts in `asset-generator/` keep the package consistent:

1. `./assets/asset-generator/generate-assets.sh` creates the standard directory tree.
2. `./assets/asset-generator/validate-assets.sh` checks required files and JSON syntax.
3. `./assets/asset-generator/optimize-images.sh` reports images that can be optimized.

For an S3-compatible CDN sync, set `ASSET_S3_URI` and run
`./scripts/deploy-assets.sh`. The deployment script validates first and never
enables public ACLs or deletes remote files unless explicitly requested.

For brand questions or approved asset requests, contact `brand@moopiew.com`.
