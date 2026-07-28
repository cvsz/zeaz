# MooPiew

MooPiew is a Thai grilled-pork restaurant commerce and delivery platform. It
provides a customer storefront, order lifecycle, distance-based delivery,
rider and merchant onboarding, inventory, loyalty, receipts, and an owner
operations console from one SQLite-backed service.

Live service: [moopiew.zeaz.dev](https://moopiew.zeaz.dev/) · API menu:
[`/api/menu`](https://moopiew.zeaz.dev/api/menu) · service status:
[`/api/status`](https://moopiew.zeaz.dev/api/status).

## What is available

- Customer ordering for pickup or delivery, including delivery quotes and live
  delivery tracking.
- Public rider and merchant application forms; owner review, rider activation,
  availability and delivery assignment.
- Menu ordering, coupons, customer loyalty, inventory recipes and stock
  movements.
- Owner operations for business profile, menus, delivery pricing/zones,
  applications, riders, orders, receipts and tax invoices.
- Private SQLite data with audit history, backups, Cloudflare Tunnel deployment
  and operational health checks.

SCB payment support is intentionally disabled until approved credentials,
certificate material and successful Sandbox verification are configured. See
[the SCB guide](docs/scb-application.md); never commit payment credentials.

## Run locally

```bash
ADMIN_KEY='replace-with-a-strong-local-key' ./scripts/start.sh
```

Open `http://127.0.0.1:8000/` for customers and
`http://127.0.0.1:8000/ops.html` for the owner console. Production values live
only in ignored `.env.production` / `.env.payment` files.

## Main routes

| Audience | Route |
| --- | --- |
| Customer storefront | `/` |
| Owner operations | `/ops.html` |
| Rider registration | `/rider-register.html` |
| Merchant registration | `/merchant-register.html` |
| Delivery tracking | `/api/tracking/{trackingCode}` |
| OpenAPI reference | `docs/openapi.yaml` |

Protected owner APIs require `X-Admin-Key`. Browser pages must not embed this
key in source control, local storage, or a public URL.

## Quality checks

```bash
python3 -m py_compile app.py
./scripts/migrate.sh
./scripts/health-check.sh
./scripts/ci/test.sh
```

Read [development](docs/DEVELOPMENT.md), [architecture](docs/ARCHITECTURE.md),
[database operations](docs/DATABASE.md), [owner operations](docs/operations.md),
[security controls](docs/security.th.md), and the bilingual roadmap
([English](docs/roadmap.en.md) / [ไทย](docs/roadmap.th.md)) before deploying.

The reusable `templates/`, `excel/`, and generation scripts remain available
for business-kit work, but they are not a replacement for MooPiew's live
operational database.
