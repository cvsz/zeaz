# Moopiew platform architecture

## Runtime today

The production runtime is deliberately small and deployable: a dependency-free
Python HTTP service binds to loopback, Caddy reverse-proxies it on loopback, and
Cloudflare Tunnel provides the public HTTPS boundary. SQLite is the operational
database; WAL mode and database transactions protect concurrent order writes.

```text
Customer browser → Cloudflare Tunnel → Caddy :8080 → Python app :8000 → SQLite
                                                    ↘ static web dashboards
```

## Platform contracts

- `web/` is the customer and operations interface.
- `packages/` contains TypeScript types, design tokens, config, icons, UI and SDK
  for future web/mobile services without coupling them to the current runtime.
- `docs/openapi.yaml` is the API contract; `/api/health` and `/api/ready` are
  unauthenticated liveness/readiness probes.
- `data/moopiew.sqlite3` is private service state; it is never committed.

## Expansion boundary

PostgreSQL, Redis, workers and container orchestration may be introduced when
multi-node deployment is required. They must preserve the existing OpenAPI
contract and role restrictions rather than bypassing the production service.
