# Arin Production Platform Design

## Goal

Turn the deployed Arin marketing replica into a real, single-origin app-builder
MVP at `https://arin.zeaz.dev`. A user must be able to create an account,
create a workspace and project from a plain-language prompt, inspect and edit
generated files, configure branding/SEO, add assets and connectors, invite
workspace members, preview the result, and publish an isolated static app.

The product must describe the current implementation honestly. Native App Store
submission and arbitrary server-code execution are outside this slice; mobile
output is responsive/PWA-ready web output, and published generated code runs in a
sandboxed static origin boundary.

## Current context

`sites/arin` is a standalone React/Vite frontend copied from the verified Arin
replica. The origin already runs Caddy and a Cloudflare Tunnel. Terraform owns
the `arin.zeaz.dev` DNS record and tunnel ingress to Caddy on
`127.0.0.1:8080`. The existing MooPiew Python service and its database remain a
separate source of truth and must not be modified for Arin data.

## Architecture

The implementation is a small same-origin service:

```text
Browser
  -> Cloudflare Tunnel
  -> Caddy :8080
     -> /api/*, /preview/*, /app/* -> Arin Python service :8787
     -> all other paths -> Arin Vite static build
  -> SQLite + private generated project files
```

The backend uses Python standard-library HTTP handling and SQLite because the
host already has a reviewed Python runtime, SQLite operational conventions, and
systemd/Caddy deployment patterns. It binds only to loopback. Runtime data is
stored under `data/arin/`, outside the public static root, with directory mode
`0700` and database/file mode `0600`.

The frontend remains a Vite build. The existing public landing page and docs
remain available, while `/auth`, `/studio`, `/preview/<project-id>`, and
`/app/<slug>` become real application routes.

## Identity and security

- Registration requires a normalized email, display name, and a password at
  least 12 characters long.
- Passwords use PBKDF2-HMAC-SHA256 with a random per-user salt and a high fixed
  iteration count. Plaintext passwords are never stored or logged.
- Login creates a random opaque session token stored only as a hash in SQLite.
  The browser receives an `HttpOnly`, `Secure`, `SameSite=Lax` cookie with a
  bounded expiry.
- Mutating same-origin requests require an `X-CSRF-Token` matching the token
  returned by the authenticated session bootstrap endpoint.
- Workspace membership roles are `owner`, `editor`, and `viewer`. Project
  writes require owner/editor; member management requires owner.
- Login, registration, invite acceptance, and build endpoints use bounded
  request sizes and loopback-safe rate limiting. All paths and generated file
  names are normalized and rejected if they escape the project directory.
- Generated previews and published apps are served with a restrictive CSP and
  `sandbox` boundary. They cannot use Arin cookies, call the Arin API, or read
  same-origin private data. Generated static content is the only publishable
  artifact; no generated server code is executed by the Arin service.
- Uploads are JSON base64 assets with a 5 MiB per-file limit, MIME allowlist,
  generated storage names, and no executable path. Asset metadata is stored in
  SQLite and content is stored outside the public root.
- Every authentication, membership, build, file, asset, connector, and publish
  mutation writes an audit event without secrets or raw file contents.

## AI and generation

The backend supports an OpenAI-compatible chat-completions endpoint configured
only through ignored environment variables:

- `ARIN_AI_BASE_URL` — empty disables remote generation.
- `ARIN_AI_API_KEY` — optional secret, never returned to the browser.
- `ARIN_AI_MODEL` — configured model name.

Remote generation must return a strict JSON project specification containing a
title, summary, theme, pages, and safe static files. The server validates the
schema, caps output size, rejects path traversal and unsupported file types,
and falls back to the deterministic local template generator when the provider
is unavailable or returns invalid output. The local generator maps the existing
categories and common prompts to useful CRM, portal, operations, inventory,
marketing, and mobile-ready templates, so the product has a real working path
without a provider credential.

The agent conversation is persisted per project as bounded user/assistant
messages. A build creates an immutable project version; editing a file creates a
new version snapshot. Version history can be listed and restored by an editor.

## Data model

The Arin database contains these tables:

- `users`: id, email, name, password hash/salt, timestamps.
- `sessions`: token hash, user id, CSRF token hash, expiry, timestamps.
- `workspaces`: id, name, slug, owner, timestamps.
- `workspace_members`: workspace/user/role with unique membership.
- `projects`: workspace, name, slug, prompt, category, status, current version,
  branding/SEO JSON, timestamps.
