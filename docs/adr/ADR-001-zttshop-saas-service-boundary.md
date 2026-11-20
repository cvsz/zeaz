# ADR-001: zTTShop SaaS Service Boundary and Data Architecture

- Status: Proposed for independent technical/security review
- Date: 2026-11-20
- Owners: ZEAZ product owner and designated engineering/security reviewers
- Scope: zTTShop AI Commerce Assistant, tenant control plane, usage metering, subscription lifecycle and channel connectors
- Related: `docs/zeaz-ai-saas-business-plan.en.md`, `docs/zeaz-ai-saas-business-plan.th.md`, `docs/sales-demo.md`, `docs/tiktok-submission.md`, `docs/ARCHITECTURE.md`, `docs/DATABASE.md`, `SECURITY.md`, `zeaz.md`

## Context

The current repository is a single-host MooPiew application. The Python service owns restaurant commerce operations and a private SQLite database. The TypeScript workspace contains a zTTShop sales demonstration. The demo uses in-memory seeded conversations, orders and stock values; it does not call Facebook Messenger, Shopee, payment or production order APIs.

The current TikTok integration is Login Kit for Web with `user.info.basic` to identify a signed-in account. Its submission notes explicitly state that Share Kit, Display API and Content Posting API are not implemented. TikTok login is not proof of permission to read messages, manage products, create orders or publish content.

There is no verified production multi-tenant SaaS control plane, customer subscription lifecycle, entitlement service, usage ledger or live Facebook/Shopee connector in the current application. The existing MooPiew SQLite database is the source of truth for restaurant orders, inventory, payments and operations and must not become the zTTShop tenant database.

## Decision

Adopt a **separate deployable zTTShop SaaS application boundary inside this monorepo**, with its own API, worker process, dedicated PostgreSQL database, migrations, secrets, deployment configuration and operational ownership. Reuse only reviewed UI components and API contracts from the existing TypeScript workspace. Do not import MooPiew runtime modules or share its SQLite database.

The initial implementation should be a modular monolith with a separately supervised worker, not a microservice fleet. The service may be split later only when independent scaling, deployment, security isolation or ownership justifies it.

### Logical topology

```text
Browser
  |
Cloudflare edge / WAF
  |
Caddy reverse proxy (private origin)
  |-- existing MooPiew routes -> existing Python service -> MooPiew SQLite
  |
  |-- zTTShop host/API routes -> zTTShop SaaS API
                                  |-- OIDC identity adapter
                                  |-- tenant authorization
                                  |-- plans / subscriptions / entitlements
                                  |-- usage ledger / quota reservations
                                  |-- connector authorization / webhooks
                                  |-- workflow API / human approval
                                  |
                                  +--> dedicated PostgreSQL database
                                  +--> private worker (outbox / retries)
                                  +--> AI provider adapter (explicitly configured)
                                  +--> official channel APIs only
```

The zTTShop application must have a distinct runtime identity, database credentials, secret namespace, backup policy, network policy and release lifecycle. Cloudflare and Caddy route changes are separate infrastructure changes and require an inspected IaC/configuration diff, an approved deployment window and origin health verification. No production DNS, Tunnel, Caddy or host mutation is authorized by this ADR.

## Decision details

### 1. Repository and runtime placement

- Add a dedicated application workspace under `apps/zttshop/` (or another path selected after confirming the current workspace conventions).
- Keep the customer-facing React demo source under `apps/web/src/sales-demo.tsx` until a reviewed migration replaces it with a real authenticated application.
- Use the repository's TypeScript toolchain for the application boundary, with strict TypeScript, runtime schema validation and a maintained HTTP framework selected after dependency/license/security review.
- Do not add dependencies or commit generated build output until the exact service and CI conventions are inspected.
- Keep the existing Python `app.py` and MooPiew SQLite domain unchanged. No zTTShop business entities may be stored in MooPiew tables.

### 2. Tenant model

Use a shared PostgreSQL database with a shared schema and mandatory `tenant_id` on every tenant-owned row. This is the simplest operational model for an initial SMB product, provided database and application isolation are both enforced.

Required controls:

