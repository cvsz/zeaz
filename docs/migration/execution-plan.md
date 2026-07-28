# ZEAZ Full Implementation Execution Plan

สถานะเอกสาร: `planned`

เอกสารนี้แปลง `docs/roadmap.th.md` ให้เป็นแผนดำเนินงานที่ตรวจสอบได้สำหรับ AI agents และทีมพัฒนา โดยใช้หนึ่ง complete vertical slice ต่อหนึ่ง Pull Request และห้ามประกาศ phase ว่าเสร็จจนกว่า acceptance evidence จะครบ

## 1. Operating contract

1. Revalidate repository, open PRs, CI และ production constraints ก่อนแก้ไขทุกครั้ง
2. ทำหนึ่ง vertical slice ที่สมบูรณ์ต่อ PR; ห้ามทิ้ง partial implementation
3. รักษา backward compatibility ของ API, schema, routes และ operational workflows เว้นแต่มี migration ที่อนุมัติ
4. Provider credentials, admin keys และ payment secrets ต้องอยู่หลัง server-side boundary เท่านั้น
5. ทุก mutation ต้องมี authorization, idempotency/failure semantics, audit evidence และ rollback
6. รัน format, lint, typecheck, tests, security checks และ migration validation ที่ repository รองรับ
7. อัปเดต roadmap, execution record, changelog, API/schema docs และ validation report ใน PR เดียวกัน
8. Merge เฉพาะเมื่อ CI ผ่านและ acceptance criteria ครบ จากนั้นจึงเริ่ม slice ถัดไป
9. Payment, wallet, mobility และ regulated capabilities ต้องคง feature gate ปิดจนกว่าจะมี legal/credential/Sandbox evidence
10. ห้ามเปลี่ยน architecture เป็น microservices หรือ Kubernetes โดยไม่มี measured need และ ADR

## 2. Status vocabulary

ใช้เฉพาะสถานะต่อไปนี้:

- `planned`
- `in-progress`
- `blocked`
- `implemented`
- `validated`
- `out-of-scope`

`implemented` หมายถึงโค้ดและ migration อยู่ใน main แต่ยังไม่ผ่าน operational acceptance ทั้งหมด ส่วน `validated` หมายถึง acceptance evidence และ staging validation ครบ

## 3. Execution sequence

| Slice | Phase | Deliverable | Depends on | Initial status |
|---|---|---|---|---|
| Z0.1 | 0 | Repository inventory, architecture map, risk register | none | planned |
| Z0.2 | 0 | CI quality gates, release checklist, rollback contract | Z0.1 | planned |
| Z0.3 | 0 | Backup/restore drill, retention and incident runbooks | Z0.1 | planned |
| Z0.4 | 0 | Structured logging, health/readiness and baseline SLOs | Z0.2 | planned |
| Z1.1 | 1 | Identity data model and authenticated session boundary | Z0.2 | planned |
| Z1.2 | 1 | Rider/merchant/admin RBAC and resource authorization | Z1.1 | planned |
| Z1.3 | 1 | Onboarding document states, consent and review audit | Z1.2 | planned |
| Z1.4 | 1 | Service credentials, secret rotation and immutable audit events | Z1.2 | planned |
| Z2.1 | 2 | Explicit order state machine and transition guards | Z1.2 | planned |
| Z2.2 | 2 | Idempotency keys, concurrency controls and retry semantics | Z2.1 | planned |
| Z2.3 | 2 | Modular merchant/catalog/inventory compatibility boundary | Z2.1 | planned |
| Z2.4 | 2 | Delivery task, assignment and proof-of-delivery lifecycle | Z2.2 | planned |
| Z2.5 | 2 | Transactional outbox and versioned domain events | Z2.2 | planned |
| Z3.1 | 3 | Payment intent abstraction and provider feature gates | Z2.2 | planned |
| Z3.2 | 3 | SCB Sandbox inquiry/callback/signature verification | Z3.1 | blocked |
| Z3.3 | 3 | Double-entry ledger core with invariant tests | Z3.1 | planned |
| Z3.4 | 3 | Refund, reconciliation and duplicate callback handling | Z3.2,Z3.3 | blocked |
| Z3.5 | 3 | Merchant/rider settlement and auditable exports | Z3.4 | planned |
| Z4.1 | 4 | Rider availability, heartbeat and location privacy boundary | Z1.2 | planned |
| Z4.2 | 4 | Geospatial service zones and stale-location handling | Z4.1 | planned |
| Z4.3 | 4 | Deterministic dispatch policy engine and simulation tests | Z4.2,Z2.4 | planned |
| Z4.4 | 4 | Realtime tracking with polling degradation fallback | Z4.1 | planned |
| Z4.5 | 4 | ETA/route provider abstraction and operator override | Z4.3 | planned |
| Z5.1 | 5 | Generated API client and shared contracts package | Z2.5 | planned |
| Z5.2 | 5 | Least-privilege merchant portal | Z1.3,Z5.1 | planned |
| Z5.3 | 5 | Rider application workflow and offline-safe delivery actions | Z4.4,Z5.1 | planned |
| Z5.4 | 5 | Customer mobile-ready API and notification workflow | Z5.1 | planned |
| Z5.5 | 5 | Fleet portal domain and compliance documents | Z1.3,Z4.1 | planned |
| Z6.1 | 6 | Reusable service-definition and pricing/cancellation policies | Z2.5 | planned |
| Z6.2 | 6 | Parcel and multi-stop order workflow | Z6.1,Z4.3 | planned |
| Z6.3 | 6 | Multi-branch and fleet assignment | Z5.5,Z6.1 | planned |
| Z6.4 | 6 | White-label tenancy isolation design and enforcement | Z1.4,Z6.1 | planned |
| Z6.5 | 6 | Mobility readiness package and regulatory gate | Z4.5,Z6.1 | blocked |
| Z7.1 | 7 | Event taxonomy and governed analytics schema | Z2.5 | planned |
| Z7.2 | 7 | Operational BI and SLO dashboards | Z0.4,Z7.1 | planned |
| Z7.3 | 7 | Model gateway, registry, evaluation and cost controls | Z1.4 | planned |
| Z7.4 | 7 | Support copilot with human approval and audit | Z7.3 | planned |
| Z7.5 | 7 | Fraud/risk scoring shadow mode and appeal workflow | Z7.1,Z7.3 | planned |
| Z8.1 | 8 | SQLite/PostgreSQL migration ADR and parity test harness | Z2.5 | planned |
| Z8.2 | 8 | PostgreSQL migration with rollback and data reconciliation | Z8.1 | planned |
| Z8.3 | 8 | Redis coordination, sessions and rate-limit abstraction | Z1.1,Z8.2 | planned |
| Z8.4 | 8 | Worker queue and durable asynchronous jobs | Z2.5,Z8.2 | planned |
| Z8.5 | 8 | Object storage for documents and delivery evidence | Z1.3,Z8.2 | planned |
| Z8.6 | 8 | Measured service extraction ADR and first bounded extraction | Z8.3,Z8.4 | planned |
| Z9.1 | 9 | Threat models, ASVS/API control matrix and security CI | Z0.2 | planned |
| Z9.2 | 9 | SBOM, provenance, dependency policy and secret rotation | Z9.1 | planned |
| Z9.3 | 9 | Abuse controls, WAF/rate-limit policy and detection | Z8.3,Z9.1 | planned |
| Z9.4 | 9 | DR/BC exercise and production readiness review | Z8.2,Z0.3 | planned |
| Z10.1 | 10 | Localization, timezone, currency and tax configuration | Z6.1 | planned |
| Z10.2 | 10 | Enterprise account, invoicing, SSO and spend controls | Z10.1,Z1.4 | planned |
| Z10.3 | 10 | Partner API, webhook governance and developer portal | Z2.5,Z9.3 | planned |
| Z10.4 | 10 | Multi-region/residency ADR after measured requirements | Z9.4,Z10.1 | planned |