- `project_versions`: immutable version metadata and generation source.
- `project_files`: version, normalized path, MIME, UTF-8 content, hash.
- `project_assets`: project, original name, generated storage name, MIME, size.
- `connectors`: project, type, label, encrypted-at-rest configuration, status.
- `invites`: workspace, email, role, hashed token, expiry and acceptance state.
- `agent_messages`: project, user/assistant role, bounded content, version link.
- `deployments`: project, slug, version, status and publish timestamps.
- `audit_events`: actor, action, target, safe metadata and timestamp.

All IDs are random URL-safe identifiers. Project slugs and publish slugs are
unique and normalized. SQLite foreign keys, WAL mode, transactions, and
explicit uniqueness constraints protect concurrent mutations.

## HTTP API

Unauthenticated:

- `GET /api/health`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/session`
- `POST /api/auth/logout`
- `POST /api/invites/accept`

Authenticated:

- `GET/POST /api/workspaces`
- `GET /api/workspaces/<id>`
- `GET/POST /api/workspaces/<id>/members` and `POST /api/workspaces/<id>/invites`
- `GET/POST /api/projects`
- `GET /api/projects/<id>`
- `POST /api/projects/<id>/build`
- `GET /api/projects/<id>/versions`
- `POST /api/projects/<id>/versions/<version>/restore`
- `GET/PUT /api/projects/<id>/files/<path>`
- `POST /api/projects/<id>/assets`
- `GET/POST/DELETE /api/projects/<id>/connectors`
- `PUT /api/projects/<id>/settings`
- `GET/POST /api/projects/<id>/agent/messages`
- `POST /api/projects/<id>/publish` and `POST /api/projects/<id>/unpublish`

Public isolated delivery:

- `GET /preview/<project-id>` serves the current draft inside the preview
  boundary.
- `GET /app/<published-slug>` serves the published version inside the same
  boundary.

Error responses use stable JSON `{ "error": { "code", "message" } }` shapes;
messages never contain passwords, API keys, session tokens, or filesystem
paths.

## Frontend product flow

- The landing CTA calls the real build flow. Signed-out users are sent to
  `/auth?next=/studio`; signed-in users are taken to `/studio/new` with the
  prompt preserved.
- `/auth` provides registration/login and displays the current session state.
- `/studio` lists the current user's workspaces and projects.
- `/studio/projects/<id>` is the builder: prompt/agent panel, file list and
  editor, live preview iframe, branding/SEO settings, assets, connectors,
  members, versions, and publish controls.
- The docs page links to the quickstart and real studio route. Copy that claims
  backend/auth/database/publish behavior is backed by the API or is explicitly
  labeled as a future integration.

The first UI pass uses accessible native controls and the existing design
system. No secrets are placed in browser source, local storage, URLs, or
generated files.

## Deployment

- Add an `arin.service` systemd unit running the loopback Python service with a
  dedicated `ARIN_DATA_DIR` and ignored `.env.arin`.
- Extend the existing host-specific Caddy block so API, preview, and publish
  paths proxy to `127.0.0.1:8787`; static paths continue to use `deploy/arin`.
- Keep Terraform's Cloudflare route unchanged: the tunnel already sends the
  complete hostname to Caddy.
- Update `deploy/arin` from the Vite build only after backend and frontend tests
  pass. Verify origin health, HTTPS auth/build flow, preview, and published
  sandbox behavior after reload.

## Testing and acceptance

- Python unit tests cover schema creation, password/session behavior, CSRF,
  workspace authorization, prompt generation, path safety, versioning, assets,
  connectors, and publish isolation.
- A Node smoke test builds the frontend and verifies `/`, `/docs/welcome`,
  `/auth`, `/studio`, and all referenced local assets.
- An integration smoke script starts the backend with a temporary database and
  executes registration, login, project build, file edit, preview, publish,
  and unpublish.
- Production verification confirms `https://arin.zeaz.dev/api/health`, the
  real auth/build flow, preview, publish, and that unpublished projects are not
  public. Existing Cloudflare routes and the user's unrelated `app.py` changes
  must remain untouched.
