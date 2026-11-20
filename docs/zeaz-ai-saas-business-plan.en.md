# ZEAZ AI + SaaS Commercial Plan

> Status: Proposed strategy and execution baseline; not a forecast, funding commitment, product availability claim, or production-readiness attestation.
> Owner: ZEAZ business owner
> Planning horizon: 12 months from approval
> Revenue objective: USD 60,000 gross collected revenue
> Initial capital: USD 0 incremental cash investment, conditional on using already-owned infrastructure and free tiers
> Markets: Thailand first, then international SMBs

## 1. Executive decision

Build a service-led, productized AI automation business around one repeatable customer problem. Use paid discovery, implementation and bounded pilots to validate demand and finance productization. Convert repeated workflows into subscription features only after customers demonstrate willingness to pay.

The first commercial wedge is **AI-assisted commerce operations for small online sellers**: product knowledge, customer inquiry triage, sales assistance, lead/order handoff and operational reporting. Thailand is the initial validation market; international SMB expansion follows evidence of repeatable onboarding, support and unit economics.

The USD 60,000 objective is an aggressive stretch target, not an earnings guarantee. Measure cash actually collected, net of refunds and chargebacks, and report taxes and operating expenses separately. Gross revenue is not profit.

### Strategic rules

1. Sell a measurable outcome before building a broad platform.
2. Start with one customer segment and one repeatable workflow.
3. Treat demos and simulations as demos; never describe simulated channel activity as a live integration.
4. Keep customer data, tenant boundaries, credentials, billing and audit trails server-side.
5. Preserve existing MooPiew, zERP and repository source-of-truth boundaries.
6. Spend only after a validated customer need and an approved cash-flow path.
7. Do not launch a paid production service until reliability, privacy, security, support and legal prerequisites are met.

## 2. Repository baseline and product truth

This repository currently contains distinct assets with different maturity levels:

| Asset | Verified role in the repository | Commercial treatment |
| --- | --- | --- |
| ZEAZ AI Live Catalog / Qwen chat | Existing AI catalog and chat integration with owner-only provider configuration | Internal capability and controlled demonstration; not a metered multi-tenant AI API |
| zTTShop ERP + AI Sales demo | Frontend simulation with seeded conversations, simulated orders/stock and simulated channel sync | Sales demo and discovery aid only |
| zERP | Protected, read-only operations workspace backed by MooPiew APIs | Internal operations product slice; not a general multi-tenant ERP |
| MooPiew service | Existing restaurant commerce/delivery application and operational data source | Keep isolated; do not repurpose its database as a SaaS tenant store |

The zTTShop demo explicitly does not call real Facebook, Shopee, payment or production order APIs. zERP documentation explicitly defers larger ERP capabilities until backend models, authorization, migrations and tests exist. No multi-tenant customer SaaS control plane, subscription entitlement service, customer billing lifecycle or production channel connector is established by these assets alone.

These facts are release boundaries. Marketing, proposals, demos and contracts must describe current capabilities accurately.

## 3. Target customer and initial offer

### Initial segment: Thai online sellers

Target owner-operated and small teams selling through social commerce and marketplaces who have repeatable product questions, inconsistent response times and manual order handoff. Prefer one product category with stable product facts and low regulatory risk. Do not begin with medical, financial, legal or other high-impact advice workflows.

### Follow-on segment: international SMBs

After the Thai pilot is repeatable, test English-speaking small ecommerce and service businesses with similar support and lead-qualification workflows. Do not localize every feature or add multiple channel integrations before paid demand exists.

### Initial paid offer: AI Commerce Assistant

A bounded implementation that can include:
- approved product/FAQ knowledge base;
- customer inquiry classification and suggested replies;
- human handoff and escalation;
- lead capture and order-intent handoff to an existing approved system;
- response-quality review and usage reporting.

Initial delivery may use a human-supervised workflow and existing tools. It must not claim autonomous order placement, inventory mutation, payment confirmation or live marketplace synchronization unless each path is implemented, authorized, tested and verified.

### Product sequence

1. **Phase A — Productized service:** configure one workflow for one customer; charge a setup fee and a time-bounded pilot fee.
2. **Phase B — Repeatable SaaS core:** only after at least three paid customers share the same requirements, build tenant workspaces, authentication, knowledge-base management, workflow configuration, usage metering and support tooling.
3. **Phase C — Integrations:** add one channel at a time after official API eligibility, partner terms, webhook security, idempotency, privacy and operational support are verified.
4. **Phase D — Analytics and workflow expansion:** add reporting and adjacent automation only when retention and paid usage justify it.

Do not create three separate products at launch. AI support, workflow automation and analytics are capabilities within one initial offer until demand supports separate packaging.

