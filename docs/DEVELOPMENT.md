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

## Platform web release

`apps/web/` is the Premium React presentation layer. It reads the same menu
API as the Python app, so the API/database remain the single source of truth.

```bash
npm run build
mkdir -p web/platform
cp -R apps/web/dist/. web/platform/
```

The final files are served at `/platform/`; check both `/platform/` and
`/api/menu` before release. Use `VITE_API_URL` only when running the React app
on a different origin.
