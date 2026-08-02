# Arin Production Platform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Arin static replica's simulated builder with a real authenticated app-builder MVP at `https://arin.zeaz.dev`.

**Architecture:** Keep the Vite React frontend and existing Cloudflare/Caddy edge. Add a loopback-only Python standard-library service on port 8787 with a private SQLite database, deterministic static project generator, optional OpenAI-compatible provider, and sandboxed preview/publish delivery. Caddy routes `/api/*`, `/preview/*`, and `/app/*` to the service while continuing to serve the compiled frontend.

**Tech Stack:** React 19, Vite 7, TypeScript, Python 3 standard library, `sqlite3`, PBKDF2-HMAC-SHA256, Caddy, systemd user service, Cloudflare Tunnel/Terraform.

## Global Constraints

- Work in `/home/cvsz/zeaz`; preserve the existing unrelated dirty `app.py` change.
- Never commit populated `.env` files, API keys, passwords, sessions, databases, uploaded assets, or generated runtime data.
- Bind the Arin backend only to `127.0.0.1:8787`; do not add a public direct origin.
- Use SQLite WAL, foreign keys, transactions, private `data/arin` mode `0700`, and database/files mode `0600`.
- Use test-first cycles: write one failing test, run it and observe the expected failure, implement the smallest passing change, then refactor only while green.
- Generated app output must be static and sandboxed; the service must never execute generated server code.
- Remote AI is optional and configured only through ignored `ARIN_AI_BASE_URL`, `ARIN_AI_API_KEY`, and `ARIN_AI_MODEL` values.
- Cloudflare Terraform remains the source of truth; no ad-hoc public DNS or tunnel route is created.

## Task 1: Backend package and database contract

**Files:**
- Create: `sites/arin/arin_app/__init__.py`
- Create: `sites/arin/arin_app/db.py`
- Create: `sites/arin/arin_app/security.py`
- Create: `sites/arin/tests/test_backend_foundation.py`
- Modify: `sites/arin/package.json` only if the test command needs a documented backend command

**Interfaces:**
- `db.connect(path: Path) -> sqlite3.Connection`
- `db.initialise(connection) -> None`
- `db.transaction(connection) -> context manager`
- `security.hash_password(password: str) -> tuple[str, str]`
- `security.verify_password(password: str, encoded_hash: str, salt: str) -> bool`
- `security.new_token() -> str`
- `security.hash_token(token: str) -> str`

- [ ] **Step 1: Write failing database and password tests.**

  Add tests that require schema tables for users, sessions, workspaces,
  workspace members, projects, project versions/files, assets, connectors,
  invites, agent messages, deployments, and audit events. Assert foreign keys
  and WAL are enabled, password hashes differ from plaintext, verification
  rejects wrong passwords, token hashes are one-way, and a transaction rolls
  back an inserted row after an exception.

- [ ] **Step 2: Run the foundation tests and verify the expected missing-module failure.**

  Run:

  ```bash
  PYTHONPATH=sites/arin python3 -m unittest discover -s sites/arin/tests -p 'test_*.py' -v
  ```

  Expected: failure because `arin_app.db` and `arin_app.security` do not yet
  exist.

- [ ] **Step 3: Implement the SQLite schema and security primitives.**

  Use `PRAGMA foreign_keys = ON`, `PRAGMA journal_mode = WAL`, explicit
  `BEGIN IMMEDIATE` transactions, PBKDF2-HMAC-SHA256 with a fixed documented
  iteration count and 16-byte random salts, and `secrets.token_urlsafe(32)`
  session/invite tokens. Store only token hashes. Reject empty or short
  passwords in a reusable validator.

- [ ] **Step 4: Run the foundation tests and verify green.**

  Run the same unittest command. Expected: all foundation tests pass with no
  plaintext secret or database path in assertion output.

- [ ] **Step 5: Refactor only after green and run `python3 -m py_compile`.**

  Keep SQL in focused schema/row helpers, then run:

  ```bash
  PYTHONPATH=sites/arin python3 -m py_compile sites/arin/arin_app/*.py
  ```

## Task 2: Authentication, sessions, and workspace authorization

**Files:**
- Create: `sites/arin/arin_app/service.py`
- Create: `sites/arin/arin_app/server.py`
- Create: `sites/arin/tests/test_auth_and_workspaces.py`

