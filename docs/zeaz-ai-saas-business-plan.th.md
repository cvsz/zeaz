# แผนธุรกิจ ZEAZ AI + SaaS

> สถานะ: ข้อเสนอเชิงกลยุทธ์และกรอบการดำเนินงาน ยังไม่ใช่ประมาณการรายได้ คำมั่นด้านเงินทุน การยืนยันความพร้อมของผลิตภัณฑ์ หรือการรับรอง production readiness
> เจ้าของแผน: ผู้รับผิดชอบธุรกิจ ZEAZ
> ระยะเวลา: 12 เดือนนับจากวันที่อนุมัติ
> เป้ารายได้: รายรับรวมที่เก็บเงินจริง USD 60,000
> เงินลงทุนเริ่มต้น: ไม่มีเงินสดลงทุนเพิ่ม โดยมีเงื่อนไขว่าใช้โครงสร้างพื้นฐานที่มีอยู่และ free tier ได้อย่างเหมาะสม
> ตลาด: ประเทศไทยก่อน แล้วจึงขยายต่างประเทศ

## 1. ข้อเสนอเชิงกลยุทธ์

สร้างธุรกิจ AI automation แบบ service-led และ productized โดยเริ่มจากปัญหาธุรกิจที่เกิดซ้ำ ขายงาน discovery, implementation และ pilot ที่มีขอบเขตชัดเจนเพื่อพิสูจน์ความต้องการและสร้างกระแสเงินสด จากนั้นจึงเปลี่ยน workflow ที่ลูกค้าต้องการซ้ำให้เป็นความสามารถแบบ subscription

จุดเริ่มต้นที่แนะนำคือ **AI ช่วยงาน commerce สำหรับร้านค้าออนไลน์ขนาดเล็ก** ได้แก่ ความรู้สินค้า การจัดประเภทคำถามลูกค้า การช่วยตอบคำถาม การส่งต่อให้พนักงาน การเก็บ lead/ความต้องการสั่งซื้อ และรายงานการดำเนินงาน เริ่มพิสูจน์ตลาดในประเทศไทยก่อน และขยายไปยัง SMB ต่างประเทศเมื่อ onboarding, support และ unit economics ทำซ้ำได้จริง

เป้า USD 60,000 เป็นเป้าหมายแบบ stretch ที่ท้าทาย ไม่ใช่การรับประกันรายได้ ให้วัดจากเงินที่เก็บได้จริง หัก refund และ chargeback และแยกภาษีกับค่าใช้จ่ายออกจากรายได้ รายได้รวมไม่ใช่กำไร

### หลักการสำคัญ

1. ขายผลลัพธ์ที่วัดได้ก่อนสร้างแพลตฟอร์มขนาดใหญ่
2. เริ่มจากลูกค้ากลุ่มเดียวและ workflow ที่ทำซ้ำได้หนึ่งเรื่อง
3. Demo และ simulation ต้องระบุว่าเป็น Demo ห้ามสื่อว่าเป็น integration จริง
4. ข้อมูลลูกค้า tenant credentials billing และ audit ต้องควบคุมจาก server
5. รักษาขอบเขต source of truth ของ MooPiew, zERP และ repository เดิม
6. ใช้จ่ายเมื่อมีความต้องการที่ผ่านการยืนยันและมีแหล่งเงินรองรับ
7. ห้ามเปิด paid production service จนกว่าจะผ่านเงื่อนไข reliability, privacy, security, support และกฎหมาย

## 2. สถานะจริงของระบบใน repository

repository ปัจจุบันมีองค์ประกอบหลายส่วน แต่มีระดับความพร้อมต่างกัน:

| องค์ประกอบ | บทบาทที่ตรวจพบ | แนวทางเชิงพาณิชย์ |
| --- | --- | --- |
| ZEAZ AI Live Catalog / Qwen chat | ระบบ catalog โมเดลและ chat พร้อมการตั้งค่า provider สำหรับ owner | ใช้เป็นความสามารถภายในและ demo แบบควบคุม ยังไม่ใช่ multi-tenant AI API ที่คิด usage ลูกค้าได้ |
| zTTShop ERP + AI Sales demo | Frontend simulation มีบทสนทนา ออเดอร์ สต็อก และ channel sync จำลอง | ใช้สาธิตและเก็บ requirement เท่านั้น |
| zERP | Operations workspace แบบ protected และ read-only ที่อ่านข้อมูลจาก MooPiew API | เป็น internal operations slice ยังไม่ใช่ ERP SaaS แบบ multi-tenant |
| MooPiew service | ระบบร้านอาหาร commerce/delivery และแหล่งข้อมูลปฏิบัติการเดิม | ต้องแยกขอบเขต ห้ามนำฐานข้อมูลร้านอาหารไปเป็น tenant store ของ SaaS อื่น |

