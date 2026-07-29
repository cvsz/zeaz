# ZERP — Codex Mega Max Prompts

> Target: `apps/zerp`
> Authority order: repository `AGENTS.md` → `apps/zerp/AGENTS.md` → `CODEX-MAX-SINGLE-SOURCE-OF-TRUTH.md` → this file
> Operating mode: evidence-driven, one complete vertical slice per pull request

This file contains executable prompts for Codex agents to discover and eliminate incomplete, broken, invalid, missing, unsafe, obsolete, or incorrectly integrated functionality in `apps/zerp`.

The prompts are intentionally strict. They must not be used to generate broad speculative rewrites, fake implementations, placeholder modules, or unverified claims of completion.

---

## 1. Mega Max master prompt

Copy the complete prompt below into Codex from the repository root.

```text
You are the principal implementation, architecture, release, security, and quality agent for ZERP in this repository.

PRIMARY TARGET
- Work only on `apps/zerp` and directly related repository-level files required to build, test, package, deploy, document, or validate it.
- Treat `apps/zerp/CODEX-MAX-SINGLE-SOURCE-OF-TRUTH.md` as the authoritative product and implementation contract.
- Read every applicable `AGENTS.md` before planning or editing.

MISSION
Continuously inspect, validate, repair, complete, and harden ZERP until every required capability is implemented or explicitly classified as deferred with a documented reason, owner, dependency, risk, and acceptance condition.

You must actively find and resolve:
- incomplete features;
- hidden TODO/FIXME/pass/not-implemented branches;
- broken or invalid source code;
- wrong source code copied from incompatible Odoo versions;
- deprecated or unsupported Odoo APIs;
- malformed module manifests;
- wrong module dependency declarations;
- missing Python, XML, CSV, JS, SCSS, translation, security, data, migration, test, documentation, deployment, or packaging files;
- missing imports and unreachable modules;
- invalid model inheritance;
- broken field definitions, constraints, computed fields, inverse methods, onchange handlers, domains, contexts, record rules, access controls, views, actions, menus, reports, controllers, RPC endpoints, cron jobs, hooks, assets, and QWeb/Owl components;
- SDK/API mismatches;
- stale generated clients or schemas;
- installer, bootstrap, configure, upgrade, backup, restore, migration, health-check, and release defects;
- invalid environment variables and configuration;
- missing config schema validation;
- Docker, Compose, systemd, Caddy, Kubernetes, Terraform, CI, and release gaps;
- build failures;
- dependency conflicts;
- missing locks or unpinned dependencies;
- unsafe secrets, credentials, permissions, logging, uploads, webhooks, payments, or external integrations;
- incorrect Thai localization, VAT, withholding-tax, branch/head-office, address, tax-ID, date, timezone, currency, document-numbering, and report behavior;
- missing tests, weak tests, skipped tests, non-deterministic tests, and false-positive validation;
- documentation that disagrees with executable behavior;
- features claimed as complete without evidence.

NON-NEGOTIABLE RULES
1. Revalidate the current repository and current branch before every edit. Never rely on a prior run's assumptions.
2. Never patch Odoo upstream core when a supported extension point can satisfy the requirement.
3. Never copy Enterprise code or emulate licensed Enterprise behavior unlawfully.
4. Never create fake integrations, placeholder UIs, no-op adapters, silently skipped tests, or TODO-only implementations.
5. Implement exactly one complete vertical slice per pull request.
6. Do not leave a partial slice. If the selected slice cannot be completed safely, stop before editing and record the blocker.
7. Preserve backward compatibility unless the SSOT explicitly authorizes a migration.
8. Every external side effect must be authenticated, authorized, idempotent, observable, retry-safe, and reconcilable.
9. Browser code must never receive provider secrets, database credentials, Odoo master passwords, admin keys, signing secrets, or unrestricted service tokens.
10. Every claim must be supported by repository evidence and validation output.
11. Do not mark the project complete while any P0/P1 defect, required missing file, failed gate, unresolved security defect, or undocumented installation step remains.
12. Do not suppress, weaken, delete, or skip a failing test merely to obtain a green build.

PHASE A — REPOSITORY RECONNAISSANCE
Before changing files:
1. Print the current branch, HEAD SHA, working-tree status, remotes, and recent commits.
2. Read:
   - repository root `AGENTS.md`;
   - every nested `AGENTS.md` applicable to `apps/zerp`;
   - `apps/zerp/CODEX-MAX-SINGLE-SOURCE-OF-TRUTH.md`;
   - `apps/zerp/README.md`, changelog, architecture, installation, configuration, testing, security, operations, release, migration, module matrix, and execution records when present.
3. Inventory every path under `apps/zerp`, including dotfiles and symlinks.
4. Identify the actual Odoo version, Python version, Node version, package managers, database version, container/runtime strategy, and module/add-ons paths from executable configuration rather than assumptions.
5. Identify all custom modules and for each module inspect:
   - `__manifest__.py`;
   - `__init__.py` files;
   - models;
   - controllers;
   - wizards;
   - security access CSV and record rules;
   - data/demo XML;
   - views, actions, menus, reports, templates, assets, translations;
   - hooks and migrations;
   - tests;
   - external dependencies;
   - installability and upgrade behavior.
6. Identify every installer, configuration, deployment, backup, restore, health-check, CI, packaging, release, and migration entry point.
7. Identify every integration boundary, SDK, API client, webhook, authentication method, payment provider, AI provider, object-storage provider, email/SMS provider, and accounting/banking exchange.

PHASE B — EVIDENCE-BASED GAP AUDIT
Create or update these authoritative artifacts before implementation:
- `apps/zerp/docs/MODULE-MATRIX.md`;
- `apps/zerp/docs/FEATURE-MATRIX.md`;
- `apps/zerp/docs/VALIDATION-REPORT.md`;
- `apps/zerp/docs/execution-records/<UTC-DATE>-repository-audit.md`;
- `apps/zerp/.codex/audit.json` when machine-readable state is permitted by repository policy.

For every discovered item record:
- stable ID;
- category;
- path/module/component;
- requirement source;
- observed evidence;
- expected behavior;
- actual behavior;
- severity: P0, P1, P2, or P3;
- confidence;
- affected editions/profiles;
- dependencies;
- security, data, financial, legal, operational, and upgrade impact;
- reproducible validation command;
- proposed vertical slice;
- status: missing, broken, invalid, incomplete, unsafe, obsolete, blocked, deferred, or complete;
- completion evidence.

Severity definitions:
- P0: data loss/corruption, authentication or authorization bypass, secret exposure, financial posting corruption, unrecoverable installation/upgrade, production outage, or legal/licensing violation.
- P1: required feature unusable, module cannot install/upgrade, broken installer/build/release, major localization/accounting defect, severe integration failure, or no valid backup/restore path.
- P2: partial behavior, missing component, compatibility defect, weak validation, missing observability, or significant UX/operational problem.
- P3: documentation, maintainability, optimization, minor UX, or non-blocking quality gap.

Audit all of the following categories explicitly:

SOURCE AND MODULE INTEGRITY
- Parse and compile every Python source file.
- Validate imports and module initialization paths.
- Validate manifests, versions, dependencies, data file order, assets, external dependencies, installable/application flags, license declarations, and Odoo-version compatibility.
- Detect orphaned files, unreachable models/controllers, duplicate XML IDs, missing XML IDs, invalid XPath inheritance, invalid field references, invalid domains/contexts, and broken menu/action references.
- Detect direct modifications of vendored/upstream Odoo source.
- Detect unsupported monkey patches and unstable private API usage.
- Detect copied code from wrong Odoo versions.

SECURITY AND ACCESS CONTROL
- Ensure every model has intentional ACL and record-rule behavior.
- Detect permissive ACLs, missing company isolation, sudo misuse, insecure public routes, unsafe CSRF/CORS settings, unvalidated redirects, IDOR, mass assignment, unrestricted file upload, unsafe attachment access, SQL injection, command injection, path traversal, SSRF, template injection, XSS, secret logging, and insecure webhook processing.
- Confirm integrations use dedicated least-privilege identities rather than superuser credentials.

DATA AND BUSINESS INTEGRITY
- Validate company-dependent fields, currencies, units, rounding, sequences, states, constraints, transactions, concurrency, idempotency, posting/reversal rules, stock/valuation consistency, and migration safety.
- Validate all dates and datetimes for timezone semantics.
- Validate authoritative money calculations use Odoo monetary fields and currency rounding.

THAI LOCALIZATION
- Validate Thai language installation and translations.
- Validate THB, company tax IDs, branch/head-office data, Thai addresses, VAT 7%, withholding tax behavior, tax invoices, document numbering, reports, and exports against the documented business contract.
- Mark accountant/legal review requirements explicitly; never claim statutory compliance solely from automated tests.

SDK, API, CONTROLLERS, AND INTEGRATIONS
- Compare implemented APIs against OpenAPI/JSON Schema/SDK contracts where present.
- Detect stale or missing generated clients.
- Validate request/response schemas, pagination, errors, auth, retries, timeouts, signatures, replay protection, idempotency, reconciliation, and observability.
- Verify no provider secret reaches browser bundles or public responses.
- For OpenAI Responses-compatible integrations, reject unsupported fields such as `input[].namespace`; resolve model capabilities before sending optional fields such as `service_tier`; default unsupported aliases such as `codex-auto-review` to capability-safe behavior.

BUILD AND FRONTEND
- Validate package manifests, lockfiles, workspace declarations, TypeScript configuration, lint/typecheck/build commands, assets, Owl/QWeb components, imports, routes, localization, and production bundles.
- Detect missing components, stale generated bundles, broken asset declarations, and UI controls without working server behavior.

INSTALLER AND CONFIGURATION
- Exercise dry-run and non-interactive modes.
- Validate supported OS/architecture detection, prerequisites, add-ons paths, PostgreSQL roles, directories, ownership, permissions, generated secrets, config files, services, reverse proxy, TLS assumptions, database initialization, module profiles, report rendering, and rollback.
- Ensure rerunning installation/configuration is idempotent.
- Validate every environment variable against a documented schema.
- Detect undocumented mandatory manual steps.
- Validate Community and licensed Enterprise paths remain separated.

UPGRADE, MIGRATION, BACKUP, AND RESTORE
- Test clean install, module install, module upgrade, database migration, backup, restore, and post-restore verification.
- Confirm database and filestore/object-storage consistency.
- Confirm rollback/restore procedures are documented and executable.
- Never run destructive migration against production data without an approved backup and explicit operator authorization.

DEPLOYMENT AND OPERATIONS
- Validate development, CI, staging, and production profiles.
- Validate health, readiness, startup, graceful shutdown, logs, metrics, traces where applicable, alerts, cron behavior, worker sizing, proxy headers, websocket/long-polling, resource limits, and restart behavior.
- Validate release artifacts, checksums, SBOM/provenance where required, versioning, changelog, and rollback.

TEST QUALITY
- Run existing tests before edits.
- Detect skipped, expected-failure, flaky, order-dependent, network-dependent, timezone-dependent, and state-leaking tests.
- Require negative authorization tests and multi-company isolation tests.
- Require install and upgrade tests for every custom module.
- Require integration tests to use mocks or approved test endpoints; never consume live production credentials.

PHASE C — SELECT ONE VERTICAL SLICE
Select the highest-value unblocked slice using this priority:
1. P0 security, data, licensing, or recovery defect;
2. P1 install/build/module-upgrade blocker;
3. P1 required business feature gap;
4. P2 cross-cutting correctness or operational gap;
5. P3 quality improvement.

A valid vertical slice must:
- have one coherent user/operator/business outcome;
- be small enough for one reviewable PR;
- include all required source, model, view/UI, API/controller, ACL/record rule, config, migration, tests, docs, observability, and rollback changes;
- leave no partially exposed feature;
- not depend on an unimplemented hidden follow-up to be safe or usable.

Before editing, write the selected slice into the execution record with:
- problem statement;
- evidence;
- scope and explicit non-scope;
- acceptance criteria;
- file plan;
- migration and rollback plan;
- test plan;
- security and data-impact analysis.

PHASE D — IMPLEMENTATION
1. Create a dedicated branch from the latest `main`.
2. Implement the complete slice using supported Odoo extension mechanisms.
3. Preserve existing public contracts unless migration is explicitly approved.
4. Add deterministic tests before or with the implementation.
5. Add migration hooks/scripts when stored data or XML data changes require them.
6. Update configuration examples and schema validation.
7. Update operations, installation, upgrade, backup/restore, and security documentation when behavior changes.
8. Update `CHANGELOG.md`, module matrix, feature matrix, validation report, and execution record.
9. Do not include unrelated formatting or cleanup.

PHASE E — VALIDATION
Discover and run the repository's actual commands. At minimum validate, when applicable:
- working-tree hygiene and `git diff --check`;
- shell syntax and ShellCheck;
- Python compile/import checks;
- formatting and lint;
- static typing where configured;
- manifest and XML validation;
- Odoo module install tests on a clean database;
- Odoo module upgrade tests on a representative previous-state database;
- unit tests;
- integration tests;
- browser/UI tests;
- API/SDK contract tests;
- ACL, record-rule, portal/public-route, and multi-company isolation tests;
- migration tests;
- installer dry-run and idempotency tests;
- backup/restore verification;
- container/deployment config validation;
- dependency, secret, SAST, container, and IaC scans;
- build and package creation;
- health/readiness smoke tests.

Fix every regression introduced by the slice. Do not hide failures.

PHASE F — REVIEW PACKAGE
Before committing:
- inspect the full diff;
- confirm no secrets, databases, filestore data, generated caches, local config, credentials, or Enterprise code were added;
- confirm all acceptance criteria have evidence;
- confirm docs match behavior;
- confirm rollback is viable.

Commit with a conventional, specific message.
Push the branch and open exactly one PR.
The PR must include:
- problem and evidence;
- implemented outcome;
- scope/non-scope;
- architecture and trade-offs;
- security/data/licensing impact;
- migration and rollback;
- exact validation commands and results;
- remaining known gaps linked to the authoritative matrices.

STOP CONDITION
After opening the PR, stop. Do not start another slice until this PR is reviewed, all comments are resolved, required checks pass, and the PR is merged.

NEXT ITERATION
After merge:
- switch to `main`;
- pull/revalidate the repository;
- rerun baseline validation;
- update the audit evidence;
- select the next highest-priority unblocked vertical slice;
- repeat until the final completion gate is satisfied.

FINAL COMPLETION GATE
You may declare ZERP complete only when all of these are true:
- no unresolved P0 or P1 items;
- every required SSOT capability is complete or formally deferred with rationale and approval;
- all custom modules install and upgrade successfully;
- clean installation is reproducible and non-interactive;
- configuration validation fails safely;
- build, lint, typecheck, tests, security scans, installer tests, migration tests, backup/restore tests, deployment validation, and health checks pass;
- Community and Enterprise licensing boundaries are proven;
- Thai localization acceptance is documented and reviewed by qualified business/accounting stakeholders where required;
- production runbooks, recovery procedures, observability, release artifacts, module matrix, feature matrix, changelog, validation report, and execution records are current;
- there are no required missing files, undocumented manual steps, placeholder implementations, silently skipped tests, or unsupported upstream patches.
```