**Interfaces:**
- `service.register_user(email: str, name: str, password: str) -> dict`
- `service.login_user(email: str, password: str) -> tuple[dict, str, str]`
- `service.create_workspace(user_id: str, name: str) -> dict`
- `service.require_membership(connection, user_id: str, workspace_id: str, roles: set[str]) -> dict`
- `server.ArinServer` exposes JSON routes on `127.0.0.1:8787`.

- [ ] **Step 1: Write failing service tests for registration, login, logout, CSRF, and role checks.**

  Use a temporary SQLite database. Assert duplicate email rejection,
  wrong-password rejection, session expiry rejection, CSRF rejection for
  mutations, owner/editor/viewer permissions, and that unauthenticated API
  responses use stable JSON error objects.

- [ ] **Step 2: Run the auth tests and verify they fail for missing service/server behavior.**

  Run:

  ```bash
  PYTHONPATH=sites/arin python3 -m unittest sites.arin.tests.test_auth_and_workspaces -v
  ```

  Expected: failure because the service and HTTP route implementations are not
  present.

- [ ] **Step 3: Implement service transactions and the HTTP auth routes.**

  Add `POST /api/auth/register`, `POST /api/auth/login`,
  `GET /api/auth/session`, `POST /api/auth/logout`, `GET/POST /api/workspaces`,
  and workspace membership/invite authorization helpers. Set an opaque
  `arin_session` cookie with `HttpOnly; Secure; SameSite=Lax`, return the CSRF
  token only from the authenticated session response, and require
  `X-CSRF-Token` on POST/PUT/DELETE after authentication. Bound JSON bodies to
  256 KiB and normalize emails.

- [ ] **Step 4: Run auth tests and verify green.**

  Run the foundation and auth commands together. Expected: all tests pass,
  including an HTTP round trip through a temporary loopback server.

- [ ] **Step 5: Add API error and audit helpers while green.**

  Keep errors shaped as `{ "error": { "code": "...", "message": "..." } }`
  and audit only action/target metadata. Add tests that responses never contain
  passwords, session tokens, CSRF tokens, or provider keys.

## Task 3: Prompt generation, project files, versions, preview, and publish

**Files:**
- Create: `sites/arin/arin_app/generator.py`
- Create: `sites/arin/tests/test_projects_and_generation.py`
- Modify: `sites/arin/arin_app/service.py`
- Modify: `sites/arin/arin_app/server.py`

**Interfaces:**
- `generator.generate_project(prompt: str, category: str, ai_client=None) -> dict`
- `service.create_project(user_id: str, workspace_id: str, prompt: str, category: str) -> dict`
- `service.build_project(user_id: str, project_id: str, prompt: str) -> dict`
- `service.read_preview(project_id: str, published: bool = False, slug: str = "") -> tuple[bytes, str]`

- [ ] **Step 1: Write failing generation and delivery tests.**

  Assert that CRM, portal, inventory, marketing, and mobile prompts produce a
  valid static file set containing `index.html`, `styles.css`, and `app.js`; all
  paths are relative safe paths; a build creates an immutable version; file
  edits create a new version; preview returns the current draft; publish creates
  a slug; unpublish removes public delivery; and traversal paths such as
  `../../secret` are rejected.

- [ ] **Step 2: Run the project tests and verify the generator/delivery failure.**

  Run:

  ```bash
  PYTHONPATH=sites/arin python3 -m unittest sites.arin.tests.test_projects_and_generation -v
  ```

  Expected: failure because generator and project service methods are absent.

- [ ] **Step 3: Implement the deterministic generator and immutable versions.**

  Generate safe HTML/CSS/JS templates with prompt-derived title, sections,
  forms, responsive styles, and category-specific content. Store every file in
  SQLite version rows plus a private materialized copy for delivery. Validate
  UTF-8 content, file count, file size, MIME, and safe paths. Add optional
  OpenAI-compatible JSON generation only after local validation; on timeout,
  invalid JSON, non-2xx, or missing credentials use the local generator.

- [ ] **Step 4: Implement preview/publish responses with isolation headers.**

  Serve `/preview/<id>` and `/app/<slug>` through the backend with
  `Content-Security-Policy: sandbox allow-scripts allow-forms; default-src
  'none'; img-src data: https:; style-src 'unsafe-inline'; script-src
  'unsafe-inline'` plus `X-Content-Type-Options: nosniff`. Do not set
  `allow-same-origin`; never expose Arin cookies or API endpoints to generated
  content.

