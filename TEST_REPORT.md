# Test Report (2026-07-28)

- `./scripts/ci/test.sh` — pass
- `./scripts/ci/smoke-api.sh` — pass
- `./scripts/production-check.sh` — pass with retry policy
- `npm audit --omit=dev --audit-level=high` — no findings
- `.venv/bin/python -m pip check` — pass
- Provider-side pytest — 521 passed (audit observation)

The browser admin-monitor path is covered by the static asset and API smoke gates.
