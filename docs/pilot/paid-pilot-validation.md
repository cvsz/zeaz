# zTTShop Paid Pilot Validation Runbook

- Status: Ready for customer discovery; no paid pilot has been evidenced
- Date: 2026-11-20
- Initial segment: Thai small online sellers
- Offer: Supervised AI Commerce Assistant
- Target: One paid, time-boxed pilot before SaaS platform expansion

## 1. Purpose

Validate that a narrowly scoped AI-assisted commerce workflow solves a recurring, measurable problem for a real business and that the buyer will pay for the outcome.

This runbook does not claim that a customer has been acquired, a payment collected, a pilot delivered or a production integration approved. Those states require dated customer and payment evidence recorded by an authorized business operator.

## 2. Ideal customer profile

Prioritize owner-operated Thai online sellers with:
- a catalogue of approximately 10–100 active SKUs;
- repeated product, price, availability or delivery questions;
- a small team manually responding to inquiries;
- a measurable baseline for inquiry volume and response time;
- an owner or authorized buyer who can approve a paid pilot;
- product information that can be substantiated and safely represented.

For the first pilot, prefer low-regulatory-risk categories such as home accessories, stationery or general household goods. Avoid medical, financial, legal, supplements and claims-sensitive product categories.

The existing zTTShop demo contains seeded skincare/serum claims, fictional customers, sample prices and simulated orders. Do not reuse those claims, product facts, customer names, order IDs or metrics as a real customer's knowledge base or evidence. Replace all sample content with customer-approved data and substantiated product information before any customer-facing pilot.

## 3. Pilot offer and boundaries

### Proposed 14-day supervised pilot

Deliver:
1. One approved product catalogue/FAQ knowledge source.
2. One inquiry-intent classification workflow.
3. AI-suggested replies grounded in approved content.
4. Human review/approval before sending external customer messages.
5. Lead/order-intent capture into an agreed customer-owned workflow.
6. Weekly usage, quality, handoff and cost report.

Explicit exclusions:
- no autonomous order placement, payment confirmation, refunds or stock mutation;
- no customer broadcast or outbound campaign automation;
- no scraping, unofficial APIs or browser-cookie automation;
- no guarantee of sales uplift, response accuracy or platform approval;
- no live connector until the relevant official developer access, permissions, terms and sandbox tests are verified;
- no high-impact product advice.

Use a manual export/import or supervised operator workflow for the pilot if no verified live connector exists. Describe it accurately as a supervised pilot, not a live marketplace integration.

## 4. Commercial hypothesis

Initial test price: THB 5,000–15,000 implementation and onboarding, plus a separately agreed pilot/subscription fee if the buyer accepts it. The amount is a hypothesis from the business plan, not a market-validated price.

Before quoting, define:
- exact workflow and channels in scope;
- number of products and knowledge sources;
- included operator seats and conversations;
- AI provider and data egress;
- customer support hours;
- data retention and deletion;
- success metrics and baseline period;
- customer responsibilities and review obligations;
- payment, tax, refund and cancellation terms;
- what happens at the end of the pilot.

Do not incur customer-specific paid API, cloud, advertising or contractor costs until an authorized adult/business operator has confirmed merchant eligibility, approved the terms and secured customer-funded payment or another explicitly approved budget.

## 5. Discovery interview

Ask the business owner:
1. Which channel receives the most product inquiries?
2. How many inquiries arrive on a normal day and at peak times?
3. What are the five most repeated questions?
4. How long does a typical first response take during and outside business hours?
5. Which questions must always be answered by a human?
6. How are leads and orders currently recorded?
7. What errors or delays create the greatest operational cost?
8. Which product facts and claims are approved and documented?
9. What customer data would the workflow need, and what data must never be processed?
10. Who approves a purchase, and what budget is available for a 14-day pilot?

Record business-level answers and avoid collecting customer personal data during discovery.

## 6. Baseline and success metrics

Capture a baseline before enabling the workflow. Use aggregate counts or anonymized samples where possible.

