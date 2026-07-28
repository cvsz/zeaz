# Master Roadmap ของ ZEAZ / MooPiew

Roadmap นี้กำหนดเส้นทางจากระบบร้านอาหารและจัดส่ง MooPiew ที่ใช้งานอยู่ ไปสู่แพลตฟอร์ม on-demand commerce, delivery, logistics และ mobility ที่ขยายได้ โดยรักษาความเข้ากันได้ย้อนหลัง ความปลอดภัยของข้อมูล และความต่อเนื่องของ production เป็นหลัก

> สถานะในเอกสารต้องใช้คำว่า `implemented`, `validated`, `planned`, `blocked` หรือ `out-of-scope` เท่านั้น ห้ามระบุว่าฟีเจอร์พร้อมใช้งานจนกว่าจะผ่าน acceptance gate ที่เกี่ยวข้อง

## 1. หลักการดำเนินงาน

1. พัฒนาทีละ vertical slice ที่ใช้งานได้ครบตั้งแต่ UI/API ถึงข้อมูล การตรวจสอบสิทธิ์ observability และ runbook
2. ไม่เปิด payment, wallet, dispatch หรือบริการที่อยู่ภายใต้การกำกับดูแลโดยไม่มี credential และการอนุมัติที่ถูกต้อง
3. Browser และ mobile client ต้องไม่รับ provider secrets, admin keys หรือ payment credentials
4. การเปลี่ยน schema และ API ต้องมี migration, rollback และ backward-compatibility plan
5. ทุกงานต้องมี owner, threat model, test evidence, operational metrics และ incident procedure

## 2. Baseline ที่มีแล้ว

- Customer storefront สำหรับ pickup และ delivery
- ราคา delivery ตามระยะทางและ live tracking
- เมนู สูตร สต็อก คูปอง แต้มสะสม ใบเสร็จ และ tax invoice
- การสมัคร merchant/rider, owner review, rider activation และ delivery assignment
- Owner operations console, audit history, backup, health checks และ Cloudflare Tunnel deployment
- OpenAPI contract และ optional owner-only AI provider catalog
- SCB integration boundary แบบปิดโดยค่าเริ่มต้น รอ approved credentials และ Sandbox validation

## 3. Target platform domains

```text
Experience
├── Customer Web / Mobile
├── Rider / Driver App
├── Merchant Portal
├── Fleet Portal
├── Support Console
└── Admin / Operations Console

Platform
├── Identity, IAM, KYC and consent
├── Catalog, inventory and merchant operations
├── Order, booking and trip lifecycle
├── Dispatch, routing, pricing and ETA
├── Tracking, geofence and proof of delivery
├── Payments, refunds, settlement and ledger
├── Promotions, loyalty and subscriptions
├── Notifications and communications
├── Support, dispute and incident management
├── Fraud, risk and trust & safety
└── AI, analytics and experimentation

Foundation
├── API gateway and service identity
├── PostgreSQL, Redis and object storage
├── Event bus and background workers
├── OpenTelemetry, metrics, logs and traces
├── Secrets, policy enforcement and audit
├── CI/CD, infrastructure as code and DR
└── Data warehouse / lakehouse and ML platform
```

## 4. Delivery phases

### Phase 0 — Governance and production baseline

**Goal:** ทำให้ระบบเดิมมี baseline ที่ตรวจสอบและกู้คืนได้ก่อนแยกบริการ

- จัดทำ system inventory, data classification และ dependency map
- กำหนด environments: local, test, staging และ production
- เพิ่ม release checklist, change approval และ rollback process
- ทดสอบ backup/restore, cancellation, refund และ failed-delivery recovery
- กำหนด SLI/SLO สำหรับ availability, latency, order success และ tracking freshness
- จัดทำ PDPA register, retention schedule, consent records และ data-subject request workflow

**Exit criteria**

- restore drill ผ่านใน staging
- secret scan, dependency scan และ baseline tests ผ่าน
- critical workflow มี runbook และ named owner
- production deployment ย้อนกลับได้

### Phase 1 — Identity and access boundary

**Goal:** เลิกใช้ shared owner privilege และแยกตัวตนตามบทบาท

