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
origin is `http://127.0.0.1:8082`.
