# ZERP — Codex Max Single Source of Truth

> Status: executable implementation contract
> Target path: `apps/zerp`
> Product name: **ZERP** (ZEAZ ERP)
> Upstream platform: Odoo 19
> Default edition: Odoo Community with optional, explicitly licensed Enterprise add-ons
> Primary deployment target: Ubuntu LTS, Docker Compose for development, hardened containers or systemd-compatible production deployment

This document is the authoritative implementation contract for every human and coding agent working on `apps/zerp`. Do not create competing roadmaps, hidden task lists, or undocumented architectural decisions. Update this file whenever scope, status, acceptance criteria, commands, dependencies, risks, or decisions change.

---

## 1. Mission

Build a production-grade, Thai-first, multilingual ERP platform based on Odoo that provides one connected operational system for ZEAZ businesses and customers. ZERP must support configuration, installation, extension, testing, deployment, backup, recovery, observability, security, data migration, and continuous delivery without requiring manual undocumented steps.

The target is not a demo. The target is an auditable, reproducible, upgrade-safe ERP distribution with clearly separated upstream code, custom modules, configuration, infrastructure, documentation, and generated artifacts.

## 2. Non-negotiable principles

1. **Single source of truth** — this file owns execution status and acceptance criteria.
2. **Upstream integrity** — never patch Odoo core when an extension, inherited model, inherited view, hook, adapter, or configuration can solve the requirement.
3. **License clarity** — Community and Enterprise code, assets, repositories, images, and modules must remain explicitly separated. Enterprise functionality requires valid entitlement and may not be copied or emulated unlawfully.
4. **Vertical slices only** — every implementation unit must be complete from data model through UI/API, authorization, tests, documentation, migration, observability, and rollback.
5. **No partial completion** — never leave commented placeholders, fake integrations, silently skipped tests, TODO-only code, or features that are visible but non-functional.
6. **Secure defaults** — no default credentials, no secrets in Git, no public database manager, no broad superuser use, no unrestricted RPC exposure, and no unvalidated file uploads.
7. **Upgrade safety** — custom modules must use stable public Odoo extension points and declare compatible versions and dependencies.
8. **Idempotent automation** — installation, configuration, upgrade, backup, restore, seeding, and deployment commands must be safe to rerun.
9. **Evidence before claims** — a feature is complete only when automated validation and an execution record prove it.
10. **Thai-first, multilingual by design** — Thai locale, timezone, currency, tax, addresses, documents, and translations are first-class requirements while English remains fully supported.

## 3. Product boundaries

### 3.1 Upstream layers

```text
Odoo Community 19
  ├── server/framework
  ├── official Community applications
  └── official localization modules

Odoo Enterprise 19 (optional; licensed)
  └── Enterprise add-ons only, mounted before Community add-ons

ZERP distribution
  ├── custom ZEAZ add-ons
  ├── Thai business extensions
  ├── integration adapters
  ├── deployment and operations automation
  ├── configuration schemas and examples
  ├── tests and quality gates
  └── documentation and runbooks
```

### 3.2 Repository target structure

Agents may refine this layout only through an architectural decision record.

```text
apps/zerp/
├── AGENTS.md
├── README.md
├── CHANGELOG.md
├── CODEX-MAX-SINGLE-SOURCE-OF-TRUTH.md
├── pyproject.toml
├── package.json
├── .env.example
├── config/
│   ├── odoo.conf.example
│   ├── logging.yaml
│   ├── modules.community.txt
│   ├── modules.enterprise.txt
│   ├── modules.zerp.txt
│   └── tenants.example.yaml
├── addons/
│   ├── zerp_base/
│   ├── zerp_localization_th/
│   ├── zerp_security/
│   ├── zerp_audit/
│   ├── zerp_integration/
│   ├── zerp_operations/
│   └── feature modules/
├── deploy/
│   ├── compose/
│   ├── docker/
│   ├── systemd/
│   ├── caddy/
│   ├── kubernetes/
│   └── terraform/
├── scripts/
│   ├── install.sh
│   ├── configure.sh
│   ├── start.sh
│   ├── stop.sh
│   ├── upgrade.sh
│   ├── backup.sh
│   ├── restore.sh
│   ├── verify.sh
│   ├── health-check.sh
│   └── release.sh
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── browser/
│   ├── security/
│   ├── migration/
│   └── performance/
├── docs/
│   ├── ARCHITECTURE.md
│   ├── INSTALLATION.md
│   ├── CONFIGURATION.md
│   ├── OPERATIONS.md
│   ├── SECURITY.md
│   ├── DISASTER-RECOVERY.md
│   ├── DATA-MIGRATION.md
│   ├── MODULE-MATRIX.md
│   ├── THAI-LOCALIZATION.md
│   ├── INTEGRATIONS.md
│   ├── TESTING.md
│   ├── RELEASE.md
│   ├── decisions/
│   └── execution-records/
└── tools/
```