---

## 2. First-run forensic audit prompt

Use this prompt for the first deep inspection before any implementation PR.

```text
Perform a forensic, read-only audit of `apps/zerp`.

Do not edit runtime source during this run.

Required outputs:
1. A complete file and component inventory.
2. A module dependency graph.
3. A business-capability-to-module map.
4. A list of expected files from the SSOT that are missing.
5. A list of existing files that are orphaned, invalid, unreachable, obsolete, duplicated, generated-but-stale, or located in the wrong layer.
6. A list of source/API/SDK/Odoo-version mismatches.
7. A build, install, configure, upgrade, backup, restore, deployment, and test command matrix.
8. A defect ledger ranked P0–P3 with reproducible evidence.
9. A proposed sequence of complete vertical slices.
10. One recommended first slice, but do not implement it.

Inspect at least:
- all manifests and module init chains;
- all Python, XML, CSV, JS, TS, SCSS, QWeb/Owl, translation, migration, configuration, shell, container, CI, and documentation files;
- module installability and dependency availability;
- ACLs, record rules, controllers, public/portal routes, cron jobs, hooks, and integrations;
- Odoo version compatibility;
- Thai localization requirements;
- installer/configuration idempotency;
- clean install and upgrade feasibility;
- test coverage and skip behavior;
- secret and licensing boundaries.

Write evidence into the authoritative ZERP audit documents. Do not mark anything complete without a command, test, or directly inspectable artifact proving it.
```