- Resolve tenant membership from the authenticated server-side principal and active membership. Never authorize using a client-supplied `tenant_id`.
- Include tenant identity in every tenant-owned unique key, foreign key, query, cache key, object-storage key and background job.
- Use composite foreign keys/unique constraints to prevent cross-tenant references.
- Enable PostgreSQL Row-Level Security on every tenant-owned table. Apply `FORCE ROW LEVEL SECURITY`; application roles must not own protected tables and must not have `BYPASSRLS`.
- Set tenant context transaction-locally and fail closed if it is absent. Never use a pooled connection with tenant context that can leak between requests.
- Add cross-tenant negative tests for reads, writes, joins, exports, search, background jobs and webhook processing.
- Keep platform/operator administration separate from tenant roles and require explicit audited break-glass access.

Schema-per-tenant and database-per-tenant are deferred. Reconsider them if enterprise isolation, residency, noisy-neighbour or customer contractual requirements demand stronger separation.

### 3. Identity and authorization

- Use an OIDC-compatible identity boundary. Evaluate an existing ZEAZ identity service only after verifying its current OIDC issuer, audience, signing-key rotation, session revocation, MFA and operational readiness.
- Do not treat TikTok Login Kit `user.info.basic` as primary SaaS authentication or as authorization for commerce APIs.
- Model users, tenants, memberships, roles, invitations and sessions separately.
- Enforce tenant-scoped RBAC on the server for every API and job. Suggested initial roles: owner, admin, operator and read-only analyst.
- Require recent re-authentication or step-up authentication for credential rotation, billing ownership changes, exports, destructive actions and connector disconnection.
- Do not expose provider credentials, raw OAuth tokens or internal authorization claims to the browser.

### 4. Billing, subscriptions and usage

- Use a provider-neutral billing adapter. Select a real payment provider only after verifying legal-entity eligibility, Thailand and international availability, recurring-payment support, fees, settlement currency, refunds, tax documentation, webhook guarantees and data-processing terms.
- Keep provider customer/subscription IDs server-side. Store only provider references and minimum reconciliation metadata.
- Represent plans, subscription state, entitlements, limits and price versions in the SaaS database. Authorization and quota checks are server-side.
- Store all monetary values as integer minor units with an explicit ISO currency. Never use binary floating-point for money.
- Implement an append-only usage event ledger with unique idempotency/event IDs, tenant, meter, quantity, unit, source, occurred-at time and bounded metadata. Do not store message bodies in usage records.
- Aggregate usage into period buckets. Usage aggregation must be reproducible from immutable events.
- Reserve quota atomically before billable work; settle actual usage after completion and release reservations on failure/timeout. Prevent parallel requests from overspending the same quota.
- Fail closed at configured hard limits. Do not silently fall back to a paid provider or permit unbounded usage.
- Treat payment webhooks as untrusted until signature, timestamp/replay, event identity and provider-side state are verified. Process duplicate and out-of-order events idempotently through an inbox/outbox pattern.
- Provide an operator reconciliation path for disputed, missing, refunded and late payment events.

A sandbox billing adapter may be implemented before production provider selection. A sandbox success is not evidence of live merchant approval or settlement.

### 5. Workflow and connector boundary

- Normalize external channel events into versioned internal event contracts.
- Build each channel as a separate adapter with explicit capabilities, scopes, token lifecycle, rate limits, webhook verification and provider error mapping.
- Start with one connector only after official developer access and business eligibility are verified. Facebook Messenger and Shopee must be assessed independently; neither may be represented as available merely because a demo row says "Connected".
- Never scrape private pages, reuse browser cookies, reverse-engineer private endpoints or bypass official platform restrictions.
- Verify webhook signatures and timestamps, reject replay, persist provider event IDs, and process asynchronously with bounded retries and dead-letter visibility.
- Use idempotency keys for order creation and inventory mutation. Reconcile provider state before retrying ambiguous external writes.
- Require human approval for order placement, cancellation, refunds, customer broadcast, stock mutation and payment-related actions during the controlled beta.
- Keep the existing demo mode visibly labelled and technically separated from live connector status.

### 6. AI provider boundary