## 4. Pricing hypotheses

Validate willingness to pay through interviews and paid pilots. These are test prices, not market research findings or public commitments.

| Offer | Thailand test price | International test price |
| --- | ---: | ---: |
| Starter subscription | THB 990/month | USD 29/month |
| Business subscription | THB 2,990/month | USD 79/month |
| Pro subscription | THB 5,990/month | USD 149/month |
| Implementation | THB 5,000–15,000 | USD 300–750 |
| Custom integration | Individually scoped | Individually scoped |

Pricing must define included seats, channels, knowledge sources, monthly conversations/tokens, retention, support hours, overage rates and exclusions. No unlimited AI usage. Bill in a clearly stated currency; disclose conversion, tax and payment fees before checkout. Do not promise fixed THB/USD equivalence.

## 5. USD 60,000 revenue model

### Target composition

| Revenue stream | 12-month target | Recognition basis |
| --- | ---: | --- |
| SaaS subscriptions | USD 40,000 | Subscription cash collected for the service period |
| Implementation and onboarding | USD 15,000 | Completed, accepted and collected setup work |
| Premium integrations / managed workflows | USD 5,000 | Accepted scoped work or recurring add-on collected |
| **Total** | **USD 60,000** | Gross collected revenue before operating costs and taxes |

Avoid double-counting implementation bundled into subscriptions. Track invoices, collections, refunds, chargebacks, taxes, fees, deferred service periods and currency conversion separately.

### Monthly collection targets

The following are monthly gross collection targets in USD, not MRR targets or forecasts. The sum is exactly USD 60,000.

| Month | Monthly target | Cumulative target | Primary evidence expected |
| --- | ---: | ---: | --- |
| 1 | 0 | 0 | Interviews, validated pain and a priced offer |
| 2 | 500 | 500 | First paid discovery or pilot |
| 3 | 1,500 | 2,000 | First accepted implementation |
| 4 | 2,500 | 4,500 | Repeatable pilot delivery |
| 5 | 3,500 | 8,000 | First subscription conversions |
| 6 | 4,500 | 12,500 | Retention and unit-cost evidence |
| 7 | 5,500 | 18,000 | Repeatable acquisition channel |
| 8 | 6,500 | 24,500 | More standardized onboarding |
| 9 | 7,500 | 32,000 | Controlled international validation |
| 10 | 8,500 | 40,500 | Expansion revenue from retained accounts |
| 11 | 9,500 | 50,000 | Predictable renewals and referrals |
| 12 | 10,000 | 60,000 | Sustainable delivery capacity |

This is a stretch ramp. If paid demand, conversion or delivery capacity misses the gate for two consecutive months, revise the target, scope or offer rather than manufacturing revenue assumptions.

### Unit economics gates

Track by tenant and plan:
- collected revenue and refunds;
- payment fees and taxes;
- model/provider cost and tokens;
- infrastructure, storage, email and observability cost;
- human onboarding and support hours;
- gross margin and contribution margin;
- acquisition cost and payback period;
- activation, weekly active use, renewal and churn.

Do not scale paid acquisition until contribution margin is positive and customer acquisition payback is supported by observed cohorts. A proposed mature gross-margin goal is at least 65%; it is a gate to validate, not a current result.

## 6. Customer acquisition and sales

### Channels

1. Founder-led, personalized outreach to businesses with a visible workflow problem.
2. Demonstrations using synthetic data and clearly labelled demo environments.
3. Educational content showing before/after workflow outcomes, not unsupported AI claims.
4. Partnerships with local web agencies, ecommerce implementers and consultants.
5. Customer referrals after measurable value has been delivered.
6. Search content targeting narrow operational questions in Thai and English.

Respect platform terms, privacy and anti-spam requirements. Do not scrape private data, automate unsolicited bulk messaging or misrepresent customer endorsements.

### Monthly activity hypotheses

- 20 qualified business conversations;
- 5 workflow demonstrations;
- 2 scoped pilot proposals;
- 1–2 paid pilot wins, subject to observed conversion;
- weekly review of loss reasons and onboarding effort.

These are activity targets, not promised conversion rates. Track each lead from source through qualification, proposal, payment, activation and renewal.

### Sales process

1. Qualify business type, workflow volume, current tools, decision-maker, data sensitivity and budget.
2. Quantify the current cost or delay using customer-provided evidence.
3. Demonstrate only the workflow that addresses the stated pain.
4. Agree scope, success metric, data processing terms, exclusions and pilot end date.
5. Collect approved payment through an eligible account before incurring customer-specific costs.
6. Onboard with synthetic data first, then customer-authorized minimum data.
7. Review outcomes and convert to subscription only if recurring value exists.