---

## 3. Missing-file and missing-component prompt

```text
Compare the actual `apps/zerp` tree with the target structure and acceptance requirements in `CODEX-MAX-SINGLE-SOURCE-OF-TRUTH.md`.

Find every missing required file, directory, module, component, manifest entry, import, security declaration, view, action, menu, report, translation, migration, test, config example, schema, installer step, deployment asset, runbook, or release artifact.

For each missing item:
- prove why it is required;
- identify the dependent feature or quality gate;
- classify severity;
- state whether it should be created, replaced by an existing equivalent, or formally deferred;
- identify the smallest complete vertical slice that can supply it safely.

Do not create empty skeleton files. Any file created in an implementation slice must contain functional, validated behavior or executable documentation required by that slice.
```

---

## 4. Wrong-source and Odoo compatibility prompt

```text
Audit all ZERP source for incompatibility with the repository's declared Odoo version.

Detect:
- code copied from older/newer Odoo versions;
- renamed or removed models, fields, methods, hooks, registries, asset bundles, JS modules, Owl APIs, controller APIs, ORM decorators, and manifest keys;
- private upstream APIs used without justification;
- invalid inheritance and XPath targets;
- upstream core modifications;
- Community/Enterprise mixing or licensing violations;
- dependency declarations that do not match imported models or XML references.

Verify findings against the pinned upstream source or official version-specific documentation available to the repository.

Produce reproducible failures or static evidence. Then propose one complete compatibility vertical slice at a time. Never perform a bulk speculative rewrite.
```

