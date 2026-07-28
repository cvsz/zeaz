# Development workflow

## Run locally

```bash
ADMIN_KEY='local-owner-key' ./scripts/start.sh
```

Use `/` for the customer flow, `/ops.html` for owner operations,
`/rider-register.html` for rider applications, and `/merchant-register.html`
for merchant applications. Do not use production keys locally.

## Verify a change

```bash
python3 -m py_compile app.py
./scripts/migrate.sh
./scripts/health-check.sh
./scripts/ci/test.sh
```

For workflow changes, test at least one pickup and one delivery order, a rider
application, a merchant application, and the owner approval path against a
clean development database. Verify delivery pricing uses configured coordinates
and that tracking output does not disclose a customer's address or phone.

## TypeScript packages

The repository is an npm workspace for UI, icons, config, design tokens, types
and SDK packages. Run `npm install` once, then `npm run typecheck`. The premium
React shell at `apps/web/` uses the existing API and can be published to
`web/platform/`; it must not add a separate order database.

## Configuration hygiene

Start from examples, keep populated `.env.production`, `.env.payment`,
`.env.cloudflare`, certificate material and database files ignored, and use the
owner console or a local master-data import for business-specific values.