## 7. Target architecture and repository boundaries

The SaaS control plane is a proposed future system. Do not bolt it into the MooPiew app.py runtime or reuse the restaurant SQLite database for unrelated tenants.

### Logical architecture

    Customer web app / Admin console
                  |
             Edge / WAF
                  |
          SaaS API / BFF
                  |
       Identity + Tenant authorization
                  |
      Subscription + Entitlements + Metering
                  |
        Workflow / Job orchestration
            |              |
      AI provider       Connectors
      adapter           (one at a time)
            |              |
            +------+-------+
                   |
      Tenant-scoped data and audit store
                   |
      Metrics / Logs / Alerts / Backups

### Required controls before real customer data

- Tenant identity derived from authenticated server-side context, never trusted from a client-supplied tenant ID.
- Database-level tenant isolation, authorization tests and cross-tenant negative tests.
- Server-side subscription entitlements and usage quotas.
- Provider credentials held in a secret store or protected server environment.
- Explicit provider topology and data-egress disclosure; no silent hosted-model fallback.
- Verified webhook signatures, replay protection, idempotency and reconciliation.
- Data minimization, retention, export/deletion and incident response.
- Audit trails for access, configuration, billing and external actions.
- Rate limits, request size limits, timeouts, bounded retries and cost circuit breakers.
- Backups with tested restoration and documented recovery objectives.
- Human approval for consequential actions such as order mutation, refunds, customer messaging campaigns and payment operations.

### Implementation placement

Before creating a new service or database, produce an ADR that compares:
- a separate app/service under this monorepo;
- a dedicated repository with a clean ownership boundary;
- reuse of existing shared packages and identity components where safe.

The ADR must specify deployment, domain, tenant model, data classification, ownership, migrations, backups, provider egress, licensing, operating cost and rollback. Keep the first implementation as a modular monolith unless independent scaling or ownership proves otherwise.

Existing apps/web/sales-demo.tsx is a simulation source; generated apps/web/dist/ and web/platform/ remain build artifacts. Existing zERP remains read-only and backed by MooPiew APIs. Do not modify generated assets as the source of truth.

## 8. Automation and operating model

Automate repeatable, reversible steps only:
- lead intake to CRM with consent and source attribution;
- qualification summaries with human review;
- tenant provisioning after verified payment and approval;
- onboarding checklist and knowledge-base ingestion;
- usage metering and quota enforcement;
- billing webhook processing with signature verification and idempotency;
- support triage and escalation;
- weekly usage, cost and reliability reports;
- renewal reminders and customer feedback collection.

Do not automate irreversible or high-impact actions without an explicit authorization and review boundary. AI-generated answers must be grounded in customer-approved content, show uncertainty where appropriate and offer human escalation.

## 9. Zero-incremental-capital constraint and cost policy

“Zero capital” means no planned upfront cash investment. It does not mean infrastructure, labour, electricity, connectivity, payment fees, tax or compliance are free.

### Initial operating policy

- Use already-owned infrastructure only for development and controlled pilots.
- Use free tiers only after reviewing current limits, data handling, region, suspension behavior, backups and commercial-use terms.
- Prefer local inference for development where it meets quality and latency requirements.
- Do not promise production availability on a free tier or an unmanaged home server.
- Keep customer production workloads off personal development environments unless a reviewed threat model and operational plan explicitly approve it.
- Require customer-funded or collected implementation revenue before adding paid infrastructure, model credits, advertising or contractors.
- Keep hard monthly spend limits and an operator-controlled kill switch.

### Cost allocation

Attribute costs per tenant and per workflow. Alert at 50%, 75% and 90% of budget; block new usage at the hard limit unless an authorized operator raises it. Show customers included usage and overage terms before activation.

## 10. 12-month execution roadmap and gates

| Period | Focus | Deliverables | Exit gate |
| --- | --- | --- | --- |
| Month 1 | Discovery | Segment, 10+ interviews, workflow map, pricing hypothesis, demo script | Repeated pain and a buyer willing to evaluate a paid pilot |
| Month 2 | Concierge pilot | One supervised workflow, scope, consent/data terms, success metrics | First paid pilot or explicit pivot decision |
| Month 3 | Repeatability | Two or more pilots, delivery playbook, cost/time baseline | Evidence that at least one workflow repeats across customers |
| Months 4–5 | Product definition | SaaS ADR, threat model, tenant model, API contracts, migration and backup design | Architecture and security review accepted |
| Month 6 | SaaS foundation | Auth, tenant isolation, entitlement checks, usage metering, audit and support tooling | Cross-tenant tests, billing tests and recovery tests pass |
| Months 7–8 | Controlled beta | Customer workspace, knowledge base, supervised AI workflow, one verified integration if justified | Paid beta users, acceptable unit economics and support capacity |
| Month 9 | International validation | English onboarding, pricing test, regional/legal review | One repeatable acquisition and onboarding path outside Thailand |
| Months 10–11 | Retention and scale | Reliability improvements, referrals, cost optimization, premium workflows | Renewals and positive contribution margin |
| Month 12 | Business review | Revenue reconciliation, cohort analysis, security review, next-year plan | USD 60,000 collected or a documented evidence-based variance |