---

## 5. Installer and configuration prompt

```text
Treat installation and configuration as a production feature.

Audit and complete the ZERP installer/configuration workflow so that a supported clean host can reach a verified healthy system without undocumented manual steps.

Validate:
- OS and architecture support;
- CPU/RAM/storage/DNS/time/ports prerequisites;
- pinned dependencies;
- Odoo Community source/image acquisition;
- optional licensed Enterprise acquisition and add-ons precedence;
- PostgreSQL role/database provisioning;
- system user and file permissions;
- config generation and schema validation;
- secret generation and external secret injection;
- filestore/object storage;
- reverse proxy and TLS assumptions;
- worker/cron/long-polling configuration;
- module profile installation;
- Thai localization and translations;
- report rendering;
- systemd/Compose/container startup;
- health/readiness checks;
- installation report redaction;
- rerun idempotency;
- dry-run;
- non-interactive mode;
- rollback and cleanup after failure.

Add automated clean-install and second-run idempotency tests. Do not claim completion from shell syntax checks alone.
```

---

## 6. Feature-completeness prompt

```text
Select one required business capability from the authoritative feature matrix that is missing, broken, or incomplete.

Trace it end to end:
- business requirement;
- installed upstream/custom module;
- data model;
- state machine;
- constraints;
- access control and multi-company behavior;
- user interface;
- API/controller/portal behavior;
- reports/documents;
- localization;
- integrations and side effects;
- auditability and observability;
- migrations;
- tests;
- installation and upgrade behavior;
- documentation and rollback.

Implement the smallest complete user-visible or operator-visible outcome. Do not expose menus, actions, endpoints, or settings for unfinished behavior.
```

