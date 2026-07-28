# AGENTS.md

## Language and Coding Standards
- **Communication**: Always talk in Thai when interacting with users.
- **Code & Technical Assets**: All code, comments, documentation, and technical definitions must be in English.

## Purpose

This file defines repository-wide operating rules for coding agents and human
contributors working in `cvsz/zeaz` (MooPiew). Follow these instructions before
editing any file. More specific `AGENTS.md` files may be added in subdirectories
later; when present, the nearest file to the changed path takes precedence.

## Repository identity

MooPiew is a Thai restaurant commerce, delivery, onboarding, document intake,
operations, and owner-AI platform. The production architecture is intentionally
small and operationally explicit:

```text
Browser
  -> Cloudflare Tunnel
  -> Caddy :8080
  -> Python service :8000
  -> SQLite (WAL + foreign keys)
```

The repository also contains an npm/Turbo workspace for reusable TypeScript
packages and a React platform shell. These clients consume the Python API; they
must not introduce a second source of truth for orders, applicants, documents,
inventory, payments, settings, or audit state.

## Read before changing code

At minimum, inspect the files relevant to the change:

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/DEVELOPMENT.md`
- `docs/DATABASE.md` for schema, migration, backup, or restore work
- `docs/security.th.md` for authentication, secrets, uploads, payment, or public
  endpoint work
- `docs/openapi.yaml` for HTTP contract changes
- `scripts/ci/test.sh` and `.github/workflows/validate.yml` for validation gates
- the nearest implementation and regression tests

Do not infer repository behavior from filenames alone. Revalidate the current
branch and read the actual implementation before editing.

## Source-of-truth boundaries

### Python service

`app.py` owns the supported runtime behavior, including:

- request validation and HTTP routing
- owner authentication and role checks
- order and delivery state transitions
- SQLite schema initialization and additive migration
- transactional mutations
- audit writes
- provider document requirements and document metadata
- optional owner-only AI-provider discovery

Keep mutations atomic. Use explicit transactions for related writes. Preserve
SQLite foreign keys and WAL-compatible behavior. Do not silently split one
business operation across non-transactional steps.

### Operational database

`data/moopiew.sqlite3` and runtime databases are private operational state and
must never be committed. Schema evolution must be backward-compatible and
additive unless a reviewed migration explicitly says otherwise.

When changing schema or data rules:

1. Preserve existing installations and legacy imports.
2. Add deterministic migration logic.
3. Keep foreign-key and uniqueness invariants explicit.
4. Update backup/restore verification when affected.
5. Add regression tests for clean and existing databases.

### Web clients

`web/` contains the served customer and owner pages. Public registration pages
must not require or expose owner credentials. `/ops.html`, `/documents.html`,
and owner APIs are privileged surfaces.

`apps/web/` and `packages/` are reusable TypeScript UI, SDK, config, icon,
design-token, and type packages. The generated platform build is published to
`web/platform/` using:

```bash
npm run build
npm run publish:platform
```

The publish step must synchronize the output exactly and remove obsolete hashed
assets. Never edit generated `web/platform/` assets as the sole source change;
edit their source and republish.

### OpenAPI

`docs/openapi.yaml` is the published API contract. Any externally observable
route, payload, authentication, validation, status-code, or response change must
update the OpenAPI document and tests in the same change.

## Security invariants

These are hard requirements, not suggestions:

- Never commit API keys, owner keys, payment credentials, OAuth secrets,
  certificates, private database files, uploaded documents, or populated env
  files.
- Production values belong only in ignored files such as `.env.production`,
  `.env.payment`, `.env.ai`, and `.env.cloudflare`, or in an approved secret
  store.
- Protected owner APIs require `X-Admin-Key` or an explicitly reviewed successor.
- Do not embed owner credentials in browser source, URLs, query strings, local
  storage, generated static files, logs, reports, fixtures, or screenshots.
- Public tracking responses must not disclose customer address, phone, secrets,
  internal notes, or unnecessary identifiers.
- Uploaded documents must remain outside the public web root, use restrictive
  permissions, validate MIME type and size against policy, and expose only
  authorized metadata or controlled content.
- Preserve CSP nonce behavior, rate limiting, path normalization, and security
  headers when changing request handling or reverse-proxy configuration.
- Payment support must remain disabled until approved credentials, certificate
  material, and sandbox verification are configured.
- Treat logs and audit records as potentially sensitive. Do not log secrets,
  credential-bearing headers, raw identity documents, or full payment payloads.

## Business and domain invariants

- Monetary values are integer minor units unless the existing contract states
  otherwise. Avoid floating-point arithmetic for totals, discounts, fees, VAT,
  receipts, and refunds.
- Order, delivery, payment, receipt, inventory, document-verification, and
  application transitions must validate the current state before mutation.
- Repeated requests and callbacks must be idempotent where retries are possible.
- Inventory adjustments and order acceptance must not permit overselling through
  concurrent or repeated operations.
- Delivery pricing is server-calculated from configured coordinates and policy;
  do not trust client-calculated totals or distance.
- Provider document policies are time-sensitive external facts. Preserve source
  references and effective dates, and do not claim a policy is current without
  verifying the official provider source.
- Audit significant owner, staff, payment, document, inventory, and status
  mutations with actor and timestamp information.

## AI provider and Responses API rules

AI integrations are optional and owner-only. Provider credentials stay on the
server and must never be returned to browser clients.

When constructing OpenAI-compatible Responses API requests:

- Send only parameters supported by the selected provider/model capability map.
- Do not emit a `namespace` member inside any object in `input[]`; it is not a
  valid Responses API input-item parameter and causes errors such as:

  ```text
  Unknown parameter: 'input[N].namespace'
  ```

- Keep internal metadata outside the provider payload or map it to a documented
  supported field.
- Do not globally force `service_tier = "priority"`. Use `auto` by default and
  include another tier only when the resolved model explicitly advertises it.
- A model alias such as `codex-auto-review` may route to different backends;
  capability checks must occur after alias resolution and before serialization.
- Provider adapters must remove unsupported optional fields deterministically,
  while surfacing a useful diagnostic. Never silently rewrite required content.
- Streaming and non-streaming paths must apply the same payload normalization.
- Add regression coverage for payload serialization, unsupported-field removal,
  provider fallback, streaming, and error propagation.

For repository or local-state cleanup, `fix-codex-namespace.sh` may be used in
`--dry-run` mode first. Review its report and backup before applying changes.
The durable fix belongs in the request builder or provider adapter, not only in
cached JSON or generated state.

## Implementation discipline

- Make the smallest complete vertical change that satisfies the requirement.
- Do not leave placeholders, dead branches, partial migrations, or commented-out
  production logic.
- Preserve backward compatibility unless the change explicitly introduces and
  documents a migration.
- Prefer clear, explicit code over clever abstraction.
- Reuse existing validation, authentication, transaction, audit, and response
  helpers before adding parallel mechanisms.
- Keep functions cohesive. When `app.py` changes, avoid broad unrelated rewrites.
- Maintain deterministic behavior and stable output ordering where reports,
  generated files, archives, or API responses are tested.
- Do not add dependencies without a concrete need, maintenance assessment, and
  lockfile/update implications.
- Pin security-sensitive runtime dependencies deliberately; do not broaden
  version ranges casually.
- Shell scripts must use `set -Eeuo pipefail`, quote expansions, handle spaces in
  paths, clean temporary files, and avoid destructive defaults.
- Destructive or production-affecting commands require an explicit flag and a
  backup/rollback path.

## Test requirements by change type

### Baseline validation

Run the repository gates applicable to the environment:

```bash
python3 -m py_compile app.py
./scripts/migrate.sh
./scripts/health-check.sh
./scripts/ci/test.sh
npm run lint
npm run typecheck
npm run build
```

`./scripts/ci/test.sh` conditionally runs TypeScript build checks when
`node_modules/` is installed. In CI, `npm ci` is run before the test script.

Also run:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
./scripts/ci/smoke-api.sh
```