## 4. Supported business capabilities

Every capability below must be classified in `docs/MODULE-MATRIX.md` as one of:

- `upstream-community`
- `upstream-enterprise-licensed`
- `official-localization`
- `zerp-custom`
- `external-integration`
- `deferred-with-rationale`

### 4.1 Foundation

- Organizations, companies, branches, operating units, teams, departments, warehouses, locations, users, contacts, partners, currencies, languages, timezones, units of measure, products, services, categories, price lists, taxes, fiscal positions, analytic dimensions, tags, activities, chatter, attachments, templates, sequences, numbering, scheduled jobs, email aliases, notifications, dashboards, search, filtering, import, export, and reporting.

### 4.2 Finance and accounting

- General ledger, chart of accounts, journals, receivables, payables, customer invoices, vendor bills, credit notes, debit notes where legally applicable, payments, bank statements, reconciliation, payment terms, multicurrency, fixed assets where supported, budgets, analytic accounting, expenses, tax reporting, withholding tax extensions, VAT, audit trail, lock dates, fiscal-year closing, attachments, approval controls, and financial statements.
- Thai localization: THB, Thailand chart of accounts mapping, VAT 7%, tax invoices, withholding tax certificates and reports, branch/head-office identification, Thai tax IDs, address formats, document numbering, Thai date rendering where required, and export formats required by configured business processes.
- Never claim legal or tax compliance solely from test success; require accountant/legal review before production activation.

### 4.3 CRM, sales, subscriptions, rental

- Leads, opportunities, pipelines, activities, teams, quotations, sales orders, product variants, price lists, discounts, promotions, approvals, subscriptions, renewals, recurring billing, rental quotations, availability, pickup/return, deposits, upsell, portal access, signatures, and reporting.

### 4.4 Purchase and supply chain

- Requests for quotation, purchase orders, vendor price lists, approvals, procurement rules, replenishment, inventory, lots, serial numbers, packages, barcodes, warehouses, routes, dropshipping, cross-docking where applicable, cycle counting, valuation, landed costs, internal transfers, delivery, returns, and traceability.

### 4.5 Manufacturing and operations

- Bills of materials, work centers, routings, manufacturing orders, work orders, by-products, scrap, subcontracting, planning, maintenance, quality checks, quality alerts, PLM/change control where licensed or custom, capacity, scheduling, costing, and traceability.

### 4.6 Point of sale and commerce

- POS sessions, cash control, receipts, refunds, discounts, loyalty, kitchen/preparation flow, product availability, customer capture, offline behavior, hardware integration abstraction, payment adapters, website, eCommerce, catalog, cart, checkout, delivery methods, payments, customer accounts, abandoned carts, order lifecycle, returns, invoicing, SEO, analytics, and consent.

### 4.7 Projects and services

- Projects, tasks, stages, milestones, timesheets, planning, field service where licensed/custom, helpdesk, SLAs, ticket routing, knowledge, appointments, customer portal, service products, billing, and profitability.

### 4.8 Human resources

- Employees, departments, contracts, recruitment, onboarding, attendance, leave, appraisals, referrals, fleet, equipment assignment, expenses, approvals, documents, skills, training records, and payroll only when supported by a validated localization or explicitly scoped custom module.
- HR data is sensitive. Enforce least privilege, field-level access where necessary, retention, auditability, and export/deletion workflows consistent with applicable policy.

### 4.9 Marketing and communications

- Email marketing, marketing automation where available, SMS adapter abstraction, social marketing where licensed, surveys, events, campaigns, UTM attribution, consent, suppression lists, templates, bounce handling, and analytics.

### 4.10 Documents, approvals, signatures, knowledge

- Document workspaces, metadata, access rules, retention, versioning, approvals, requests, e-signature where licensed or integrated, knowledge bases, templates, and audit trails.

### 4.11 ZEAZ integrations