zTTShop demo ระบุชัดว่าไม่ได้เรียก Facebook, Shopee, payment หรือ production order API จริง ส่วนเอกสาร zERP ระบุว่ายังไม่ทำ ERP ความสามารถใหญ่จนกว่าจะมี backend model, authorization, migration และ test ครบ ระบบเหล่านี้ยังไม่ได้พิสูจน์ว่ามี SaaS control plane แบบ multi-tenant, subscription entitlement, customer billing lifecycle หรือ production channel connector ครบแล้ว

ข้อเท็จจริงเหล่านี้เป็น release boundary เอกสารการตลาด ใบเสนอราคา demo และสัญญาต้องอธิบายความสามารถตามจริง

## 3. ลูกค้าเป้าหมายและข้อเสนอแรก

### กลุ่มแรก: ร้านค้าออนไลน์ไทย

มุ่งที่เจ้าของร้านหรือทีมขนาดเล็กที่ขายผ่าน social commerce/marketplace มีคำถามสินค้าเดิมซ้ำ ๆ ตอบช้า และส่งต่อออเดอร์ด้วยมือ เลือกหมวดสินค้าที่ข้อมูลชัดเจนและความเสี่ยงด้านกฎระเบียบต่ำก่อน หลีกเลี่ยงการเริ่มจากคำแนะนำด้านการแพทย์ การเงิน กฎหมาย หรือเรื่องที่มีผลกระทบสูง

### กลุ่มถัดไป: SMB ต่างประเทศ

หลังจาก pilot ในไทยทำซ้ำได้ จึงทดสอบกับธุรกิจ ecommerce และ service business ที่ใช้ภาษาอังกฤษและมีปัญหา support/lead qualification คล้ายกัน ห้ามเพิ่มหลายภาษาและหลาย channel ก่อนมีลูกค้าจ่ายเงินจริงรองรับ

### ข้อเสนอแรก: AI Commerce Assistant

บริการแบบมีขอบเขต ประกอบด้วย:
- knowledge base ของสินค้าและ FAQ ที่ลูกค้าอนุมัติ;
- การจัดประเภทคำถามและเสนอคำตอบ;
- human handoff และ escalation;
- การเก็บ lead และส่งต่อเจตนาสั่งซื้อไปยังระบบที่ได้รับอนุมัติ;
- การทบทวนคุณภาพคำตอบและรายงาน usage.

ช่วงแรกสามารถใช้ workflow ที่มีคนกำกับและเครื่องมือเดิมได้ แต่ห้ามอ้างว่าระบบสร้างออเดอร์จริง แก้สต็อก ยืนยันการชำระเงิน หรือ sync marketplace จริง จนกว่าจะ implement, authorize, test และ verify ครบทุกเส้นทาง

### ลำดับผลิตภัณฑ์

1. **Phase A — Productized service:** ตั้งค่า workflow หนึ่งเรื่องให้ลูกค้าหนึ่งราย คิดค่าติดตั้งและ pilot ที่มีระยะเวลาชัดเจน
2. **Phase B — SaaS core:** เมื่อมีลูกค้าจ่ายเงินจริงอย่างน้อย 3 รายและมี requirement ซ้ำกัน จึงสร้าง tenant workspace, authentication, knowledge-base management, workflow configuration, usage metering และ support tooling
3. **Phase C — Integrations:** เพิ่มทีละ channel หลังตรวจสิทธิ์ API เงื่อนไข partner, webhook security, idempotency, privacy และ support ได้ครบ
4. **Phase D — Analytics และ workflow เพิ่มเติม:** เพิ่มรายงานและ automation เมื่อ retention และ paid usage สนับสนุนแล้ว

ห้ามสร้างสามผลิตภัณฑ์แยกกันตั้งแต่แรก ให้ AI support, workflow automation และ analytics เป็นความสามารถของข้อเสนอเดียว จนกว่าจะมี demand รองรับการแยกแพ็กเกจ

## 4. สมมติฐานราคาเพื่อทดสอบ

