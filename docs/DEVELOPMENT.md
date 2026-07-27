# Development workflow

## Run the current platform

```bash
ADMIN_KEY=owner EMPLOYEE_KEY=staff KITCHEN_KEY=kitchen ./scripts/start.sh
```

Use `/`, `/dashboard.html`, `/admin.html`, `/ops.html` and
`/ops.html?role=kitchen`. Production uses `.env.production`; never commit it.

## Checks

```bash
./scripts/migrate.sh
./scripts/health-check.sh
./scripts/ci/test.sh
```

The repository is an npm workspace for reusable TypeScript packages. Run
`npm install` once, then `npm run typecheck` to validate every shared package.
