# Deployment

The supported application deployment is Python behind Caddy and Cloudflare
Tunnel using the reviewed files under `deploy/`; follow
[`docs/cloudflare-deployment.md`](docs/cloudflare-deployment.md). Terraform
under `infrastructure/terraform/cloudflare` owns Cloudflare resources.

The application and engineering dashboard have non-root Docker images. Local
dashboard deployment uses `dashboard/compose.yml`; the Kubernetes deployment is
owned by `deploy/kubernetes/` and preserves SQLite's single-replica constraint
with `Recreate`, a `ReadWriteOnce` PVC, external secret references, probes,
resource limits, restricted pod security, and default-deny networking. Follow
`deploy/kubernetes/README.md` and replace example hosts and mutable image tags
with environment-specific hosts and immutable digests.

The supported single-host dashboard service is
`deploy/systemd/moopiew-dashboard.service`, listening only on
`127.0.0.1:8082`. The Cloudflare Tunnel maps `piewdash.zeaz.dev` to that
loopback origin through Caddy. Because the shared tunnel wildcard uses port 80,
install `deploy/systemd/moopiew-proxy-system@.service` as the system-level
reverse proxy; it runs as the selected user with only
`CAP_NET_BIND_SERVICE`. Public access is protected by a Terraform-managed
Cloudflare Access application restricted to exact operator emails and by
environment-backed Caddy Basic Auth at the origin. Keep `.env.dashboard` mode
`0600`; anonymous requests must never return dashboard data.

The application requires a dedicated `DOCUMENT_ENCRYPTION_KEY` before document
onboarding is enabled. Run the hash-verified legacy migration and enable
`moopiew-document-retention.timer` as documented in
[`docs/operations.md`](docs/operations.md); never deploy a plaintext document
directory.

Release archives and GHCR images are produced only after validation and
container builds by `.github/workflows/release.yml`. Each release bundle
includes npm and Python CycloneDX SBOMs plus a SHA-256 manifest. The application
and dashboard OCI images include BuildKit SBOM/provenance attestations and
GitHub signs a separate Sigstore-backed build-provenance attestation over each
published digest. No mutable `latest` tag is published. Verify artifacts before
deployment:

```bash
sha256sum --check moopiew-<version>.sha256
gh attestation verify moopiew-<version>.zip --repo cvsz/zeaz
gh attestation verify \
  oci://ghcr.io/cvsz/zeaz/moopiew:<version> --repo cvsz/zeaz
gh attestation verify \
  oci://ghcr.io/cvsz/zeaz/dashboard:<version> --repo cvsz/zeaz
```

Resolve the verified tag to its digest and deploy
`ghcr.io/cvsz/zeaz/<image>@sha256:<digest>`; Kubernetes manifests must never
consume a mutable release tag. Roll back by redeploying the previous verified
digest and restoring a compatible verified database backup when a migration
was applied.
