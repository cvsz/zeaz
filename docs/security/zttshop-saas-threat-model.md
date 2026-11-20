# zTTShop SaaS Threat Model

- Status: Initial design baseline; not an independent security assessment or production approval
- Date: 2026-11-20
- System: Proposed zTTShop AI Commerce Assistant SaaS
- Related: `docs/adr/ADR-001-zttshop-saas-service-boundary.md`, `SECURITY.md`, `zeaz.md`

## 1. Scope and security objectives

This threat model covers the proposed SaaS control plane, tenant workspace, AI workflow, subscription/usage metering, connector authorization, webhook processing and external channel actions.

It does not certify the existing zTTShop demo, MooPiew runtime, TikTok app review, payment provider account or any production deployment.

Security objectives:

1. Prevent cross-tenant confidentiality and integrity failures.
2. Ensure only authorized tenant members can access tenant resources and actions.
3. Prevent forged, replayed or duplicated billing and channel events from changing state incorrectly.
4. Bound AI, connector, storage and background-job costs.
5. Preserve trustworthy audit, usage and billing evidence.
6. Minimize customer data exposure to model providers and external platforms.
7. Allow operators to disable a connector or the whole SaaS boundary without disrupting MooPiew.

## 2. System assets

| Asset | Classification | Security requirement |
| --- | --- | --- |
| User identity, sessions and recovery factors | Restricted | Strong authentication, secure session lifecycle, least privilege |
| Tenant membership and role assignments | Confidential | Server-side authorization, audited changes |
| Tenant product catalogue and knowledge base | Confidential | Tenant isolation, provenance and retention |
| Conversations and customer references | Confidential / potentially personal data | Minimize, encrypt, access audit and retention |
| OAuth access/refresh tokens | Restricted | Envelope encryption, no browser/log exposure, rotation/revocation |
| Payment-provider credentials and webhook secrets | Restricted | Secret store, scoped access, rotation and audit |
| Subscription and payment references | Confidential | Server-side ownership, reconciliation and audit |
| Usage events and quota reservations | Confidential / financial evidence | Append-only events, idempotency and reproducible aggregation |
| Order/inventory actions | Confidential / business-critical | Human approval in beta, idempotency and state validation |
| Audit records and incident evidence | Confidential | Restricted write access, integrity and retention |
| Model prompts and outputs | Confidential; may contain personal data | Data minimization, provider policy and bounded retention |

## 3. Trust boundaries and data flows

```text
TB1: Untrusted browser
    |
    | TLS, session token, CSRF protection
    v
TB2: Edge / reverse proxy
    |
    | authenticated request, bounded body/rate
    v
TB3: SaaS API
    |-- identity and tenant membership checks
    |-- plan entitlement / quota reservation
    |-- tenant-scoped PostgreSQL transaction
    |
    +--> TB4: Private worker / outbox
    |       |--> TB5: AI provider or approved gateway
    |       |--> TB6: Facebook / Shopee official APIs
    |       +--> TB7: Billing provider
    |
    +--> TB8: Private file/object storage
    |
    +--> TB9: Operator console / break-glass access
```

All inbound browser input, external webhook payloads, model output, connector responses, uploaded files and queue messages are untrusted. A tenant identifier is trusted only after the server resolves it from the authenticated principal and verified membership.

## 4. Attacker model

Assume an attacker may:
- be an unauthenticated internet user;
- hold a valid account in one tenant and attempt to access another tenant;
- compromise a low-privilege user or obtain a stolen session;
- submit malformed, oversized, replayed or high-volume requests;
- exploit race conditions in quota, subscription or connector workflows;
- send forged or duplicate webhook events;
- control product text, uploaded documents or customer messages to prompt-inject the AI;
- exploit a compromised connector token or provider outage;
- abuse public endpoints to exhaust model/API or storage budgets;
- obtain access to a developer workstation, CI artifact or misconfigured log;
- act as a malicious tenant owner attempting to access another tenant's data.

Out of scope for this initial baseline: compromise of the cloud provider control plane, cryptographic primitive break, physical host compromise and malicious privileged repository maintainers. These remain residual risks requiring infrastructure controls and independent review.

## 5. STRIDE threat register

