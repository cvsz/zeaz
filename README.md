# หมูปิ้ววว — Restaurant operations

เว็บแอปสั่งหมูปิ้งล่วงหน้าและระบบปฏิบัติการร้านสำหรับธุรกิจขนาดเล็ก: ลูกค้าจองสินค้า,
Staff ยืนยันและส่งมอบ, Kitchen ทำคิว และ Owner จัดการร้านจากคนละ dashboard.

## Run locally

ต้องใช้ Python 3.10 ขึ้นไป และต้องใช้ secret แยกกันทุกบทบาท:

```bash
ADMIN_KEY='owner-secret' EMPLOYEE_KEY='staff-secret' KITCHEN_KEY='kitchen-secret' ./scripts/start.sh
```

เปิด [http://127.0.0.1:8000](http://127.0.0.1:8000) เพื่อลูกค้าสั่งล่วงหน้า,
`/dashboard.html` เป็นทางเข้ารวม: `/admin.html` สำหรับ Owner, `/ops.html` สำหรับ Staff และ `/ops.html?role=kitchen` สำหรับ Kitchen.

Premium React platform shell อยู่ที่ `/platform/` และใช้ API/database เดียวกับหน้า preorder ปัจจุบัน.

## Features

- SQLite database (`data/moopiew.sqlite3`) พร้อม WAL, foreign keys และ atomic transactions
- import ข้อมูล `data/orders.json` และ `data/settings.json` เดิมอัตโนมัติครั้งแรก โดยไม่ลบต้นฉบับ
- pickup capacity, customer order lookup/cancellation และ payment state
- `AUTO_CONFIRM_ORDERS=true` ยืนยันการรับออเดอร์โดยอัตโนมัติ แต่ไม่ยืนยันว่าได้รับชำระเงิน
- Owner dashboard: ยอดจอง เมนู ความจุ การชำระเงิน และ audit log
- Staff dashboard: ยืนยันและส่งมอบออเดอร์
- Kitchen dashboard: คิวที่ต้องเตรียมและเปลี่ยนเป็นพร้อมรับ
- RBAC แยก `ADMIN_KEY`, `EMPLOYEE_KEY`, `KITCHEN_KEY`, rate limiting และ security headers

## API

| Method | Endpoint | Access |
| --- | --- | --- |
| `GET` | `/api/menu` | Public |
| `POST` | `/api/orders` | Public |
| `POST` | `/api/order-lookup` | Public |
| `POST` | `/api/orders/:id/cancel` | Public with matching phone |
| `GET` | `/api/admin/dashboard` | `X-Admin-Key` |
| `PATCH` | `/api/admin/orders/:id` | `X-Admin-Key` |
| `GET` | `/api/staff/dashboard` | `X-Employee-Key` |
| `PATCH` | `/api/staff/orders/:id` | `X-Employee-Key` |
| `GET` | `/api/kitchen/dashboard` | `X-Kitchen-Key` |
| `PATCH` | `/api/kitchen/orders/:id` | `X-Kitchen-Key` |

รายละเอียด request/response อยู่ใน [OpenAPI contract](docs/openapi.yaml).

## Operations and deployment

อ่าน [คู่มือปฏิบัติการ](docs/operations.th.md) สำหรับสิทธิ์ การสำรอง และลำดับงานประจำวัน.
ใช้ `./scripts/backup-database.sh` เพื่อสร้าง SQLite backup ที่ permission ปลอดภัย.

Production binds the app to loopback and publishes it only through the Cloudflare Tunnel. Terraform,
cloudflared and the reverse proxy instructions are in [Cloudflare deployment guide](docs/cloudflare-deployment.md).
อ่าน [security controls](docs/security.th.md) ก่อนเปลี่ยน `HOST`, secrets หรือ systemd.

## Repository extras

โฟลเดอร์ `docs/`, `templates/`, `excel/`, และ `scripts/generate.sh` เก็บ Business-in-a-Box framework
ที่นำกลับมาใช้กับธุรกิจอื่นได้ ส่วนแอปที่ใช้งานจริงอยู่ใน `app.py` และ `web/`.