ต้องทดสอบ willingness to pay ผ่านการสัมภาษณ์และ paid pilot ตัวเลขต่อไปนี้เป็นราคาทดลอง ไม่ใช่ผลวิจัยตลาดหรือราคาประกาศอย่างเป็นทางการ

| ข้อเสนอ | ราคาไทยเพื่อทดสอบ | ราคาต่างประเทศเพื่อทดสอบ |
| --- | ---: | ---: |
| Starter subscription | 990 บาท/เดือน | USD 29/เดือน |
| Business subscription | 2,990 บาท/เดือน | USD 79/เดือน |
| Pro subscription | 5,990 บาท/เดือน | USD 149/เดือน |
| Implementation | 5,000–15,000 บาท | USD 300–750 |
| Custom integration | ประเมินเป็นรายงาน | ประเมินเป็นรายงาน |

แต่ละ plan ต้องกำหนดจำนวนผู้ใช้ channel, knowledge sources, จำนวน conversation/token, retention, support hours, overage และข้อยกเว้นให้ชัดเจน ห้ามขาย AI usage แบบไม่จำกัด ต้องแจ้งสกุลเงิน conversion ภาษี และค่าธรรมเนียมก่อนชำระเงิน ห้ามรับประกันอัตรา THB/USD คงที่

## 5. โมเดลรายได้ USD 60,000

### สัดส่วนเป้าหมาย

| รายได้ | เป้า 12 เดือน | หลักการนับรายได้ |
| --- | ---: | --- |
| SaaS subscriptions | USD 40,000 | เงิน subscription ที่เก็บได้สำหรับรอบบริการ |
| Implementation และ onboarding | USD 15,000 | งาน setup ที่ส่งมอบ ยอมรับ และเก็บเงินแล้ว |
| Premium integrations / managed workflows | USD 5,000 | งานตามขอบเขตที่ยอมรับแล้วหรือ add-on ที่เก็บเงินแล้ว |
| **รวม** | **USD 60,000** | รายได้รวมก่อนค่าใช้จ่ายและภาษี |

ห้ามนับค่าติดตั้งซ้ำเมื่อรวมอยู่ใน subscription ต้องแยก invoice, collection, refund, chargeback, tax, fee, service period และ currency conversion

### เป้ารายรับรายเดือน

ตัวเลขนี้คือเป้ารายรับรวมที่เก็บได้ในแต่ละเดือน ไม่ใช่ MRR และไม่ใช่การพยากรณ์ ผลรวมเท่ากับ USD 60,000 พอดี

| เดือน | เป้ารายเดือน | เป้าสะสม | หลักฐานที่ต้องมี |
| --- | ---: | ---: | --- |
| 1 | 0 | 0 | สัมภาษณ์และข้อเสนอที่มีผู้ซื้อสนใจจริง |
| 2 | 500 | 500 | paid discovery หรือ pilot แรก |
| 3 | 1,500 | 2,000 | ส่งมอบ implementation แรกและลูกค้ายอมรับ |
| 4 | 2,500 | 4,500 | ส่งมอบ pilot ซ้ำได้ |
| 5 | 3,500 | 8,000 | ลูกค้าแรกเปลี่ยนเป็น subscription |
| 6 | 4,500 | 12,500 | มีข้อมูล retention และต้นทุนต่อหน่วย |
| 7 | 5,500 | 18,000 | มีช่องทางหาลูกค้าที่ทำซ้ำได้ |
| 8 | 6,500 | 24,500 | onboarding เป็นมาตรฐานมากขึ้น |
| 9 | 7,500 | 32,000 | ทดสอบตลาดต่างประเทศแบบควบคุม |
| 10 | 8,500 | 40,500 | รายได้ขยายจากลูกค้าเดิมที่ยังใช้งาน |
| 11 | 9,500 | 50,000 | renewal และ referral คาดการณ์ได้จากข้อมูลจริง |
| 12 | 10,000 | 60,000 | มีกำลังส่งมอบงานรองรับ |

นี่เป็นแผนแบบ stretch หากยอดจ่ายจริง conversion หรือกำลังส่งมอบไม่ผ่าน gate สองเดือนติดต่อกัน ให้ปรับเป้าหมาย ขอบเขต หรือข้อเสนอ ไม่ใช่สร้างตัวเลขรายได้สมมติ

### เงื่อนไข unit economics

