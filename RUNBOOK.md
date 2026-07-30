# Runbook

## Service failure

1. Run `./scripts/production-check.sh` and `./scripts/health-check.sh`.
2. Inspect the application, Caddy, and cloudflared systemd logs.
3. If data integrity is suspected, stop writes and follow
   [`docs/DATABASE.md`](docs/DATABASE.md) before restoration.
4. Record the incident timeline and validate `./scripts/ci/test.sh` before
   returning traffic.

## Dashboard failure

1. Request `/api/health`; a valid JSON response isolates UI/SSE failures.
2. Validate `python3 -m dashboard.api.health`.
3. Verify the tunnel ingress targets `http://127.0.0.1:80` and that an
   anonymous public request receives Cloudflare Access or Caddy
   authentication, never dashboard JSON.
4. Treat missing reports as unavailable evidence, not a successful control.
5. Restart the dashboard only after preserving its logs.

## Terraform state migration failure

1. Stop every Terraform writer and preserve `.terraform/`, ignored
   `backend.tf`, the local state, and the newest
   `output/backups/cloudflare-state-*.tfstate{,.sha256}` without modification.
2. Verify the backup from its directory with
   `sha256sum --check <backup-name>.sha256`; reject a checksum or permission
   mismatch.
3. If `backend.tf` exists after the command failed, assume R2 may already be
   authoritative. Do not delete it, reinitialize the local backend, apply, or
   push state.
4. Run `./scripts/cloudflare-state.sh verify` with the same mode-`0600`
   `.env.cloudflare`, then compare remote state lineage and managed addresses
   with the verified backup.
5. If verification cannot establish one authoritative state, make both state
   copies immutable, record their serial, lineage, checksum, and writer
   timeline, and require a reviewed recovery decision before any mutation.
6. Use `terraform state push` only against an explicitly reviewed recovery
   backend after a no-change import and plan review. Never force-unlock without
   first identifying the lock owner and current writer.

Security incidents follow [`SECURITY.md`](SECURITY.md). Deployment and rollback
procedures are in [`DEPLOYMENT.md`](DEPLOYMENT.md).