- MooPiew commerce data bridge where required.
- Identity and SSO adapter.
- Payment providers through server-side adapters.
- Email and SMS providers.
- Object storage for attachments and backups.
- AI provider gateway for approved use cases; provider credentials never reach browsers.
- Accounting/banking exports and imports.
- Webhooks with signatures, replay protection, idempotency, delivery logs, retries, dead-letter handling, and reconciliation.

## 5. Architecture requirements

### 5.1 Runtime

- Odoo application nodes must be stateless except for approved local temporary files.
- PostgreSQL is the authoritative transactional database.
- Persistent attachments use a clearly documented filestore or object-storage strategy with backup consistency guarantees.
- Reverse proxy terminates TLS and sets correct proxy headers.
- Long-polling/websocket/event endpoints use a compatible worker/proxy configuration.
- Cron/scheduled actions must not execute concurrently in an unsafe way across replicas.
- Separate development, test, staging, and production environments.

### 5.2 Add-on precedence

For Enterprise deployments, the Enterprise add-ons directory must precede Community and ZERP paths where required by Odoo. The exact order must be documented and tested. Never mix unlicensed Enterprise code into Community builds.

### 5.3 Configuration

- Configuration is schema-controlled and environment-aware.
- `.env.example` contains names and safe examples only.
- Secrets come from an external secret store or protected deployment environment.
- Config validation must fail fast on missing required values, malformed URLs, weak production secrets, conflicting database settings, invalid add-on paths, or unsupported module combinations.
- Production must disable public database listing/management unless explicitly required and protected.

### 5.4 Multi-company and tenancy

Default to Odoo multi-company inside a controlled database unless isolation, data residency, regulatory, performance, or lifecycle requirements justify separate databases. Document the chosen tenancy model, record rules, shared master data, company-dependent properties, cross-company access, backup/restore granularity, and tenant deletion process.

## 6. Security and privacy invariants

- Use least privilege for PostgreSQL, operating-system users, Odoo groups, record rules, service accounts, CI tokens, and integration credentials.
- Never use the Odoo superuser as an integration identity.
- Enforce secure cookies, HTTPS, trusted proxy configuration, CSRF protection, clickjacking protection, content security policy where compatible, rate limiting at the edge, safe CORS, upload validation, malware scanning hook, and attachment authorization.
- Redact passwords, API keys, OAuth tokens, session identifiers, payment data, national IDs, employee data, and document contents from logs.
- Authenticate and authorize every external API and webhook operation.
- Validate webhook signatures before parsing side effects; enforce timestamp windows and idempotency keys.
- Record security-sensitive configuration and business mutations in an immutable or exportable audit stream.
- Run dependency, secret, container, static, and infrastructure scans in CI.
- Produce threat models for authentication, authorization, uploads, payments, public portal access, integrations, backup/restore, and administrator operations.
- Document PDPA responsibilities, lawful basis, consent where needed, purpose limitation, data minimization, retention, subject requests, breach response, and processor/subprocessor boundaries.

## 7. Data integrity invariants

- Business mutations that span related records must be transactional.
- Use Odoo ORM and supported APIs; direct SQL requires an explicit justification, parameterization, tests, and migration review.
- Money uses currency-aware decimal fields and configured rounding; never binary floating-point arithmetic for authoritative totals.
- Quantities honor units of measure and rounding.
- Stock cannot silently diverge from valuation.
- Posted accounting entries are not casually edited; corrections use supported reversal or adjustment flows.
- External operations are idempotent and reconcilable.
- Sequence/number allocation is concurrency-safe.
- Dates and datetimes have explicit timezone semantics.
- Every schema/data migration is forward-tested against a production-like backup and has a documented rollback or restore strategy.

## 8. Installation and deployment contract

The installer must support a fully automated, non-interactive mode and a guided interactive mode.

### 8.1 Required installer capabilities

- Detect supported Ubuntu version and architecture.
- Validate CPU, RAM, storage, filesystem, DNS, ports, time synchronization, and required kernel/container capabilities.
- Install or validate Git, Python/build dependencies, PostgreSQL client/server where selected, Node tooling where needed, wkhtmltopdf or supported report renderer, reverse proxy, container runtime, backup utilities, and observability agents.
- Fetch pinned Odoo Community source or image.
- Optionally fetch Enterprise add-ons only after validating required credentials/entitlement supplied outside source control.
- Create isolated system users, directories, permissions, database roles, configuration, logs, filestore, backup destinations, and services.
- Generate secrets using a cryptographically secure source.
- Initialize database, install selected module profile, load translations/localization, run migrations, create health probes, and verify login/API/report rendering.
- Produce a machine-readable installation report without revealing secrets.
- Be idempotent and support `--dry-run`, `--non-interactive`, `--profile`, `--edition`, `--domain`, `--database`, `--backup-dir`, and `--rollback` or equivalent.