ติดตามแยกตาม tenant และ plan:
- รายได้ที่เก็บได้และ refund;
- payment fee และภาษี;
- model/provider cost และ tokens;
- infrastructure, storage, email และ observability;
- ชั่วโมง onboarding และ support;
- gross margin และ contribution margin;
- acquisition cost และ payback period;
- activation, weekly active use, renewal และ churn.

ห้ามขยาย paid acquisition จนกว่า contribution margin เป็นบวกและมีข้อมูล cohort สนับสนุน payback เป้าหมาย gross margin 65% เป็นเกณฑ์ที่ต้องพิสูจน์ ไม่ใช่ผลลัพธ์ปัจจุบัน

## 6. การหาลูกค้าและการขาย

### ช่องทาง

1. ติดต่อธุรกิจแบบเฉพาะเจาะจงโดยผู้ก่อตั้ง โดยอ้างอิงปัญหาที่เห็นได้จริง
2. สาธิตด้วย synthetic data และติดป้าย demo ให้ชัดเจน
3. เผยแพร่เนื้อหาความรู้ที่แสดงผลลัพธ์ workflow ก่อน/หลัง โดยไม่กล่าวอ้าง AI เกินจริง
4. ร่วมมือกับ web agency, ecommerce implementer และ consultant ในพื้นที่
5. referral หลังส่งมอบคุณค่าที่วัดผลได้
6. SEO ภาษาไทยและอังกฤษสำหรับปัญหาปฏิบัติการที่เฉพาะเจาะจง

ต้องปฏิบัติตามเงื่อนไข platform, privacy และ anti-spam ห้าม scrape ข้อมูลส่วนตัว ส่งข้อความจำนวนมากโดยไม่ได้รับอนุญาต หรือสร้าง endorsement ปลอม

### สมมติฐานกิจกรรมรายเดือน

- คุยกับธุรกิจที่ผ่านการคัดกรอง 20 ราย;
- สาธิต workflow 5 ครั้ง;
- ส่ง pilot proposal 2 ฉบับ;
- ตั้งเป้าชนะ paid pilot 1–2 รายตาม conversion จริง;
- ทบทวนเหตุผลที่ปิดการขายไม่ได้และเวลาที่ใช้ onboarding ทุกสัปดาห์

ตัวเลขนี้เป็นเป้ากิจกรรม ไม่ใช่อัตรา conversion ที่รับประกัน ต้องติดตามตั้งแต่ source, qualification, proposal, payment, activation จนถึง renewal

### ขั้นตอนขาย

1. คัดกรองประเภทธุรกิจ ปริมาณงาน เครื่องมือเดิม ผู้ตัดสินใจ ความอ่อนไหวของข้อมูล และงบประมาณ
2. วัดต้นทุนหรือความล่าช้าปัจจุบันจากข้อมูลที่ลูกค้าให้
3. สาธิตเฉพาะ workflow ที่แก้ปัญหานั้น
4. ตกลง scope, success metric, data terms, exclusions และวันสิ้นสุด pilot
5. รับชำระผ่านบัญชีที่มีสิทธิ์ก่อนเกิดค่าใช้จ่ายเฉพาะลูกค้า
6. เริ่ม onboarding ด้วย synthetic data ก่อนใช้ข้อมูลจริงขั้นต่ำที่ลูกค้าอนุญาต
7. ทบทวนผลลัพธ์และเปลี่ยนเป็น subscription เมื่อมีคุณค่าที่เกิดซ้ำจริง

## 7. สถาปัตยกรรมเป้าหมายและขอบเขต repository

SaaS control plane เป็นระบบในอนาคต ห้ามยัดเข้า MooPiew app.py หรือใช้ SQLite ของร้านอาหารเป็นฐานข้อมูล tenant ของผลิตภัณฑ์อื่น

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

### ข้อกำหนดก่อนใช้ข้อมูลลูกค้าจริง

- tenant identity ต้องมาจาก authenticated server-side context ห้ามเชื่อ tenant ID จาก client
- database-level tenant isolation พร้อม authorization tests และ cross-tenant negative tests
- subscription entitlement และ usage quota ต้องตรวจฝั่ง server
- provider credentials อยู่ใน secret store หรือ protected server environment
- ระบุ provider topology และ data egress ให้ชัด ห้าม fallback ไป hosted model โดยไม่แจ้ง
- webhook ต้องตรวจ signature, replay protection, idempotency และ reconciliation
- มี data minimization, retention, export/deletion และ incident response
- audit การเข้าถึง การตั้งค่า billing และ external action
- rate limit, request size limit, timeout, bounded retry และ cost circuit breaker
- backup ที่ทดสอบ restore แล้วและมี recovery objective
- งานที่มีผลกระทบ เช่น แก้ออเดอร์ refund ส่งข้อความหาลูกค้า หรือ payment ต้องมี human approval