---

## 7. Build, SDK, API, and frontend prompt

```text
Audit the complete ZERP build and contract pipeline.

Find and fix:
- invalid package/workspace manifests;
- missing or stale lockfiles;
- incompatible Node/TypeScript/Owl versions;
- missing imports and components;
- stale generated SDKs;
- OpenAPI/JSON Schema drift;
- request/response type mismatches;
- routes documented but not implemented;
- implementations not documented;
- broken production asset bundles;
- invalid Odoo asset declarations;
- QWeb/Owl rendering failures;
- browser-secret exposure;
- UI controls with no working backend;
- build output not packaged or deployed;
- cache-busting and upgrade problems.

For Responses-compatible AI adapters:
- never send `namespace` inside `input[]`;
- resolve model alias capabilities before optional request fields;
- omit or downgrade unsupported `service_tier` values safely;
- test streaming and non-streaming error paths;
- keep provider credentials server-side.

Add contract tests proving the server, schemas, generated client, and UI agree.
```

---

## 8. Security, data, and Thai accounting prompt

```text
Perform a threat-driven audit of one ZERP business vertical slice.

Prove:
- least-privilege ACL and record rules;
- company isolation;
- safe portal/public behavior;
- no sudo-based authorization bypass;
- CSRF/CORS/session/upload/webhook safety;
- secret and personal-data redaction;
- transactional integrity;
- concurrency safety;
- idempotency and reconciliation;
- correct monetary and quantity rounding;
- supported posting/reversal behavior;
- audit trail;
- backup/restore implications;
- Thai tax/localization behavior required by the slice.

Add negative tests. For accounting and tax behavior, distinguish technical correctness from statutory approval and record required accountant/legal review.
```

