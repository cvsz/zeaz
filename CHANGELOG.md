# Changelog

## 1.0.0 — 2026-07-28

- Added the live engineering dashboard, CI evidence reports, Docker deployment,
  Kubernetes manifests, and the `piewdash.zeaz.dev` Cloudflare route.
- Restricted the engineering dashboard with exact-email Cloudflare Access and
  environment-backed Caddy Basic Auth defense in depth.
- Consolidated SQLite schema ownership into checksummed migrations with
  concurrency and legacy-upgrade regression coverage.
- Added strict OpenAPI route validation, rendered Kubernetes schema validation,
  Python/npm vulnerability audits, CycloneDX release SBOMs, and signed build
  provenance.
- Hardened SCB authorization callbacks with atomic expiring state consumption
  and feature-gated S256 PKCE using encrypted one-time verifiers.
- Added cross-process SQLite serialization for critical commerce mutations,
  unique order inventory consumption, and isolated backup restore drills.
- Added tagged GHCR publication for application and dashboard images with OCI
  SBOMs, maximum BuildKit provenance, and GitHub digest attestations.
- Hardened the isolated API smoke harness against port-allocation races and
  preserved server diagnostics on failure.
- Added dedicated Fernet encryption for onboarding document objects plus
  hash-verified legacy migration and dry-run-safe tombstone retention tooling.
- Made provider document-policy versioning concurrency-safe with end-exclusive
  UTC windows, read-only history, expired-upload rejection, audit coverage and
  provider-specific integration matrices.
- Added catalog/chat contract tests for every prioritized AI adapter and an
  explicit runtime denylist for suspended or operationally disallowed
  providers.
- Added exact reverse parity between runtime handler routes and the canonical
  OpenAPI operations, including reviewed mappings for regex routes.
- Added additive provider document-policy schema and Thailand provider
  references for Grab, Bolt, LINE MAN and Lalamove.
- Added database-driven requirement APIs, secure owner document upload,
  verification, deletion and history endpoints, plus the reusable upload UI.

- Established MooPiew as a restaurant ordering and delivery platform with a
  customer storefront and owner operations console.
- Added pickup/delivery orders, distance quotations, tracking codes and
  server-sent delivery status updates.
- Added rider and merchant applications, review workflows, rider management
  and order assignment.
- Added menu display ordering, inventory recipes/movements, coupons, loyalty,
  receipts and VAT tax-invoice controls.
- Added Cloudflare Tunnel deployment, production checks, database backups and
  documented security boundaries.
- Added SCB integration safeguards: payment features remain opt-in and payment
  completion requires provider inquiry rather than client/callback claims.

## 0.1.0 — Foundation

- Created the reusable business-kit templates, bilingual documents and shell
  generation utilities.
