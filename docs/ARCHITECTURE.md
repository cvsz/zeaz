# MooPiew platform architecture

## Runtime

```text
Customer / rider / merchant browser
              │ HTTPS
Cloudflare Tunnel → Caddy :8080 → Python service :8000 → SQLite
                                      ├─ web/ customer and owner pages
                                      ├─ dynamic provider document requirements
                                      └─ SSE delivery tracking
```

The Python service binds to loopback. Caddy and the tunnel are the only public
path. SQLite runs with WAL and foreign keys; an order mutation is handled as a
database transaction.

## Boundaries

- `app.py` owns API validation, authentication, order transitions and audit
  writes. Ordered files under `migrations/` own schema and upgrade history;
  startup and `scripts/migrate.sh` use the same checksummed runner.
- `web/` is the served customer/owner UI. `/ops.html` is an owner console;
  public registration pages have no owner credential.
- `data/moopiew.sqlite3` is private operational state and is never committed.
- `packages/` and `apps/web/` hold reusable TypeScript UI/SDK migration work;
  they consume the same API and never create a second source of truth.
- `docs/openapi.yaml` describes the supported HTTP surface. `/api/health` and
  `/api/ready` are liveness/readiness probes.
- Provider policies are normalized in SQLite. Uploads are validated by
  requirement MIME/size rules, stored outside the public web root with `0600`
  permissions, and exposed only as metadata to owner APIs.

## Delivery flow

```text
Quote → customer order → queued → assigned → picked_up → on_the_way → delivered
                         │                         │
                         └─ owner assigns active rider ─┘
```

The server calculates a distance fee from the configured store coordinates and
pricing policy. The tracking API exposes only the minimum status information
needed by the customer; delivery address and phone never appear in its payload.

## Growth path

Use PostgreSQL, a queue and worker services only when a multi-node deployment
needs them. Preserve API contracts, auditability and role checks when replacing
SQLite-backed components.
