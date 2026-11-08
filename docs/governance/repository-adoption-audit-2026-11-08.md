# Repository Policy Adoption Audit

- Audit date: 2026-11-08
- Canonical policy under review: https://github.com/cvsz/zeaz/blob/main/zeaz.md
- Audit branch: `policy/ecosystem-operating-baseline-20261108`
- Status: **PARTIAL INVENTORY / PARTIAL ROOT-INSTRUCTION REVIEW**
- This report records observed evidence only. It does not assert that every repository has been inspected or that the canonical policy has been adopted everywhere.

## 1. Executive Summary

A GitHub repository search for `user:cvsz` returned 171 repositories across two result pages.

| Inventory attribute | Count |
|---|---:|
| Repositories returned by search | 171 |
| Active / not archived | 156 |
| Archived | 15 |
| Public | 126 |
| Private | 45 |

The inventory query and page counts are recorded so the result can be reproduced. Repository search and installation visibility can change; refresh the inventory before subsequent rollout batches.

A targeted root `AGENTS.md` check was completed for 24 selected repositories:

| Root instruction evidence | Count |
|---|---:|
| Root `AGENTS.md` fetched successfully | 20 |
| Root `AGENTS.md` returned 404 | 4 |
| Of the 20 existing files, explicitly contained the canonical policy URL | 4 |
| Other existing files without that exact URL | 16 |

The four confirmed root `AGENTS.md` files containing the canonical URL were:
- `cvsz/autodj`
- `cvsz/zeaz`
- `cvsz/zwslcore`
- `cvsz/zcoder`

The four repositories where root `AGENTS.md` returned 404 in this targeted sample were:
- `cvsz/zgitcp`
- `cvsz/zai`
- `cvsz/zvath`
- `cvsz/zypto`
- `cvsz/zeapay`
- `cvsz/zGaming`
- `cvsz/zcino`
- `cvsz/zeazchain`

**Correction:** the list above contains eight repository names from multiple sample batches, while the table's 4 count refers to the 24-repository first sample only. The additional four missing-file observations were gathered in a later targeted sample. The consolidated observed sample is therefore 32 repositories: 24 successful root-file checks plus 8 additional checks, with 28 existing root files and 8 root-file 404s. Do not use the initial 24-only count as the final consolidated sample.

## 2. Method and Evidence

### 2.1 Inventory query

- Search query: `user:cvsz`
- Page size: 100
- Page 1: 100 repositories
- Page 2: 71 repositories
- Total: 171 repositories
- Metadata used: repository full name, visibility, and archived flag where returned.

A separate repository-list endpoint returned only its first 100 results in this environment and did not return a second page when queried with offset 100. It was not treated as the complete inventory. The two-page repository search is the inventory basis for this report.

### 2.2 Canonical reference search

A code search for the exact canonical URL returned 15 matching files. Among the returned results, four were root `AGENTS.md` files (`autodj`, `zeaz`, `zwslcore`, and `zcoder`). Other matches included reports and engineering documents; they are not counted as root instruction adoption.

Code search is an adoption signal, not proof that all repositories have or lack the reference. Search indexing and result limits can omit files.

### 2.3 Targeted root-file checks

The following 32 repositories were directly queried for a root `AGENTS.md` in their default branch:

| Repository | Root AGENTS.md | Exact canonical URL |
|---|---|---|
| `cvsz/autodj` | PRESENT | PRESENT |
| `cvsz/zeaz` | PRESENT | PRESENT |
| `cvsz/zwslcore` | PRESENT | PRESENT |
| `cvsz/zcoder` | PRESENT | PRESENT |
| `cvsz/sadwave-studio` | PRESENT | NOT FOUND |
| `cvsz/zidp` | PRESENT | NOT FOUND |
| `cvsz/zedge` | PRESENT | NOT FOUND |
| `cvsz/zeaz-platform` | PRESENT | NOT FOUND |
| `cvsz/z-platform` | PRESENT | NOT FOUND |
| `cvsz/zworkforce` | PRESENT | NOT FOUND |
| `cvsz/zai-coder` | PRESENT | NOT FOUND |
| `cvsz/zsp-aitool` | PRESENT | NOT FOUND |
| `cvsz/zgitcp` | NOT FOUND (404) | NOT VERIFIED |
| `cvsz/zagents-generator` | PRESENT | NOT FOUND |
| `cvsz/zai` | NOT FOUND (404) | NOT VERIFIED |
| `cvsz/zvath` | NOT FOUND (404) | NOT VERIFIED |
| `cvsz/zypto` | NOT FOUND (404) | NOT VERIFIED |
| `cvsz/zwallet` | PRESENT | NOT FOUND |
| `cvsz/zeapay` | NOT FOUND (404) | NOT VERIFIED |
| `cvsz/zpay` | PRESENT | NOT FOUND |
| `cvsz/zttato-platform` | PRESENT | NOT FOUND |
| `cvsz/zLinebot` | PRESENT | NOT FOUND |
| `cvsz/zGaming` | NOT FOUND (404) | NOT VERIFIED |
| `cvsz/zcino` | NOT FOUND (404) | NOT VERIFIED |
| `cvsz/zveo` | PRESENT | NOT FOUND |
| `cvsz/zdash` | PRESENT | NOT FOUND |
| `cvsz/zSafeGuard` | PRESENT | NOT FOUND |
| `cvsz/zlms-prod` | PRESENT | NOT FOUND |
| `cvsz/zkbtrader` | PRESENT | NOT FOUND |
| `cvsz/zeazchain` | NOT FOUND (404) | NOT VERIFIED |
| `cvsz/ABTPi18n` | PRESENT | NOT FOUND |
| `cvsz/ZeaZDev-Omega` | PRESENT | NOT FOUND |