Do not start the multi-tenant build before the paid-pilot and architecture gates pass. Do not enable live channel integrations before official API access, provider terms, privacy and webhook controls are verified.

## 11. KPI dashboard

| Metric | Initial operating target / gate |
| --- | --- |
| Gross cash collected | USD 60,000 over 12 months |
| Paid pilot evidence | First paid pilot by Month 2–3 |
| Qualified conversations | 20/month hypothesis |
| Demonstrations | 5/month hypothesis |
| Subscription MRR | Report actual MRR separately; no fabricated target |
| Gross margin | Validate path to 65%+ |
| AI cost / revenue | Aim below 15%, subject to product quality |
| Monthly logo churn | Track by cohort; investigate every cancellation |
| Activation | Customer reaches first successful workflow within agreed onboarding window |
| Support | First response within one business day during published support hours |
| Availability | Define SLO before paid production; do not advertise an unmeasured SLA |
| Security | Zero unresolved critical/high findings before production onboarding |

## 12. Principal risks and mitigations

| Risk | Mitigation |
| --- | --- |
| No willingness to pay | Paid discovery and pilot before product build |
| Scope creep | One segment, one workflow, written exclusions |
| Demo mistaken for live integration | Persistent demo labels and capability matrix |
| Cross-tenant data exposure | Server-derived tenant context, DB controls and negative tests |
| AI hallucinations or harmful advice | Approved knowledge, restricted domains, human escalation |
| AI cost spikes | Quotas, model routing, budget alerts and hard limits |
| Provider outages or policy changes | Adapter boundary, explicit provider status and safe failure |
| Marketplace API restrictions | Verify official access and terms before promising connectors |
| Customer churn | Measure time saved, resolution quality and adoption |
| Payment and tax errors | Eligible payment account, reconciliation and qualified local advice |
| Data breach | Minimize data, encrypt, restrict access, audit and incident response |
| Zero-capital underfunding | Customer-funded onboarding; stop work that creates unfunded recurring cost |
| Founder delivery bottleneck | Standardized scope, onboarding checklist and support limits |

## 13. Legal, payments and governance

Before commercial onboarding, obtain appropriate adult/legal-business oversight where required and qualified advice for business registration, contracts, consumer protection, privacy, tax, employment and cross-border data processing. Confirm account eligibility and provider terms directly with payment providers. Do not bypass age, identity, business verification or financial-service requirements.

For Thailand, assess PDPA obligations, notices, lawful basis, processor agreements, retention, data-subject requests and cross-border transfers with qualified advice. For international customers, assess applicable local privacy and consumer rules before accepting data.

Use payment-provider hosted checkout/tokenization. Do not store raw card data. Treat signed webhooks as untrusted until signature, timestamp, replay, event identity and provider state are verified. Reconcile payments server-side; browser redirects are not proof of payment.

## 14. Decision log and definition of done

### Decisions

- Initial product: supervised AI Commerce Assistant.
- Initial market: Thai online sellers; global SMBs only after local validation.
- Initial commercial motion: paid implementation and pilot, then subscription.
- Existing demos: demonstration only until live integrations are verified.
- Existing MooPiew and zERP data boundaries: preserved.
- SaaS control plane: separate architecture decision required before implementation.
- Capital: no unfunded paid dependencies or production obligations.

### Definition of done for the strategy

- The business owner approves the segment, offer, pricing tests and revenue definitions.
- At least 10 customer interviews are documented without unnecessary personal data.
- One paid pilot has written scope, success criteria and customer data terms.
- Product capability statements match verified implementation.
- Unit costs and support effort are measured.
- SaaS architecture and threat model are reviewed before multi-tenant implementation.
- Payment, privacy, legal and operational requirements are reviewed before production.
- Monthly revenue is reconciled to actual collections, refunds, fees and taxes.
- All code changes follow zeaz.md, repository AGENTS.md, tests, PR review and release controls.

---

This plan is a decision and execution baseline. It does not assert that the USD 60,000 target is likely, that the product is already SaaS-ready, or that any customer, provider integration, payment approval or production control exists without current evidence.
