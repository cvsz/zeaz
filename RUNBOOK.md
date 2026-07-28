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
3. Treat missing reports as unavailable evidence, not a successful control.
4. Restart the dashboard only after preserving its logs.

Security incidents follow [`SECURITY.md`](SECURITY.md). Deployment and rollback
procedures are in [`DEPLOYMENT.md`](DEPLOYMENT.md).
