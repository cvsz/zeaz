# Test Report (2026-07-28)

The canonical machine-readable results are `dashboard/data/*.json`, regenerated
by `scripts/ci/evidence.py` and uploaded by `.github/workflows/validate.yml`.
At this revision:

- `python3 scripts/ci/evidence.py coverage` — 98 tests passed; 54.07% measured
  Python line coverage with a 53% minimum gate; `app.py` measured 52.89%.
- `npm run validate` — lint, TypeScript type checking, workspace build and
  Python tests passed.
- `python3 scripts/ci/evidence.py security` — Python and npm dependency audits
  reported zero known vulnerabilities.
- `./scripts/ci/test.sh` and `./scripts/ci/smoke-api.sh` — platform, security
  regression and isolated API smoke checks passed.
- `python3 scripts/ci/evidence.py infrastructure` and `performance` — deployment
  controls, rendered Kubernetes proof and static performance budgets passed.
- `./scripts/production-check.sh` — local services, reverse proxies, public app
  and protected dashboard boundary passed.

The coverage gate is a regression floor, not a production-readiness claim.
Risk-based integration coverage must continue to prioritize authorization,
financial lifecycle and destructive administrative mutations.