## 4. Required PR package

ทุก PR ต้องมี:

- scoped PRD/SRS และ user journey
- acceptance criteria ที่ trace ไปยัง tests
- ADR เมื่อเปลี่ยน architecture, data model หรือ security boundary
- threat model และ authorization matrix
- API/schema/event contract changes
- forward migration, rollback และ compatibility notes
- unit, integration, contract และ end-to-end tests ตามความเสี่ยง
- metrics, logs, traces, alerts หรือเหตุผลที่ไม่เกี่ยวข้อง
- runbook/support notes และ validation report
- changelog และ execution record

## 5. Validation command contract

ก่อนเริ่ม slice แรก ให้ Z0.1 ตรวจหา command จริงจาก repository และบันทึกใน `docs/migration/validation.md` อย่างน้อย:

```bash
python3 -m py_compile app.py
./scripts/migrate.sh
./scripts/health-check.sh
./scripts/ci/test.sh
```

เมื่อเพิ่ม tooling ใหม่ ต้องกำหนด command เดียวที่ CI และ local ใช้ร่วมกัน ห้ามสร้าง validation path ที่รันได้เฉพาะเครื่องผู้พัฒนา

## 6. Execution records

สร้างไฟล์หนึ่งไฟล์ต่อ slice ภายใต้:

```text
docs/migration/execution-records/<slice-id>.md
```

แต่ละ record ต้องมี:

- status และ PR/commit references
- scope และ non-goals
- changed contracts/data
- security/privacy assessment
- validation commands และผลลัพธ์
- migration/rollback evidence
- staging evidence และ known limitations
- decision ว่า `implemented`, `validated` หรือ `blocked`

## 7. External blockers

รายการต่อไปนี้ห้ามปลอม completion:

- SCB/ผู้ให้บริการชำระเงินจริง: ต้องมี approved credentials, certificate/signing material และ Sandbox evidence
- Mobility/ride-hailing: ต้องมี legal และ transport-regulatory review สำหรับพื้นที่ให้บริการจริง
- Production deployment: ต้องมี environment access, accountable approver และ rollback evidence
- PCI/ISO certification: เอกสาร readiness ไม่เท่ากับ certification
- AI fraud/suspension/financial decisions: ต้องมี policy owner, human review และ appeal process

## 8. Definition of complete

Roadmap ทั้งหมดจะถือว่า complete เมื่อทุก slice ที่ไม่ใช่ `out-of-scope` มีสถานะ `validated`, external blockers ถูกแก้ไขหรือมี formal scope decision, CI และ security gates ผ่าน, staging validation มีหลักฐาน, production activation ใช้ feature gates และเอกสาร architecture/operations/compliance ตรงกับระบบจริง