### ตำแหน่งการพัฒนา

ก่อนสร้าง service หรือ database ใหม่ ต้องทำ ADR เปรียบเทียบ:
- แยก app/service ใน monorepo นี้;
- สร้าง repository ใหม่ที่มีขอบเขต ownership ชัดเจน;
- reuse shared package และ identity component เดิมเมื่อปลอดภัย

ADR ต้องระบุ deployment, domain, tenant model, data classification, ownership, migration, backup, provider egress, licensing, operating cost และ rollback ให้ชัดเจน เริ่มเป็น modular monolith ก่อน เว้นแต่มีหลักฐานว่าต้องแยก scale หรือ ownership

apps/web/sales-demo.tsx เป็น simulation source ส่วน apps/web/dist/ และ web/platform/ เป็น generated artifacts เท่านั้น zERP ยังคงเป็น read-only และใช้ MooPiew API เป็นแหล่งข้อมูล ห้ามแก้ generated asset เป็น source of truth

## 8. Automation และรูปแบบการปฏิบัติงาน

ทำ automation เฉพาะขั้นตอนที่ทำซ้ำได้และย้อนกลับได้:
- รับ lead เข้า CRM พร้อม consent และ source attribution;
- สรุปการคัดกรองด้วย AI และให้คนตรวจ;
- สร้าง tenant หลังยืนยันการชำระเงินและอนุมัติ;
- onboarding checklist และ knowledge-base ingestion;
- usage metering และ quota enforcement;
- ประมวลผล billing webhook โดยตรวจ signature และ idempotency;
- จัดประเภท support และส่งต่อ;
- รายงาน usage, cost และ reliability รายสัปดาห์;
- แจ้ง renewal และเก็บ feedback.

ห้ามให้ AI ทำงานที่ย้อนกลับไม่ได้หรือมีผลกระทบสูงโดยไม่มี authorization และ review boundary คำตอบ AI ต้องอิงเนื้อหาที่ลูกค้าอนุมัติ ระบุความไม่แน่ใจเมื่อเหมาะสม และมีช่องทางส่งต่อมนุษย์

## 9. ข้อจำกัดเงินลงทุนเริ่มต้นเป็นศูนย์

“ไม่มีเงินลงทุนเริ่มต้น” หมายถึงไม่มีแผนใช้เงินสดลงทุนล่วงหน้า ไม่ได้แปลว่า infrastructure, แรงงาน, ไฟฟ้า, internet, payment fee, ภาษี หรือ compliance ไม่มีต้นทุน

### นโยบายเริ่มต้น

- ใช้ infrastructure ที่มีอยู่เฉพาะ development และ pilot แบบควบคุม
- ใช้ free tier หลังตรวจ limit, data handling, region, suspension, backup และเงื่อนไข commercial use
- ใช้ local inference สำหรับ development เมื่อคุณภาพและ latency เหมาะสม
- ห้ามรับประกัน production availability บน free tier หรือ home server ที่ไม่มีการดูแล
- ห้ามนำ production workload ของลูกค้าไปไว้บนเครื่อง development ส่วนตัว เว้นแต่ผ่าน threat model และ operational plan
- ต้องมีรายได้ onboarding ที่ลูกค้าจ่ายหรือเก็บได้ก่อนเพิ่ม paid infrastructure, model credits, advertising หรือ contractor
- กำหนด hard monthly spend limit และ kill switch ที่ operator ควบคุมได้

### การจัดสรรต้นทุน

แยกต้นทุนตาม tenant และ workflow แจ้งเตือนเมื่อใช้ 50%, 75%, 90% ของงบ และหยุด usage ใหม่เมื่อถึง hard limit เว้นแต่ operator ที่มีอำนาจอนุมัติให้เพิ่มงบ ต้องแจ้ง usage ที่รวมและ overage ก่อนเปิดใช้งาน

## 10. Roadmap 12 เดือนและ decision gates