---

## 9. PR review and regression prompt

```text
Review the current ZERP pull request as an adversarial principal engineer.

Read the SSOT, execution record, issue/PR description, full diff, test changes, and CI output.

Find:
- incomplete slice boundaries;
- missing files/components/tests/docs/migrations;
- invalid Odoo APIs;
- backward incompatibility;
- security and company-isolation regressions;
- data migration hazards;
- installer/configuration regressions;
- build/SDK/schema drift;
- hidden licensing violations;
- claims unsupported by evidence;
- tests that pass without exercising the new behavior;
- unrelated changes.

Do not approve until every acceptance criterion has direct evidence, every required check passes, and rollback is credible.
```

---

## 10. Human-supervised execution loop

Run one Codex iteration at a time. Review and merge each PR before starting the next.

```bash
#!/usr/bin/env bash
set -Eeuo pipefail

REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel)}"
PROMPT_FILE="$REPO_ROOT/apps/zerp/CODEX-MEGA-MAX-PROMPTS.md"
SSOT_FILE="$REPO_ROOT/apps/zerp/CODEX-MAX-SINGLE-SOURCE-OF-TRUTH.md"

cd "$REPO_ROOT"

while true; do
  git switch main
  git pull --ff-only
  git status --short

  test -f "$PROMPT_FILE"
  test -f "$SSOT_FILE"

  codex exec "$(cat <<EOF
Read and execute the Mega Max master prompt in:
$PROMPT_FILE

The authoritative product contract is:
$SSOT_FILE

Revalidate the repository, select and implement exactly one complete highest-priority unblocked vertical slice, validate it fully, commit it, push a branch, and open one pull request. Stop immediately after opening the PR.
EOF
)"

  printf '\nReview the newly opened PR and wait for all required checks.\n'
  read -r -p 'Has the PR been reviewed and merged into main? [y/N] ' answer
  case "$answer" in
    y|Y|yes|YES) ;;
    *) echo 'Stopping until the PR is merged.'; exit 0 ;;
  esac
done
```

This loop is intentionally supervised. It prevents agents from stacking multiple dependent PRs, hiding regressions, or continuing from stale repository state.

---

## 11. Completion report prompt

```text
Assess whether ZERP satisfies the final completion gate in the SSOT and Mega Max prompt.

Do not implement changes during this assessment.

For every completion criterion provide:
- PASS, FAIL, BLOCKED, or DEFERRED;
- exact evidence path;
- exact validation command and latest result;
- responsible module/profile;
- unresolved risk;
- required next vertical slice.

A green CI status alone is insufficient.

Return NOT COMPLETE when any required file, required feature, P0/P1 defect, installation step, upgrade test, backup/restore verification, security control, localization acceptance, release artifact, runbook, or evidence record is absent or stale.
```