### 8.2 Deployment profiles

- `dev`: Docker Compose, mounted custom add-ons, debug tooling, disposable data option.
- `ci`: ephemeral PostgreSQL, deterministic test database, no external network except explicitly mocked services.
- `staging`: production-like topology with non-production credentials and sanitized data.
- `production-single-node`: hardened reverse proxy, Odoo workers, PostgreSQL or managed database, backup, monitoring, and restore verification.
- `production-ha`: multiple app nodes, managed or HA PostgreSQL, shared/object filestore design, load balancer, scheduled-job coordination, rolling deployment, and tested failure recovery.

## 9. Observability and operations

- Structured logs with correlation IDs and redaction.
- Metrics for HTTP latency/errors, worker saturation, database connections/locks, cron duration/failures, queue/webhook delivery, email failures, authentication failures, storage use, backup success, restore verification, and business-critical flows.
- Health endpoints distinguish liveness, readiness, and dependency degradation.
- Alerting has severity, owner, runbook, deduplication, and escalation.
- Backups include PostgreSQL plus filestore/object data and configuration metadata, are encrypted, copied off-host, retention-managed, and restore-tested.
- Define RPO and RTO per deployment profile.
- Releases include versioned images/artifacts, SBOM, checksums, migration notes, rollback instructions, and provenance.

## 10. Testing strategy

### 10.1 Mandatory layers

- Python/unit tests for business logic, constraints, computed fields, permissions, and adapters.
- Odoo module installation and upgrade tests.
- Transaction/integration tests with PostgreSQL.
- API/webhook contract tests.
- Browser tests for critical workflows.
- Access-control matrix tests using real user roles and companies.
- Thai localization and document rendering tests.
- Data migration tests using representative anonymized fixtures.
- Backup/restore tests.
- Performance tests for agreed critical paths.
- Security tests for privilege escalation, insecure direct object references, uploads, webhook replay, session handling, and secret leakage.

### 10.2 Minimum critical workflows

1. Lead to opportunity to quotation to sales order to delivery to invoice to payment and reconciliation.
2. Purchase request/RFQ to receipt to vendor bill to payment.
3. Product replenishment and stock valuation.
4. Manufacturing order from demand through consumption, production, quality, and costing.
5. POS session opening, sale, payment, receipt, refund, and closing.
6. eCommerce product to checkout, payment adapter, delivery, return, and invoice.
7. Employee expense submission, approval, posting, and reimbursement.
8. Multi-company access and intercompany restrictions.
9. Thai VAT/tax invoice and withholding workflows selected by the configured profile.
10. Backup, destructive test mutation, restore, and reconciliation.

## 11. Quality gates

Every pull request affecting `apps/zerp` must run all applicable gates:

```bash
./apps/zerp/scripts/verify.sh
```

The aggregate verification command must include, as applicable:

- formatting and linting
- XML/CSV/manifest/schema validation
- Python static checks
- JavaScript/TypeScript checks
- shell syntax and shellcheck
- module install tests
- module upgrade tests
- unit and integration tests
- browser smoke tests
- access-control tests
- localization tests
- dependency and license checks
- secret scanning
- container/IaC scanning
- generated artifact drift checks
- documentation link/command validation
- `git diff --check`

No gate may be disabled merely to obtain a passing result. Fix the defect, narrow the documented scope, or record a temporary exception with owner, risk, expiry, and remediation issue.

## 12. Execution model

### 12.1 Phase map

| Phase | Outcome |
|---|---|
| 0 | Repository inventory, decisions, module/license matrix, risk register, baseline validation |
| 1 | Reproducible development and CI environment |
| 2 | Automated installation, configuration, health checks, backup and restore |
| 3 | Foundation, security, audit, Thai language and base localization |
| 4 | CRM, sales, purchase, inventory and accounting vertical flows |
| 5 | Manufacturing, quality, maintenance and operations |
| 6 | POS, website, eCommerce, payments and customer portal |
| 7 | Projects, services, helpdesk, HR, documents and approvals |
| 8 | ZEAZ integrations, identity, messaging, AI gateway and data migration |
| 9 | Observability, performance, HA, DR, release engineering and security hardening |
| 10 | Production acceptance, operator training, runbooks, launch and post-launch verification |