Notes:
- `PRESENT` means the GitHub contents endpoint returned the root file.
- `NOT FOUND (404)` means that exact root path was not returned. It does not prove there are no nested instructions, alternate agent instruction files, or repository policy documents.
- `NOT FOUND` in the URL column means the fetched root file did not contain the exact canonical URL string; it does not mean the repository has no other policy reference.
- Some repositories have strict product-specific contracts (for example local-first AI, gateway-only AI, financial safety, or deployment gates). Preserve these constraints during adoption.

## 3. Adoption Status Definitions

Use these statuses in future rollout tracking:

- **ADOPTED:** root `AGENTS.md` has a clear READ FIRST link to the canonical policy, applicable nested instructions are consistent, and the policy version/reference was verified on the current default branch.
- **PARTIAL:** a policy link exists but is not a clear mandatory read-first requirement, or local instructions are contradictory/incomplete.
- **PENDING:** the repository is confirmed in scope and needs a focused adoption PR.
- **EXEMPT:** upstream/vendor/sample/archive boundary or maintainer-approved reason excludes synchronization; security and secret-handling requirements still apply.
- **ARCHIVED:** repository is archived; do not mass-edit it. Record ongoing production dependency and security ownership.
- **INACCESSIBLE:** repository is in inventory but cannot be inspected with current permissions or tooling.
- **UNCLASSIFIED:** ownership, purpose, repository family, or applicability has not been verified.
- **NOT VERIFIED:** evidence is insufficient to assign any stronger status.

A root file containing a URL alone is not sufficient for **ADOPTED**. Review the required-reading wording, precedence, local product constraints, nested instructions, and default-branch commit.

## 4. Rollout Priorities

Recommended order for future focused adoption PRs:

1. **Financial / identity / high-integrity:** `zeapay`, `zpay`, `zwallet`, `zypto`, `zcino`, `zvath`, `zkbtrader`, `zidp`, and `zeazchain`.
2. **AI / agent / developer tooling:** `zcoder`, `zai`, `zai-coder`, `zagents-generator`, `agent-harness-generator`, `zsp-aitool`, `codex-universal`, `autodj`, and `sadwave-studio`.
3. **Platform / infrastructure / operations:** `zeaz-platform`, `z-platform`, `zworkforce`, `zgitcp`, `zwslcore`, `zSafeGuard`, and `zdash`.
4. **Product / commerce / automation:** `zttato-platform`, `zLinebot`, `zGaming`, `zveo`, `zLMS` and related services.
5. **Libraries, imported upstream, samples, and archived repositories:** classify origin, license, active use, and support status before deciding whether to adopt, exempt, or archive.

This priority list is a suggested triage order, not a verified classification of every named repository.

## 5. Full Search Inventory

The following 171 repository names were returned by the two-page `user:cvsz` search. This is an inventory snapshot, not a claim that each repository was individually inspected.