- Customer, rider, merchant, fleet, support และ administrator identities
- OAuth/OIDC-compatible authentication, MFA/passkey และ session management
- RBAC + resource-scoped authorization; ABAC เฉพาะกรณีที่จำเป็น
- Rider/merchant onboarding พร้อม document status, consent และ review trail
- Service-to-service identity และ short-lived credentials
- Immutable security audit events

**Exit criteria:** ทุก protected endpoint มี authorization tests และไม่มี client ใดเก็บ admin key

### Phase 2 — Modular commerce and delivery core

**Goal:** แยก domain boundary โดยยังคง API เดิมผ่าน compatibility layer

- Merchant, branch, catalog, menu, inventory และ pricing modules
- Order state machine พร้อม idempotency keys และ optimistic concurrency
- Delivery quote, delivery task, rider assignment และ proof of delivery
- Coupon/loyalty rules แบบ deterministic และตรวจสอบย้อนหลังได้
- Outbox pattern สำหรับ domain events
- API versioning และ contract tests

**Exit criteria:** order lifecycle ทำงานครบทั้ง success, cancel, retry และ recovery โดยไม่เกิด double mutation

### Phase 3 — Payments, ledger and settlement

**Goal:** รองรับการเงินแบบตรวจสอบยอดได้ โดยแยก payment orchestration ออกจากบัญชีธุรกรรม

- Payment intent, authorization, capture, inquiry, callback verification และ refund
- PromptPay/QR และ approved payment provider adapters ผ่าน server-side boundary
- Double-entry ledger สำหรับ payable, receivable, fee, refund และ adjustment
- Merchant/rider settlement, reconciliation และ downloadable reports
- Feature gates และ kill switch สำหรับแต่ละ provider
- PCI scope minimization; ไม่จัดเก็บ PAN/CVV

**Exit criteria:** Sandbox end-to-end, signature verification, reconciliation และ duplicate-callback tests ผ่านก่อน production enablement

### Phase 4 — Realtime tracking and dispatch

**Goal:** ยกระดับ delivery assignment ไปเป็น dispatch platform ที่รองรับหลายบริการ

- Driver/rider availability, heartbeat และ location ingestion
- Geospatial indexing, service zones และ geofencing
- Dispatch policies: nearest eligible, batching, capacity และ manual override
- ETA, route and fare estimate provider abstraction
- WebSocket/SSE tracking พร้อม degraded polling fallback
- Privacy controls สำหรับ location precision และ retention

**Exit criteria:** dispatch มี deterministic simulation, load test, stale-location handling และ operator override

### Phase 5 — Mobile and partner experiences

- Customer mobile application
- Rider/driver application: online/offline, offers, navigation, proof of delivery, earnings
- Merchant portal: branches, catalog, inventory, orders, promotions และ settlement
- Fleet portal: vehicles, drivers, compliance documents และ assignment
- Shared API contract, generated SDK และ design system
- Offline-safe workflows และ push notifications

### Phase 6 — Multi-service marketplace

เพิ่มบริการผ่าน reusable capability model แทนการทำระบบแยกที่ซ้ำซ้อน

- Food delivery และ grocery/mart
- Parcel, courier, same-day และ multi-stop
- Scheduled delivery และ corporate accounts
- Mobility/ride booking เฉพาะเมื่อผ่าน legal and transport-regulatory review
- White-label tenancy พร้อม strict tenant isolation

บริการใหม่ทุกประเภทต้องประกาศ service definition, eligibility, pricing policy, cancellation policy, insurance/compliance requirement และ operational SLA

### Phase 7 — Data, AI and optimization

- Event taxonomy และ governed analytics schema
- Operational BI: revenue, conversion, fulfillment, cancellation และ SLA
- Demand forecasting, ETA prediction และ dispatch ranking
- Fraud/risk scoring พร้อม human review และ appeal process
- Customer support copilot และ operator assistant
- Model gateway, prompt/version registry, evaluation datasets และ cost controls
- ห้ามให้ AI ตัดสินใจด้านความปลอดภัย การระงับบัญชี หรือการเงินโดยไม่มี policy guardrail และ human oversight

### Phase 8 — Platform scale and service extraction

เริ่ม extraction เมื่อมี measured need เท่านั้น