Do not implement all applications simultaneously. Within each phase, choose exactly one complete vertical slice, complete it, validate it, commit it, open a PR, and wait for merge before starting the next slice unless the repository owner explicitly authorizes a different flow.

### 12.2 Definition of a vertical slice

A vertical slice includes:

- explicit business requirement
- module/profile classification and license status
- models and constraints
- access control and record rules
- views and user workflow
- API/integration contract if applicable
- localization and translations
- migration/seed data
- logging, metrics, and audit events
- tests at required layers
- documentation and operator notes
- upgrade and rollback validation
- changelog and execution record

### 12.3 Definition of done

A slice is complete only when:

- acceptance criteria are objectively satisfied
- no placeholders or known broken paths remain
- clean install succeeds
- upgrade from the previous supported state succeeds
- applicable tests and scans pass
- authorization is tested negatively and positively
- backup/restore implications are documented
- documentation matches implementation
- this SSOT, module matrix, changelog, validation report, and execution record are updated
- commit and PR contain one coherent slice
- CI is green and review feedback is resolved

## 13. Codex Max master prompt

Copy the following prompt into Codex at the repository root. This prompt is intentionally strict.

```text
You are the lead ERP platform engineer for cvsz/zeaz.

Your only target for this mission is apps/zerp.
The authoritative contract is:
apps/zerp/CODEX-MAX-SINGLE-SOURCE-OF-TRUTH.md

MISSION
Build ZERP, a production-grade Thai-first Odoo 19 ERP distribution, by implementing one complete vertical slice per pull request until every non-deferred acceptance criterion in the SSOT and module matrix is complete.

MANDATORY STARTUP PROCEDURE
1. Read the root AGENTS.md and every applicable nested AGENTS.md.
2. Read the ZERP SSOT completely.
3. Revalidate the current repository, branch, open pull requests, CI status, file tree, dependency versions, Odoo version, edition/license boundaries, existing modules, tests, docs, deployment files, and execution records. Never rely on an earlier inventory.
4. Run the current baseline verification before editing.
5. If the baseline is failing, distinguish pre-existing failures from regressions and either fix them as the current coherent slice or record a blocking report. Never conceal failures.
6. Select exactly one highest-priority incomplete vertical slice whose prerequisites are satisfied.
7. Write or update a slice plan with concrete acceptance criteria before implementation.

IMPLEMENTATION RULES
- Never patch Odoo core when a supported extension mechanism exists.
- Never copy or recreate restricted Enterprise code. Enterprise modules require valid licensing and explicit configuration.
- Preserve backward compatibility unless the active slice explicitly defines and tests a migration.
- Use Odoo ORM and supported framework APIs.
- Treat authorization, record rules, multi-company isolation, auditability, migration, observability, and rollback as first-class implementation work.
- Never expose secrets, provider credentials, database credentials, internal tokens, or unrestricted administrative operations to browsers.
- Never leave TODO-only behavior, mocks in production paths, commented-out implementations, silent exception swallowing, skipped validation, or partially wired UI.
- Keep external providers behind server-side adapters with timeout, retry policy, idempotency, signature verification, reconciliation, metrics, and deterministic tests.
- Keep all automation idempotent and support safe dry-run where meaningful.
- Add dependencies only when justified, pinned or constrained appropriately, scanned, licensed compatibly, and documented.
- Update translations and Thai-specific behavior for user-visible features.

FOR EACH SLICE
1. Implement models, constraints, security, views, adapters, migrations, configuration, tests, docs, observability, and rollback as required.
2. Add positive, negative, permission, multi-company, upgrade, and failure-path tests.
3. Run formatting, lint, static checks, module install, module upgrade, unit, integration, browser, security, localization, dependency, secret, container, documentation, and drift checks as applicable.
4. Fix every regression introduced by the slice.
5. Update:
   - CODEX-MAX-SINGLE-SOURCE-OF-TRUTH.md status
   - docs/MODULE-MATRIX.md
   - CHANGELOG.md
   - validation report
   - docs/execution-records/<slice-id>.md
   - relevant architecture, operations, security, API, migration, and user documentation
6. Review the diff for unrelated changes, secrets, generated drift, unsafe permissions, core patches, and missing tests.
7. Commit with a conventional, precise message.
8. Push a dedicated branch and open one pull request containing one complete vertical slice.
9. Include in the PR: scope, architecture, license/edition impact, migration, security, tests, validation evidence, operational impact, rollback, risks, and follow-up items.
10. Stop after opening the PR. Do not begin the next slice until the current PR is merged, unless explicitly authorized.

LOOP BEHAVIOR
After a slice is merged, repeat the mandatory startup procedure from the new main branch. Recompute priorities from actual repository state. Continue until all non-deferred criteria are complete and the final production acceptance phase passes.

FINAL COMPLETION CONDITION
Do not declare ZERP complete merely because modules install or the UI renders. Completion requires:
- all required vertical workflows operational end-to-end
- installation and upgrade reproducible
- security and multi-company isolation validated
- Thai localization acceptance completed
- integrations reconcilable and failure-tested
- monitoring, backups, restore verification, DR and release process operational
- documentation and runbooks accurate
- all required CI and production acceptance gates green
- no unresolved critical/high security findings
- final execution record and release signed off

Begin now with repository revalidation and Phase 0 inventory. Do not ask for permission for ordinary read-only analysis or test execution. Ask only when a required business, licensing, credential, destructive, production, or irreversible decision cannot be resolved from repository evidence.
```