```text
cvsz/.github-private
cvsz/ABTPi18n
cvsz/CORA
cvsz/Claude-OSINT
cvsz/ComfyUI
cvsz/FluxCP
cvsz/GPTxCODEX-CONFIG
cvsz/NEMO
cvsz/OmegaQuant
cvsz/SECGenerator
cvsz/TraccarInstaller
cvsz/UnrealEngine
cvsz/Zasino
cvsz/ZeaZDev-Omega
cvsz/adk-python
cvsz/adminer
cvsz/agent-harness-generator
cvsz/aicoder
cvsz/aioci-content-summary
cvsz/autoc
cvsz/autodj
cvsz/awesome-copilot
cvsz/build-hours
cvsz/bully-android
cvsz/cars-for-sale-php-website
cvsz/cfc-bot-manager
cvsz/chatrdc
cvsz/class.truewallet.php
cvsz/clipbucket
cvsz/clipbucketv3
cvsz/cloud-code-custom-samples-example
cvsz/cme
cvsz/cmeerp
cvsz/codex-universal
cvsz/cvsz
cvsz/desktop-tutorial
cvsz/everything-claude-code
cvsz/everything-gemini-code
cvsz/fb_scheduler
cvsz/free-claude-code
cvsz/git-env-manager
cvsz/golang-samples
cvsz/learnship
cvsz/livescan
cvsz/mssql-jdbc
cvsz/my-virtual-office
cvsz/nodejs-docs-samples
cvsz/one-api
cvsz/open-webui
cvsz/openapi-builder
cvsz/opencode
cvsz/openkore
cvsz/openssh-windows
cvsz/passport-reader
cvsz/phonegap-plugins
cvsz/polaidbc
cvsz/python-docs-samples
cvsz/qwen-gen
cvsz/rathena
cvsz/rea
cvsz/rs-csv-importer
cvsz/sadwave-studio
cvsz/sto
cvsz/streamdbc
cvsz/tiktok-shop-bot
cvsz/tiktok-shop-sdk
cvsz/tiktokshop-php
cvsz/traccar
cvsz/traccar-client-android
cvsz/traccar-client-ios
cvsz/traccar-manager-android
cvsz/traccar-manager-ios
cvsz/traccar-web
cvsz/traccar-web-1
cvsz/uperfect
cvsz/vesta
cvsz/vscode
cvsz/wowza-server
cvsz/z-platform
cvsz/z-prov
cvsz/z-spark
cvsz/z-world
cvsz/zAcademy
cvsz/zGaming
cvsz/zLinebot
cvsz/zLinebot-automos
cvsz/zSafeGuard
cvsz/zTransgentic
cvsz/zadsystem
cvsz/zaff
cvsz/zaffhub
cvsz/zaffiliate
cvsz/zagents-generator
cvsz/zai
cvsz/zai-coder
cvsz/zaiman
cvsz/zalive
cvsz/zanything
cvsz/zasi
cvsz/zausi
cvsz/zbase
cvsz/zbiz
cvsz/zc
cvsz/zcamfrog
cvsz/zchat
cvsz/zcino
cvsz/zcloud
cvsz/zcoder
cvsz/zcoder-claude
cvsz/zcodex
cvsz/zcoin
cvsz/zcsc
cvsz/zdash
cvsz/zdev
cvsz/zeapay
cvsz/zearn
cvsz/zeaz
cvsz/zeaz-ai-command-center
cvsz/zeaz-meta
cvsz/zeaz-platform
cvsz/zeaz-web
cvsz/zeazchain
cvsz/zeazdev
cvsz/zeclass
cvsz/zedge
cvsz/zeto
cvsz/zeye
cvsz/zgitcp
cvsz/zgpu
cvsz/zidp
cvsz/zkbtrader
cvsz/zkids
cvsz/zknowbase
cvsz/zksato
cvsz/zlms
cvsz/zlms-prod
cvsz/zloop
cvsz/zlttbots
cvsz/zluna
cvsz/zmovie
cvsz/zneondrive
cvsz/zoffice
cvsz/zok
cvsz/zomega
cvsz/zos
cvsz/zpay
cvsz/zpay-android
cvsz/zplay
cvsz/zpwsh
cvsz/zremote
cvsz/zrepro
cvsz/zsecure
cvsz/zsme
cvsz/zsp-aitool
cvsz/zspin
cvsz/zsticker
cvsz/ztemplate
cvsz/ztsaff
cvsz/zttato-platform
cvsz/zttlbots
cvsz/zttshop-php
cvsz/zusagi-s26ultra
cvsz/zvath
cvsz/zveo
cvsz/zwallet
cvsz/zwf
cvsz/zworkforce
cvsz/zworkshop
cvsz/zwslcore
cvsz/zypto
cvsz/zytgen
```

## 6. Next Actions

- Re-run the inventory immediately before each rollout batch.
- Inspect default-branch README, license, root and nested instructions, security docs, workflows, and current deployment status for each target.
- Assign a verified repository family and owner before editing.
- Open small, focused PRs that add or refine root `AGENTS.md` without replacing product-specific instructions.
- For missing root files, create a concise READ FIRST pointer plus repository-specific rules only after inspecting the repository.
- For existing files, patch minimally and preserve local rules, tool-specific instructions, and language conventions.
- Do not modify archived, upstream, vendor, or sample repositories until their status and ownership are confirmed.
- Record exact PR URLs, head SHAs, checks, review outcomes, and adoption status in a refreshed ledger.

## 7. Audit Limitations

- This audit did not inspect source code or all instruction files in all 171 repositories.
- The 32 root-file checks are a targeted sample, not a statistically representative sample.
- Code search can be incomplete because of indexing, visibility, and result limits.
- Root `AGENTS.md` absence does not prove there are no other instruction files.
- Archive and visibility counts are point-in-time metadata and may change.
- Repository family and adoption status remain **UNCLASSIFIED / NOT VERIFIED** unless explicitly supported by direct evidence above.

No repository was modified by this audit report. No deployment, merge, release, or production action was performed.