### Python/API changes

- Add or update `unittest` regression coverage.
- Test success, validation failure, authentication failure, invalid state,
  duplicate/retry behavior, and transactional rollback where relevant.
- Update `docs/openapi.yaml` for contract changes.
- Verify no sensitive data is added to public responses.

### Database changes

- Test a clean database.
- Test migration from the previous schema/state.
- Test foreign-key, uniqueness, and state invariants.
- Verify backup and restore behavior when affected.

### Web/static changes

- Run JavaScript syntax checks for changed non-bundled files.
- Verify referenced static assets exist.
- Test the affected public and owner flow manually or through browser tests.
- Do not expose `X-Admin-Key` or provider secrets.

### TypeScript workspace changes

```bash
npm ci
npm run typecheck
npm run build
npm run publish:platform
./scripts/ci/test.sh
```

Confirm `apps/web/dist/` and `web/platform/` are synchronized exactly.

### Shell/deployment changes

```bash
bash -n path/to/changed-script.sh
npm run lint
```

Test dry-run and failure behavior. For Caddy, Cloudflare, systemd, backup,
restore, release, or credential-sync changes, verify the generated configuration
or command output without exposing production values.

### AI/provider changes

Test at least:

- model discovery with missing optional credentials
- alias-to-model capability resolution
- Responses API payloads without `input[].namespace`
- omission or downgrade of unsupported `service_tier`
- streaming and non-streaming parity
- provider timeout/error handling and safe fallback
- absence of provider keys in browser responses and logs

## Manual workflow verification

For changes that affect core business behavior, exercise the relevant path
against a clean development database. Depending on scope, include:

- one pickup order
- one delivery order and distance quote
- rider and merchant applications
- owner approval and activation
- delivery assignment and status progression
- document requirement lookup, upload, review, rejection, deletion, and history
- coupon/loyalty behavior
- inventory movement and recipe consumption
- receipt/tax-invoice generation
- public tracking privacy

Use synthetic data only. Never copy production identities, documents, phone
numbers, addresses, credentials, or payment material into tests.

## Git and pull-request workflow

1. Revalidate `main` and inspect active work before editing.
2. Create a focused branch.
3. Implement one complete, reviewable change.
4. Run all applicable checks and fix regressions.
5. Review `git diff --check` and the final diff for secrets and generated noise.
6. Update documentation, changelog, OpenAPI, and tests when affected.
7. Commit with a scoped, descriptive message.
8. Open a pull request summarizing behavior, security impact, migration impact,
   tests run, and rollback considerations.

Do not merge failing CI. Do not bypass branch protection or validation gates.
Do not combine unrelated refactors with a production fix.

## Generated and reusable business-kit content

`templates/`, `excel/`, `examples/`, and generation/packaging scripts support
reusable business-kit output. They are not the runtime operational database.
Generated output must be deterministic, free of secrets, and validated before
packaging. Avoid committing generated archives unless the release process
explicitly requires them.

## Definition of done

A change is complete only when:

- behavior is implemented end to end
- security and privacy boundaries are preserved
- schema/API compatibility is addressed
- tests cover success and important failure paths
- applicable lint, build, typecheck, migration, health, and smoke checks pass
- generated platform assets are synchronized when required
- documentation and OpenAPI are current
- no secrets, private data, runtime databases, uploads, or accidental artifacts
  are included
- the pull request explains validation and rollback