| ช่วงเวลา | เป้าหมาย | สิ่งส่งมอบ | Gate ก่อนผ่าน |
| --- | --- | --- | --- |
| เดือน 1 | Discovery | เลือก segment, สัมภาษณ์ 10+ ราย, workflow map, pricing hypothesis และ demo script | พบปัญหาซ้ำและผู้ซื้อพร้อมประเมิน paid pilot |
| เดือน 2 | Concierge pilot | workflow ที่มีคนกำกับ, scope, consent/data terms และ success metric | มี paid pilot แรกหรือมีการตัดสินใจ pivot ชัดเจน |
| เดือน 3 | Repeatability | pilot อย่างน้อย 2 ราย, delivery playbook, baseline cost/time | พิสูจน์ workflow ที่ใช้ซ้ำข้ามลูกค้าได้อย่างน้อยหนึ่งเรื่อง |
| เดือน 4–5 | Product definition | SaaS ADR, threat model, tenant model, API contract, migration และ backup design | ผ่าน architecture และ security review |
| เดือน 6 | SaaS foundation | auth, tenant isolation, entitlement, usage metering, audit และ support tooling | cross-tenant, billing และ recovery tests ผ่าน |
| เดือน 7–8 | Controlled beta | customer workspace, knowledge base, supervised AI workflow และ integration ที่ verify แล้วหากจำเป็น | มี paid beta, unit economics และ support capacity ที่ยอมรับได้ |
| เดือน 9 | International validation | English onboarding, pricing test และ regional/legal review | มี acquisition/onboarding path ที่ทำซ้ำได้นอกไทย |
| เดือน 10–11 | Retention and scale | reliability, referral, cost optimization และ premium workflow | renewal และ contribution margin เป็นบวก |
| เดือน 12 | Business review | กระทบยอดรายได้ วิเคราะห์ cohort ตรวจ security และวางแผนปีถัดไป | เก็บรายได้ USD 60,000 หรือบันทึก variance ตามหลักฐานจริง |

ห้ามเริ่ม multi-tenant build ก่อนผ่าน paid-pilot และ architecture gate ห้ามเปิด live channel integration ก่อนตรวจ official API access, terms, privacy และ webhook control

## 11. KPI dashboard

| ตัวชี้วัด | เป้าหมายหรือ gate เริ่มต้น |
| --- | --- |
| Gross cash collected | USD 60,000 ใน 12 เดือน |
| Paid pilot | มีหลักฐาน paid pilot แรกในเดือน 2–3 |
| Qualified conversations | สมมติฐาน 20 ราย/เดือน |
| Demonstrations | สมมติฐาน 5 ครั้ง/เดือน |
| Subscription MRR | รายงาน MRR จริงแยกต่างหาก ห้ามสร้างตัวเลขสมมติ |
| Gross margin | พิสูจน์เส้นทางสู่ 65%+ |
| AI cost / revenue | ตั้งเป้าต่ำกว่า 15% โดยต้องไม่ลดคุณภาพ |
| Monthly logo churn | ติดตามเป็น cohort และวิเคราะห์ทุกการยกเลิก |
| Activation | ลูกค้าใช้งาน workflow แรกสำเร็จภายใน onboarding window ที่ตกลง |
| Support | ตอบครั้งแรกภายใน 1 วันทำการตาม support hours ที่ประกาศ |
| Availability | กำหนด SLO ก่อน production ห้ามโฆษณา SLA ที่ยังไม่ได้วัด |
| Security | ไม่มี critical/high finding ที่ยังไม่แก้ก่อน production customer |

## 12. ความเสี่ยงและการควบคุม