| Metric | Baseline | Pilot target | Measurement |
| --- | --- | --- | --- |
| First response time | Customer measured | Improve by at least 30% | Median time from inquiry receipt to first human-approved response |
| Suggested reply acceptance | Not available | At least 70% | Approved suggestions / reviewed suggestions |
| Factual answer accuracy | Human-reviewed sample | At least 95% | Correct claims against approved product source |
| Human handoff recall | Human-reviewed sample | 100% for defined critical triggers | Critical triggers correctly escalated |
| Cost per resolved inquiry | Customer baseline | Lower than agreed baseline | AI + infra + operator cost / resolved inquiry |
| Customer satisfaction | Customer baseline | No material decline | Customer's existing feedback measure |
| Workflow availability | Not yet measured | Report actual only | Successful workflow runs / eligible runs |

These are proposed acceptance thresholds. Agree them with the customer before the pilot starts. A pilot fails if the product reduces safety or customer trust even when response speed improves.

## 7. Pilot lifecycle

### Before start
- Confirm buyer authority and signed scope.
- Confirm appropriate adult/business oversight for contracts, payments and data processing.
- Complete privacy notice, data roles, lawful basis, retention, deletion and processor terms with qualified advice.
- Identify the exact source system and data fields; minimize collection.
- Use synthetic data for setup and acceptance tests.
- Record baseline and acceptance metrics.
- Confirm no unsupported live integration is represented.

### Days 1–2: configuration
- Import only customer-approved product/FAQ content.
- Record source, owner, version and review date for every knowledge source.
- Configure allowed claims, prohibited claims, handoff triggers and response limits.
- Test adversarial prompts, unknown questions, sensitive content and escalation.
- Obtain customer sign-off on the knowledge base.

### Days 3–12: supervised operation
- Keep human approval before sending messages externally.
- Review all factual errors and handoff misses.
- Track usage and costs by tenant/workflow.
- Pause automation on provider errors, suspicious activity, quota exhaustion or unsafe output.
- Hold a short weekly review with the customer.

### Days 13–14: evaluation
- Recompute metrics from retained evidence.
- Compare with baseline and agreed thresholds.
- Review operator time, AI cost, customer feedback and unresolved defects.
- Delete or return data according to the agreed retention terms.
- Decide stop, extend, repeat or convert to subscription.

## 8. Evidence required to mark a paid pilot validated

A pilot can be marked **PASS** only when all are present:
- named business customer and authorized buyer (store business name; avoid unnecessary personal details);
- signed or otherwise legally valid scope and data terms;
- invoice/receipt and independently reconciled payment evidence;
- dated start/end and exact pilot scope;
- documented baseline and customer-approved success metrics;
- evidence of actual supervised workflow use;
- reviewed output-quality and handoff sample;
- actual provider/infrastructure/operator cost;
- customer acceptance or documented reason for rejection;
- deletion/return evidence for data no longer required;
- explicit decision to renew, convert, extend or stop.

Statuses:
- PASS: all required evidence exists and acceptance criteria met.
- FAIL: pilot ran and acceptance criteria were not met.
- BLOCKED: customer, payment, legal, provider or environment dependency is unavailable.
- NOT VERIFIED: evidence is incomplete.
- NOT STARTED: no customer pilot has begun.

Current status: **NOT VERIFIED — no customer/payment evidence supplied or observed.**

## 9. Acquisition activity and funnel

Monthly activity hypothesis:
- 20 qualified owner conversations;
- 5 workflow demonstrations using synthetic data;
- 2 written pilot proposals;
- track actual paid conversion rather than assuming a fixed rate.

Track each prospect by a non-sensitive internal reference and stage: identified → contacted → qualified → discovery → demo → proposal → paid → active → evaluated → renewed/stopped. Do not bulk-message, scrape private contact data or publish customer names/logos without permission.

## 10. Decision after pilot

Proceed to tenant SaaS implementation only if:
- at least one paid pilot has been completed and accepted;
- a second prospect confirms the same workflow problem or a second paid pilot demonstrates repeatability;
- the workflow has positive contribution margin under observed costs;
- customers accept the data-processing and human-review model;
- the security architecture and threat model have passed independent review.

If these gates fail, narrow the segment or revise the offer before building more platform capability.
