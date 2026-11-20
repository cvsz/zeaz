# Services and Documentation Authority

| Concern | Canonical source |
| --- | --- |
| Runtime architecture | `docs/ARCHITECTURE.md` |
| API contract | `docs/openapi.yaml` |
| Database schema | `migrations/` |
| Database operations | `docs/DATABASE.md` |
| Application runtime | `app.py` |
| Browser production assets | `web/` |
| Shared TypeScript contracts | `packages/` |
| Cloudflare infrastructure | `infrastructure/terraform/cloudflare/` and `docs/cloudflare-deployment.md` |
| zERP web application | `apps/zerp/` and `zerp.zeaz.dev` via the Cloudflare/Caddy proxy |
| Host and Kubernetes deployment | `deploy/` and `DEPLOYMENT.md` |
| Operational procedures | `OPERATIONS.md` and `RUNBOOK.md` |
| Security policy | `SECURITY.md` |
| Engineering health | `dashboard/` |
| zTTShop SaaS architecture decision | `docs/adr/ADR-001-zttshop-saas-service-boundary.md` |
| zTTShop SaaS threat model | `docs/security/zttshop-saas-threat-model.md` |
| zTTShop paid-pilot validation | `docs/pilot/paid-pilot-validation.md` |
| zTTShop SaaS execution status | `docs/rollout/zttshop-saas-execution-status.md` |
| ZEAZ AI + SaaS commercial strategy | [PR #71](https://github.com/cvsz/zeaz/pull/71) |

Root summary files link to these authorities. Dated `*_REPORT.md` documents are
historical evidence and must not override executable configuration or current
contracts. zTTShop SaaS documents describe a proposed service boundary; they do
not establish that the SaaS API, tenant database, billing provider or live
channel connectors have been implemented or approved.