| ID | Threat / STRIDE | Impact | Required mitigations | Verification evidence |
| --- | --- | --- | --- | --- |
| T-01 | Cross-tenant object access (EoP / Information Disclosure) | Critical confidentiality and integrity breach | Server-derived tenant context; RLS with FORCE; composite tenant foreign keys; no BYPASSRLS; tenant-scoped cache/job keys | Automated negative tests across every API, query, export, search, worker and webhook path |
| T-02 | Client-supplied tenant ID substitution (Spoofing / EoP) | Unauthorized tenant access | Ignore client ownership IDs; resolve membership from authenticated identity; explicit active-tenant selection validated server-side | Tampering tests for path, body, headers and query |
| T-03 | Session theft / account takeover (Spoofing) | Full tenant compromise | OIDC issuer/audience validation, secure cookies, CSRF, short session lifetime, refresh rotation, revocation, MFA/step-up for sensitive actions | Auth integration tests, cookie/header inspection, session revocation test |
| T-04 | Privilege escalation through role or invitation mutation (EoP) | Unauthorized admin and billing control | Server-side RBAC; invitation expiry/single-use; owner-transfer safeguards; audit; step-up auth | Role matrix and negative authorization tests |
| T-05 | SQL injection or unsafe dynamic filtering (Tampering / EoP) | Data exfiltration or mutation | Parameterized SQL, schema validation, safe query builders, least-privilege DB role | SAST and injection regression tests |
| T-06 | RLS bypass or pooled tenant context leakage (EoP / Info Disclosure) | Cross-tenant exposure | App role is not table owner and lacks BYPASSRLS; FORCE RLS; transaction-local tenant context; pool reset; deny missing context | Database integration tests using production-equivalent roles and concurrent pooled requests |
| T-07 | Forged/replayed channel webhook (Spoofing / Tampering) | Fake messages/orders or repeated actions | Official signature validation, timestamp tolerance, event ID uniqueness, replay storage, bounded body, secret rotation | Invalid signature, stale timestamp, duplicate and out-of-order tests |
| T-08 | Duplicate/out-of-order connector jobs (Tampering / DoS) | Duplicate orders, stock drift or message spam | Inbox/outbox, idempotency keys, state machine, provider reconciliation, bounded retries and DLQ | Retry, race, timeout-after-provider-success and replay tests |
| T-09 | OAuth CSRF, code interception or token leakage (Spoofing / Info Disclosure) | Connector account takeover | State/nonce, PKCE where supported, exact redirect URI, one-time code exchange, encrypted tokens, no query/log leakage | OAuth negative tests, redirect allowlist and secret scan |
| T-10 | Billing webhook forgery or event replay (Spoofing / Tampering) | Unauthorized activation, suspension or refund state | Provider signature + timestamp, provider-side object reconciliation, unique event IDs, idempotent state transitions | Provider sandbox tests and replay/out-of-order fixtures |
| T-11 | Quota race or metering tampering (Tampering / DoS) | Unbilled spend or wrongful suspension | Append-only event ledger; atomic reservation; unique event IDs; immutable plan versions; reconciliation | Parallel quota tests, duplicate event tests and recomputation checks |
| T-12 | Prompt injection in customer messages/catalogues (Tampering) | Data exfiltration or unauthorized tool actions | Treat content as data; no secrets in prompt; tool allowlist; structured output validation; no autonomous consequential action; human approval | Adversarial prompt suite and tool authorization tests |
| T-13 | AI hallucinated or unsubstantiated product claims (Tampering / Repudiation) | Customer harm, legal/reputation risk | Tenant-approved source material, claim allowlist, citation/provenance, confidence/handoff, restricted domain policy | Golden-set evaluations and human review of claims |
| T-14 | Sensitive data sent to external model (Info Disclosure) | Privacy breach | Explicit provider topology; minimization/redaction; tenant consent and provider data terms; no silent cloud fallback | Egress tests, provider adapter tests and configuration audit |
| T-15 | Public API/model abuse (DoS / Elevation of Cost) | Service outage and unbounded spend | Authenticated tenant API, IP/user/tenant rate limits, request/token bounds, queue quotas, budget circuit breakers | Load and abuse tests; hard-limit enforcement evidence |
| T-16 | Malicious upload or parser exploit (Tampering / EoP) | Code execution or data exposure | Private storage, allowlisted file types, size limits, signature inspection, malware scan where available, no inline execution | Upload fuzzing, content-type spoof and path traversal tests |
| T-17 | Secret exposure in logs, CI or browser bundle (Info Disclosure) | Account/provider compromise | Secret manager, redaction, least privilege, no secrets in frontend env/build, secret scanning, short-lived credentials | CI secret scan and browser artifact inspection |
| T-18 | Operator misuse or compromised admin account (EoP / Repudiation) | Cross-tenant access and irreversible changes | Separate operator principal, MFA, just-in-time break-glass, reason codes, time-bound grants and audit | Break-glass tabletop and audit completeness test |
| T-19 | Backup compromise or incomplete restore (Info Disclosure / DoS) | Bulk tenant data exposure or loss | Encrypted backups, separate keys, access restriction, restore drills, retention and deletion policy | Restore test and backup access review |
| T-20 | Provider outage, throttling or policy revocation (DoS) | Workflow interruption or stuck jobs | Circuit breakers, bounded retries, provider status, reconciliation, safe queue pause and manual handoff | Failure-injection and queue recovery tests |
| T-21 | Cross-tenant analytics/search leakage (Info Disclosure) | Data leakage via derived datasets | Tenant filter at source and query layer, scoped indexes and cache keys, export authorization | Cross-tenant tests for reports, search and analytics |
| T-22 | Subscription state race / downgrade bypass (EoP) | Unauthorized feature use | Server-side entitlement evaluation; immutable event history; versioned plan; grace-period policy explicit | Concurrent billing-event and entitlement transition tests |