- [ ] **Step 5: Run project tests and verify green.**

  Run foundation, auth, and project tests. Expected: all pass, including
  unpublished access returning 404 and published content remaining isolated.

## Task 4: Assets, branding/SEO, connectors, team invites, and agent history

**Files:**
- Create: `sites/arin/tests/test_project_capabilities.py`
- Modify: `sites/arin/arin_app/service.py`
- Modify: `sites/arin/arin_app/server.py`
- Modify: `sites/arin/arin_app/db.py`

**Interfaces:**
- `service.update_project_settings(user_id: str, project_id: str, settings: dict) -> dict`
- `service.add_asset(user_id: str, project_id: str, filename: str, mime: str, data: bytes) -> dict`
- `service.create_connector(user_id: str, project_id: str, kind: str, label: str, config: dict) -> dict`
- `service.invite_member(user_id: str, workspace_id: str, email: str, role: str) -> dict`
- `service.record_agent_message(user_id: str, project_id: str, role: str, content: str) -> dict`

- [ ] **Step 1: Write failing capability tests.**

  Test settings validation for title/description/colors/SEO, 5 MiB asset limit
  and MIME allowlist, generated asset storage names, connector config
  encryption/omission from list responses, owner-only invites, invite expiry
  and acceptance, bounded agent messages, and audit events for each mutation.

- [ ] **Step 2: Run the capability tests and verify red.**

  Run:

  ```bash
  PYTHONPATH=sites/arin python3 -m unittest sites.arin.tests.test_project_capabilities -v
  ```

  Expected: failure because capability service methods are absent.

- [ ] **Step 3: Implement settings, assets, connectors, invites, and messages.**

  Store settings as validated JSON, assets outside `deploy/arin`, encrypt
  connector configuration with an installation key from `.env.arin`, and return
  only connector kind/label/status. Hash invite tokens, enforce role allowlists,
  expire invites after 72 hours, and store message content under a fixed byte
  limit.

- [ ] **Step 4: Add route coverage and verify green.**

  Expose the documented project settings/assets/connectors/team/agent routes and
  run the complete backend test suite. Confirm no secret configuration appears
  in JSON responses or logs.

## Task 5: Real frontend auth and studio

**Files:**
- Create: `sites/arin/src/lib/api.ts`
- Create: `sites/arin/src/types/studio.ts`
- Create: `sites/arin/src/components/AuthPage.tsx`
- Create: `sites/arin/src/components/StudioPage.tsx`
- Create: `sites/arin/src/components/ProjectStudio.tsx`
- Create: `sites/arin/src/studio.css`
- Modify: `sites/arin/src/App.tsx`
- Modify: `sites/arin/src/components/Header.tsx`
- Modify: `sites/arin/src/components/HeroBuilder.tsx`
- Modify: `sites/arin/src/components/DocsWelcome.tsx`
- Modify: `sites/arin/src/styles.css`
- Modify: `sites/arin/scripts/smoke-test.mjs`

**Interfaces:**
- `api.request<T>(path: string, options?: RequestInit): Promise<T>`
- `api.register(payload): Promise<Session>`
- `api.login(payload): Promise<Session>`
- `api.listProjects(): Promise<Project[]>`
- `api.buildProject(projectId, payload): Promise<Project>`
- `api.updateFile(projectId, path, content): Promise<ProjectVersion>`
- `api.publishProject(projectId): Promise<Deployment>`

- [ ] **Step 1: Write failing frontend smoke assertions.**

  Extend the Node smoke test to require `/auth` and `/studio` shell routes and
  source markers for real login, project list, build, preview, settings, and
  publish controls. Add a browser test script that starts the temporary backend,
  registers a synthetic user, logs in, creates a project, and confirms the
  studio receives a project response.

- [ ] **Step 2: Run the frontend tests and verify red.**

  Run:

  ```bash
  npm --prefix sites/arin test
  ```

  Expected: failure because `/auth`, `/studio`, and API client markers are not
  present.

- [ ] **Step 3: Implement the typed API client and auth route.**

  Use `credentials: 'include'`, keep the CSRF token in React memory only, route
  authenticated users to `/studio`, and show server error messages without
  reflecting untrusted HTML. Add real Login/Register forms with accessible
  labels and pending/error states.

