# Operations

This is the canonical operations entry point. Detailed store procedures remain
in [`docs/operations.md`](docs/operations.md), database backup and recovery in
[`docs/DATABASE.md`](docs/DATABASE.md), and public-edge deployment in
[`DEPLOYMENT.md`](DEPLOYMENT.md).

## Engineering dashboard

Run `npm run dashboard` and open `http://127.0.0.1:8080`. The server is
read-only, binds to loopback by default, publishes a point-in-time snapshot at
`/api/health`, and streams snapshots from `/api/events` using Server-Sent
Events. Set `DASHBOARD_HOST`, `DASHBOARD_PORT`, or
`DASHBOARD_REFRESH_SECONDS` to override local defaults.

CI systems publish evidence as JSON objects under `dashboard/data/<name>.json`,
where `name` is one of `ci`, `coverage`, `security`, `performance`,
`infrastructure`, or `agents`. Every report requires `schemaVersion`,
`generatedAt`, `summary`, and a `status` of `pass`, `fail`, `unknown`, or
`not_applicable`; `metrics` and `details` are optional. Missing, malformed, and
stale evidence is deliberately excluded from passing scores. CI generates and
uploads these files with `scripts/ci/evidence.py`.

```bash
docker compose -f dashboard/compose.yml up --build
curl --fail http://127.0.0.1:8080/api/health
```

Do not expose the dashboard publicly without authentication at the reverse
proxy. Repository state, branch names, and commit subjects are operational
metadata.

The production single-host URL is `https://piewdash.zeaz.dev/`; its local
process listens at `http://127.0.0.1:8082`. Cloudflared must target the
authenticated Caddy route at `http://127.0.0.1:80`, not the process directly.

## Terraform state

Cloudflare state migration and verification are owned by
`scripts/cloudflare-state.sh` and
`infrastructure/terraform/cloudflare/backend.r2.tf.example`. The current
backend mode and write authorization live only in `.env.cloudflare`; the
script installs ignored `backend.tf` from that canonical template only for R2
operations. A local backend is not collaborative production state;
`ROADMAP.md` remains open until an encrypted R2 backend migration and
lock-backed plan have both succeeded.

Migration requires a mode-`0600` version-4 local state with a nonempty lineage
and managed resource set. It creates a mode-`0700` backup directory containing
a unique mode-`0600` state copy and checksum, then verifies remote lineage and
resource-address parity. If backend initialization succeeds but verification
fails, `backend.tf` intentionally remains installed: stop Terraform writers
and use the recovery procedure in [`RUNBOOK.md`](RUNBOOK.md) before changing
backend authority.