## 14. Autonomous loop command template

Use a human-supervised loop. Do not automatically merge or bypass review protections.

```bash
#!/usr/bin/env bash
set -Eeuo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
SSOT="$REPO_ROOT/apps/zerp/CODEX-MAX-SINGLE-SOURCE-OF-TRUTH.md"

cd "$REPO_ROOT"

while true; do
  git fetch origin
  git switch main
  git pull --ff-only origin main

  codex exec "$(cat "$SSOT")"

  echo
  echo "Codex must have opened exactly one complete vertical-slice PR."
  read -r -p "Enter the merged PR number, or 'stop': " answer
  [[ "$answer" != "stop" ]] || break

  state="$(gh pr view "$answer" --json state,mergedAt --jq 'if .mergedAt then "merged" else .state end')"
  [[ "$state" == "merged" ]] || {
    echo "PR #$answer is not merged; stopping." >&2
    exit 1
  }
done
```

The loop is an orchestration aid, not a substitute for branch protection, CI, review, staging verification, licensing decisions, production approval, or business acceptance.

## 15. Phase 0 first-run checklist

The first Codex slice must create or complete all of the following without implementing broad business features prematurely:

- [ ] `apps/zerp/AGENTS.md`
- [ ] `apps/zerp/README.md`
- [ ] `apps/zerp/CHANGELOG.md`
- [ ] `apps/zerp/docs/ARCHITECTURE.md`
- [ ] `apps/zerp/docs/MODULE-MATRIX.md`
- [ ] `apps/zerp/docs/INSTALLATION.md`
- [ ] `apps/zerp/docs/CONFIGURATION.md`
- [ ] `apps/zerp/docs/SECURITY.md`
- [ ] `apps/zerp/docs/THAI-LOCALIZATION.md`
- [ ] `apps/zerp/docs/TESTING.md`
- [ ] `apps/zerp/docs/decisions/`
- [ ] `apps/zerp/docs/execution-records/`
- [ ] upstream version and edition decision
- [ ] Community/Enterprise/license matrix
- [ ] existing repository integration inventory
- [ ] target deployment profiles
- [ ] threat model and data classification
- [ ] baseline dependency and security scan
- [ ] baseline install/test commands
- [ ] risk register
- [ ] prioritized vertical-slice backlog with dependencies

## 16. Required decisions before production

The agents must not guess these decisions:

- Odoo Community-only versus licensed Enterprise profiles
- source installation versus official image/package strategy
- production topology and expected scale
- tenancy/database isolation model
- Thai accounting and payroll compliance scope and approving professional
- payment providers and merchant credentials
- SSO/identity provider
- email/SMS providers
- object storage and backup destinations
- RPO/RTO
- data migration sources and data owners
- retention and PDPA policy
- domains, certificates, DNS, outbound email, and production secrets
- production approval and change window

Until decided, implement adapters, schemas, validation, examples, and test doubles without fabricating credentials or claiming production readiness.

## 17. Research baseline

This SSOT is informed by:

- Odoo 19 official documentation for applications, installation, source deployment, maintenance, and development.
- The Odoo architecture where apps are modules containing models, views, data, controllers, and static assets.
- Cybernetics Plus's Odoo ERP positioning: integrated applications, process automation, centralized visibility, customization, implementation consulting, and ongoing support.

External marketing claims are context, not acceptance evidence. Odoo official documentation, the selected source version, repository code, automated tests, signed architectural decisions, and business-owner acceptance are the implementation authorities.
