# zERP contribution guide

`apps/zerp` is the ZEAZ owner ERP workspace. Keep the API and database source
of truth in the MooPiew service; do not add a second operational database to
the browser application.

## Required checks

From the repository root run:

```bash
./apps/zerp/scripts/verify.sh
```

Changes that add a route, payload, permission, or persistent field must update
the relevant API contract, tests, and documentation. Never commit secrets,
production databases, generated credentials, or populated environment files.

## Current boundary

The delivered zERP slice is a protected read-only operations workspace. It
surfaces receipts, tax invoices, inventory, recipes, applications, and rider
workforce data from `/api/admin/operations`. Larger ERP capabilities remain
deferred until their backend models and authorization are implemented.
