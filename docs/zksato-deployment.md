# zksato and zWorkforce deployment ports

The two control planes share the Cloudflare Tunnel but use separate host
origins:

| Public hostname | Host origin | Container/API port | Purpose |
| --- | --- | --- | --- |
| `zksato.zeaz.dev` | `127.0.0.1:9569` | `9569` | zksato FastAPI/dashboard |
| `zwf.zeaz.dev` | `127.0.0.1:9570` | `9569` | zWorkforce API |

The zWorkforce container still listens on `9569`; only its Docker host
publication changes to `9570`. PostgreSQL and Redis for zksato remain private
Compose services on container ports `5432` and `6379` and are not published
on the host.

## Verification

```bash
curl --fail http://127.0.0.1:9569/livez
curl --fail http://127.0.0.1:9569/readyz
curl --fail http://127.0.0.1:9570/health
curl --fail https://zksato.zeaz.dev/livez
curl --fail https://zksato.zeaz.dev/readyz
curl --fail https://zwf.zeaz.dev/health
```

`zksato /readyz` is expected to be `200` only when its PostgreSQL, Redis,
audit-chain, and reconciliation checks are healthy. Keep zksato in paper mode
unless a separately authorized UAT/live-execution gate is satisfied.

## Rollback

1. Keep zksato running on `9569` while restoring zWorkforce's host
   publication to `9570` if that is the active topology.
2. Restore the previous zWorkforce image/configuration, then verify
   `http://127.0.0.1:9570/health`.
3. Revert only the `zwf` Cloudflare origin if the public route fails; do not
   expose `5432` or `6379` as a workaround.