- Use an explicit provider topology per environment: local-only, gateway-only, direct-provider or hybrid.
- Keep model/provider credentials server-side. Never silently fall back from local/private inference to a hosted model.
- Enforce tenant-specific model policy, token/conversation quotas, timeouts, output limits and cost circuit breakers.
- Ground product answers in tenant-approved product data. Include source/version traceability and a human escalation path.
- Do not make medical, financial, legal or other high-impact claims. Product claims require customer-provided substantiation and review.
- Minimize prompt content and redact unnecessary personal data before external inference.

### 7. Data ownership and retention

- Tenant data includes catalogues, knowledge sources, conversations, customer references, workflow configuration, connector references, usage events and audit events.
- Define retention and deletion for every data class before accepting real customer data. Conversation content must have a customer-configurable retention period; usage and billing evidence may require a separate legally reviewed retention period.
- Store uploaded files in private object storage or an equivalent private filesystem boundary, never a public web root. Validate size, type and content, and scan where supported.
- Encrypt sensitive data in transit and at rest. Use envelope encryption/KMS or a documented protected key-management boundary for OAuth credentials.
- Backups must be tenant-aware only at the logical export layer, encrypted, access-controlled and restore-tested. Never mix zTTShop backups with MooPiew's operational database backup.

## Alternatives considered

| Option | Advantages | Rejected / deferred because |
| --- | --- | --- |
| Add tenant tables to MooPiew SQLite and `app.py` | Lowest apparent setup effort | Couples unrelated business domains, expands the blast radius, weakens isolation and creates competing ownership inside a restaurant operations database |
| Put the SaaS API inside the existing Python service | Reuses routing and deployment | Couples release/security lifecycle and runtime; existing service is intentionally single-host and SQLite-backed |
| Microservices from day one | Independent scaling and deployment | Too much operational overhead for zero-capital validation and no proven customer demand |
| Separate deployable app with dedicated PostgreSQL | Clear domain boundary, tenant controls, independent lifecycle | Requires a new service, database operations and deployment review; selected as the smallest safe production boundary |

## Consequences

Positive:
- MooPiew's restaurant operations and data ownership remain isolated.
- Tenant isolation, billing, metering and connector policies have a dedicated control plane.
- The product can evolve without forcing a premature microservice architecture.
- Provider integrations can be enabled independently after official access and security review.

Costs and constraints:
- A dedicated PostgreSQL service, backups, monitoring and on-call ownership are required before production.
- Zero incremental capital limits production hosting and provider choices; free-tier availability does not constitute an SLA.
- The initial service must not accept real customer data until tenant isolation, identity, retention, incident response and restore controls pass review.
- Billing provider selection and live marketplace integrations remain blocked on eligibility, credentials, official access and sandbox verification.

## Rollout gates

1. Approve this ADR and the accompanying threat model through independent review.
2. Obtain one paid-pilot customer and document scope, success metrics, data roles, consent/notices and support boundaries before building customer-specific live connectors.
3. Implement tenant/auth foundations and automated cross-tenant negative tests.
4. Implement internal subscription/entitlement and usage ledger with a sandbox billing adapter.
5. Verify the selected payment provider and one official channel connector in their respective sandboxes.
6. Run a controlled beta with synthetic data first, then minimum customer-authorized data.
7. Permit production onboarding only after security, privacy, restore, billing reconciliation, support and cost-control gates pass.

## Rollback

- Disable zTTShop public routing and connector processing independently.
- Stop the zTTShop worker before any schema rollback.
- Prefer forward-only, additive migrations; do not drop tenant or billing data as a rollback shortcut.
- Revoke connector grants and tokens through provider-supported flows, then destroy encrypted token material only under an approved deletion procedure.
- Preserve immutable billing and usage evidence for reconciliation.
- MooPiew service, database and routes must remain operational and unchanged.

## Approval record

Business model and initial customer segment: approved by the business owner in the conversation on 2026-11-20.

Technical architecture decision: proposed; requires independent engineering/security review before implementation.

Production routing, payment provider activation, paid infrastructure, customer-data onboarding and live connector activation: not authorized by this ADR.