- [ ] **Step 4: Implement studio/project UI.**

  Add workspace/project list, prompt builder that calls `/build`, project file
  list/editor, preview iframe, version restore, settings form, asset upload,
  connector list, member invite, agent history, publish/unpublish controls, and
  a public link. Keep generated preview in an iframe with `sandbox="allow-forms
  allow-scripts"` and do not put session data in local storage.

- [ ] **Step 5: Update landing/docs links and run frontend typecheck/build/smoke.**

  `Create account`, `Log in`, hero Build it, quickstart, and docs actions must
  point at real routes. Run `npm --prefix sites/arin test` and a browser check at
  desktop/mobile sizes. Expected: all shell routes and local assets pass.

## Task 6: Production process, Caddy, environment, and release checks

**Files:**
- Create: `sites/arin/.env.arin.example`
- Create: `deploy/systemd/arin.service`
- Create: `sites/arin/scripts/integration-smoke.py`
- Modify: `deploy/caddy/Caddyfile`
- Modify: `.gitignore`
- Modify: `docs/cloudflare-deployment.md`
- Modify: `sites/arin/README.md`

- [ ] **Step 1: Write failing integration smoke checks.**

  The temporary service smoke script must exercise health, registration, login,
  project build, file edit, preview, publish, public fetch, unpublish, and
  public 404. Require status/error shape and the sandbox CSP header.

- [ ] **Step 2: Run the integration smoke script and verify red until the service exists.**

  Run:

  ```bash
  PYTHONPATH=sites/arin python3 sites/arin/scripts/integration-smoke.py
  ```

- [ ] **Step 3: Add the production service and environment example.**

  The systemd user unit runs `/usr/bin/python3 -m arin_app.server` from
  `/home/%i/zeaz/sites/arin`, loads ignored `.env.arin`, restarts on failure,
  uses `UMask=0077`, `NoNewPrivileges=true`, `ProtectSystem=full`, and writes
  only to `data/arin`. The example documents port, DB path, session secret,
  connector key, and optional AI provider values without populated secrets.

- [ ] **Step 4: Route dynamic paths through Caddy and validate configuration.**

  In the `arin.zeaz.dev:8080` block, send `/api/*`, `/preview/*`, and `/app/*`
  to `127.0.0.1:8787`, preserve static fallback for the Vite shell, and keep
  security headers on both paths. Run `caddy validate` before reload.

- [ ] **Step 5: Run integration smoke and production checks.**

  Run Python compile/tests, frontend build/smoke, Caddy validation, systemd unit
  syntax inspection, and the temporary integration script. Only then build and
  copy the static artifact to ignored `deploy/arin` and reload Caddy/service.

## Task 7: Live deploy and completion audit

**Files:**
- Modify only ignored runtime files: `.env.arin`, `data/arin/*`, `deploy/arin/*`
- No Cloudflare Terraform change is required unless a new public hostname is
  explicitly needed; `arin.zeaz.dev` already routes to Caddy.

- [ ] **Step 1: Verify local origin services.**

  Confirm `arin.service`, Caddy, and cloudflared are active; query
  `http://127.0.0.1:8787/api/health` and the Caddy Host route.

- [ ] **Step 2: Perform the live reload with a rollback copy.**

  Save a timestamped copy of the current `deploy/arin` artifact and use the
  validated build. Reload the Arin service and Caddy; do not restart the
  unrelated MooPiew service.

- [ ] **Step 3: Verify the real public lifecycle.**

  With synthetic credentials only, execute register/login/create/build/edit/
  preview/publish/unpublish at `https://arin.zeaz.dev`. Confirm anonymous
  project/API access is rejected, published output is sandboxed, unpublished
  output is 404, assets load, and existing public hosts still return their
  baseline status.

- [ ] **Step 4: Run final source/state audit.**

  Run `git diff --check`, secret-pattern scan over tracked changes, frontend
  build/smoke, backend tests, integration smoke, Caddy validation, and Terraform
  plan. Confirm no `.env`, SQLite, upload, generated runtime file, or user
  `app.py` change is staged or overwritten.

- [ ] **Step 5: Report live URL, routes, tests, and any explicitly out-of-scope behavior.**

  Do not claim native App Store publishing or arbitrary backend code execution;
  report the actual sandboxed static publish boundary.
