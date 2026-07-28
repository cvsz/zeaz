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
`CAP_NET_BIND_SERVICE`. Public access must be protected with Cloudflare Access.

Release archives are produced only after validation and container builds by
`.github/workflows/release.yml` and include a SHA-256 manifest. Signing,
provenance attestation, and image publication remain production-readiness gaps.