## 6. Security invariants

These invariants are mandatory for the beta:

1. No request, job, export or webhook can select a tenant solely by supplying a tenant ID.
2. Every tenant-owned row and derived resource has an enforceable tenant boundary.
3. Missing or invalid identity, membership, tenant context, webhook signature or entitlement fails closed.
4. No AI output can directly execute a consequential business action.
5. No channel connector can mutate orders, inventory or payments without an approved workflow and idempotency key.
6. No provider token or payment secret is returned to a browser or written to logs.
7. No model/provider fallback can create unapproved external cost or data egress.
8. Usage cannot exceed a tenant's hard budget through concurrent requests or retries.
9. Billing state is derived from verified provider state and immutable internal events, not browser redirects.
10. MooPiew SQLite data and credentials remain inaccessible to zTTShop tenant principals.
11. Operator break-glass access is explicit, time-bound and audited.
12. Disabling zTTShop or a connector does not stop MooPiew.

## 7. Required security test plan

Before accepting real customer data, implement and pass:

### Identity and tenant isolation
- unauthenticated and expired-session denial;
- invalid issuer/audience/signature denial;
- membership removal and role downgrade take effect;
- cross-tenant IDOR tests for every resource and HTTP verb;
- RLS tests with the actual restricted application DB role;
- missing tenant context denial;
- concurrent pooled-connection tests to detect tenant-context leakage;
- cross-tenant search, analytics, exports, file access, cache and worker tests.

### Billing and metering
- invalid signature, stale timestamp, replay and duplicate event tests;
- out-of-order subscription lifecycle events;
- provider timeout after successful charge followed by reconciliation;
- refund, dispute, cancellation and failed-renewal transitions;
- concurrent quota reservation at the hard limit;
- duplicate usage event and aggregate recomputation;
- currency/minor-unit and rounding boundary tests.

### Connectors and AI
- invalid OAuth state, redirect URI and token refresh failure;
- invalid/duplicate/out-of-order webhook;
- provider timeout after remote mutation;
- prompt injection and malicious catalogue text;
- external model egress disabled by configuration;
- token, request-size, concurrency and cost limits;
- human-approval bypass attempts.

### Operations
- encrypted backup and isolated restore;
- secret rotation/revocation;
- operator break-glass expiry and audit;
- worker pause, DLQ replay and kill-switch behavior;
- service disablement without MooPiew impact.

## 8. Beta admission gates

A controlled beta is **not approved** until all of the following are evidenced:

- independent architecture and threat-model review;
- tenant isolation and RLS tests pass using restricted DB roles;
- no unresolved critical/high security findings;
- authentication, session revocation and operator MFA/step-up verified;
- privacy notice, customer data roles, retention and deletion process reviewed;
- backup restore drill passes;
- subscription entitlement and usage reconciliation pass;
- provider sandbox webhook tests pass;
- one official channel connector has verified developer access and sandbox acceptance;
- human approval and safe-disable paths work;
- hard cost caps and per-tenant usage visibility work;
- support owner, incident escalation and service objectives are documented;
- customer pilot agreement and consent/data processing requirements are satisfied.

## 9. Residual risks and assumptions

- RLS is defense in depth, not a substitute for correct application authorization and integration tests.
- A shared-database model has a larger shared blast radius than database-per-tenant isolation.
- Free hosting tiers and a self-hosted single node may not provide production availability, backup guarantees or regional residency.
- Provider API permissions and rate limits can change; current access is not assumed.
- The current TikTok Login Kit scope does not provide posting, messaging or marketplace operations.
- Product-specific regulatory, privacy, consumer protection and tax obligations require qualified review before onboarding.
- This threat model is a design artifact. It does not establish that controls have been implemented or tested.

## 10. Review sign-off

| Role | Required evidence | State |
| --- | --- | --- |
| Product owner | Scope and risk acceptance | Business model/segment approved; technical risks not accepted as production |
| Engineering reviewer | Architecture and implementation review | BLOCKED — independent review required |
| Security reviewer | Threat model and test coverage review | BLOCKED — independent review required |
| Privacy/legal reviewer | Data processing and customer terms | BLOCKED — qualified review required |
| Operations owner | Backup, restore, monitoring and incident readiness | NOT VERIFIED |
| Payment provider owner | Merchant eligibility and sandbox/live reconciliation | BLOCKED — provider/account evidence required |
| Channel provider owner | Official API access and webhook verification | BLOCKED — platform evidence required |