| ความเสี่ยง | วิธีควบคุม |
| --- | --- |
| ไม่มีคนยอมจ่าย | paid discovery และ pilot ก่อนสร้างผลิตภัณฑ์ |
| Scope creep | หนึ่ง segment หนึ่ง workflow และเขียน exclusions |
| ลูกค้าเข้าใจ demo ว่าใช้งานจริง | ติดป้าย demo และ capability matrix |
| ข้อมูลข้าม tenant รั่ว | server-derived tenant context, DB controls และ negative tests |
| AI ตอบผิดหรือให้คำแนะนำอันตราย | approved knowledge, จำกัด domain และ human escalation |
| AI cost พุ่ง | quota, model routing, budget alert และ hard limit |
| provider outage/เปลี่ยนนโยบาย | adapter boundary, provider status และ safe failure |
| Marketplace API จำกัดสิทธิ์ | ตรวจ official access และ terms ก่อนรับปาก connector |
| ลูกค้ายกเลิก | วัดเวลาที่ประหยัด คุณภาพการแก้ปัญหา และ adoption |
| Payment/ภาษีผิดพลาด | บัญชีรับเงินที่มีสิทธิ์ กระทบยอด และปรึกษาผู้เชี่ยวชาญ |
| ข้อมูลรั่ว | เก็บข้อมูลขั้นต่ำ เข้ารหัส จำกัดสิทธิ์ audit และ incident response |
| เงินทุนไม่พอ | ให้ลูกค้าจ่าย onboarding และหยุดงานที่สร้าง recurring cost โดยไม่มีเงินรองรับ |
| ผู้ก่อตั้งเป็นคอขวด | scope มาตรฐาน checklist onboarding และ support limit |

## 13. กฎหมาย การชำระเงิน และ governance

ก่อนรับลูกค้าเชิงพาณิชย์ ให้มีผู้ใหญ่/ผู้ดูแลกิจการและคำปรึกษาที่เหมาะสมตามข้อกำหนดเรื่องการจดทะเบียน สัญญา consumer protection, privacy, tax, employment และ cross-border data processing ตรวจ eligibility และ terms กับ payment provider โดยตรง ห้ามหลบเลี่ยงข้อกำหนดอายุ ตัวตน การยืนยันธุรกิจ หรือบริการทางการเงิน

สำหรับประเทศไทย ให้ประเมินหน้าที่ตาม PDPA ได้แก่ privacy notice, lawful basis, processor agreement, retention, data-subject request และ cross-border transfer กับผู้เชี่ยวชาญ สำหรับลูกค้าต่างประเทศต้องประเมินกฎหมาย privacy และ consumer ที่เกี่ยวข้องก่อนรับข้อมูล

ใช้ hosted checkout/tokenization ของ payment provider ห้ามเก็บ raw card data webhook ต้องตรวจ signature, timestamp, replay, event identity และสถานะจาก provider ก่อนถือว่าน่าเชื่อถือ ต้องกระทบยอดฝั่ง server; browser redirect ไม่ใช่หลักฐานการชำระเงิน

## 14. Decision log และ Definition of Done

### ข้อตัดสินใจ

- ผลิตภัณฑ์แรก: supervised AI Commerce Assistant
- ตลาดแรก: ร้านค้าออนไลน์ไทย; ขยาย global SMB หลังผ่าน local validation
- รูปแบบขาย: implementation และ paid pilot ก่อน subscription
- Demo เดิม: ใช้สาธิตเท่านั้นจนกว่า live integration จะ verify
- ขอบเขตข้อมูล MooPiew และ zERP: คงเดิม
- SaaS control plane: ต้องมี architecture decision แยกก่อน implement
- เงินลงทุน: ห้ามเพิ่ม paid dependency หรือ production obligation โดยไม่มีเงินรองรับ

### Definition of Done ของแผน

- เจ้าของธุรกิจอนุมัติ segment, offer, pricing test และนิยามรายได้
- มีบันทึก customer interview อย่างน้อย 10 ราย โดยไม่เก็บข้อมูลส่วนบุคคลเกินจำเป็น
- มี paid pilot หนึ่งรายพร้อม scope, success criteria และ data terms เป็นลายลักษณ์อักษร
- คำกล่าวอ้างผลิตภัณฑ์ตรงกับ implementation ที่ตรวจสอบแล้ว
- วัด unit cost และ support effort ได้
- SaaS architecture และ threat model ผ่าน review ก่อนทำ multi-tenant
- ทบทวน payment, privacy, legal และ operational requirements ก่อน production
- กระทบยอดรายได้รายเดือนกับ collection, refund, fee และ tax จริง
- การเปลี่ยนแปลงโค้ดทั้งหมดทำตาม zeaz.md, AGENTS.md, tests, PR review และ release controls

---

เอกสารนี้เป็นกรอบตัดสินใจและดำเนินงาน ไม่ได้ยืนยันว่าเป้ารายได้ USD 60,000 มีโอกาสเกิดขึ้นแน่นอน ผลิตภัณฑ์พร้อมเป็น SaaS แล้ว หรือมีลูกค้า integration, payment approval และ production control ใดอยู่จริงโดยไม่มีหลักฐานปัจจุบัน
