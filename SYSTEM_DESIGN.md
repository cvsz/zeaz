# System Design

[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) is the canonical architecture
description. The production request path is Cloudflare Tunnel to Caddy to the
dependency-light Python HTTP service and SQLite WAL storage. Static clients are
served from `web/`; the TypeScript workspace builds the migration surface under
`apps/web` and publishes it to `web/platform`.

The engineering dashboard is a separate read-only process. It collects Git and
repository controls locally, reads CI-produced JSON evidence, and serves JSON
plus SSE to `dashboard/index.html`. It never mutates the repository or executes
user-supplied commands.

Ordered, checksummed files under `migrations/` are the database schema SSOT.
`app.py` runs the same migration runner used by `scripts/migrate.sh`, then
performs idempotent reference-data seeding. Kubernetes is intentionally
single-replica for the application because SQLite is the supported durable
store; horizontal application scaling requires a network database migration.