- ย้าย SQLite ไป PostgreSQL ด้วย dual-read/dual-write หรือ migration window ที่ทดสอบแล้ว
- Redis สำหรับ cache, rate limit, session และ ephemeral coordination
- Worker queue/event bus สำหรับงาน asynchronous
- Object storage สำหรับเอกสารและหลักฐาน
- Extract services ตาม bottleneck และ ownership boundary ไม่แยก microservices ล่วงหน้า
- Kubernetes/managed container platform เมื่อ operational complexity คุ้มค่า

### Phase 9 — Security, compliance and resilience

- Threat modeling และ secure design review ต่อ vertical slice
- OWASP ASVS/API Security controls, SAST, DAST, SBOM และ provenance
- Encryption in transit/at rest, secret rotation และ key-management policy
- WAF, rate limiting, anti-automation และ abuse detection
- Incident response, breach workflow, DR และ business continuity exercises
- Readiness path สำหรับ ISO/IEC 27001, ISO/IEC 27701 และ PCI DSS ตาม scope จริง

### Phase 10 — Regional and enterprise expansion

- Multi-language, timezone, currency และ tax configuration
- Country-specific legal/policy modules
- Enterprise billing, invoicing, spend controls และ SSO
- Multi-region architecture หลังมี RTO/RPO และ residency requirement ชัดเจน
- Partner API, webhook governance และ developer portal

## 5. Repository target structure

โครงสร้างเป้าหมายนี้เป็น evolutionary layout ไม่ใช่คำสั่งให้ย้ายทุกไฟล์ในครั้งเดียว

```text
apps/
  customer-web/
  operations-web/
  merchant-web/
  rider-mobile/
  customer-mobile/
services/
  identity/
  commerce/
  orders/
  delivery/
  dispatch/
  payments/
  ledger/
  notifications/
packages/
  contracts/
  authz/
  observability/
  testing/
docs/
  architecture/
  product/
  security/
  operations/
  compliance/
  adr/
infra/
  docker/
  terraform/
  kubernetes/
scripts/
```

## 6. Required specification per vertical slice

แต่ละ slice ต้องมีอย่างน้อย:

- PRD และ user journeys
- Functional/non-functional requirements
- API/event/schema contracts
- State machine และ failure semantics
- Authorization matrix และ threat model
- Migration/rollback plan
- Unit, integration, contract และ end-to-end tests
- Metrics, logs, traces, alerts และ dashboards
- Runbook, support procedure และ acceptance evidence

## 7. AI-assisted generation workflow

```text
Roadmap
  -> scoped PRD
  -> SRS and acceptance criteria
  -> ADR and threat model
  -> API/schema/event contracts
  -> implementation plan
  -> code + migrations
  -> tests and validation
  -> observability + runbook
  -> staged rollout
  -> production evidence
```

AI agents ต้องทำงานบน branch แยก สร้างหนึ่ง complete vertical slice ต่อ PR รัน format/lint/typecheck/tests/security checks และห้าม merge เมื่อ acceptance evidence ไม่ครบ

## 8. Prioritized execution backlog

### P0 — ทำทันที

1. Auth boundary สำหรับ rider/merchant/admin
2. Backup restore drill และ incident runbooks
3. Order idempotency + explicit state machine
4. Payment Sandbox verification และ reconciliation โดยยังปิด production gate
5. Data retention/PDPA operations

### P1 — หลัง P0 ผ่าน

1. PostgreSQL migration design และ performance baseline
2. Merchant portal แบบ least privilege
3. Rider location/availability boundary
4. Structured events, OpenTelemetry และ SLO dashboards
5. Settlement ledger และ export reports

### P2 — การขยายบริการ

1. Mobile applications
2. Advanced dispatch and routing
3. Parcel/multi-stop service
4. Multi-branch and fleet management
5. AI forecasting/fraud/support capabilities

## 9. Definition of Done

งานถือว่าเสร็จเมื่อ:

- requirement และ acceptance criteria trace ไปยัง tests ได้
- security/privacy review ผ่าน
- migration และ rollback ถูกทดสอบ
- metrics/alerts/runbook พร้อมใช้งาน
- API compatibility ได้รับการยืนยัน
- CI ผ่านทั้งหมด
- deploy ใน staging และบันทึก evidence แล้ว
- production activation ใช้ feature gate และมี accountable approver
