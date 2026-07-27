# หมูปิ้ววว — Pre-order

เว็บแอปสั่งหมูปิ้งล่วงหน้าแบบ full-stack สำหรับร้านขนาดเล็ก ลูกค้าเลือกเมนูและเวลารับสินค้าได้
แอดมินดูและอัปเดตสถานะออเดอร์ได้จากหน้าเดียว ข้อมูลถูกเก็บในไฟล์ JSON บนเครื่องโดยไม่ต้องติดตั้ง package เพิ่ม

## Run locally

ต้องใช้ Python 3.10 ขึ้นไป

```bash
ADMIN_KEY='ตั้งรหัสลับที่เดายาก' ./scripts/start.sh
```

เปิด [http://127.0.0.1:8000](http://127.0.0.1:8000) เพื่อสั่งล่วงหน้า และ
`http://127.0.0.1:8000/admin.html` เพื่อจัดการออเดอร์ (ใส่ Admin key เดียวกัน)

สำหรับการพัฒนาเท่านั้น หากไม่กำหนด `ADMIN_KEY` จะใช้ค่าเริ่มต้นที่ไม่ปลอดภัย
`change-me-before-production` ห้ามนำไปใช้จริงบนอินเทอร์เน็ตโดยไม่มี HTTPS, authentication,
ฐานข้อมูล และระบบชำระเงินที่เหมาะสม

## Features

- เมนูและตะกร้าแบบ responsive ภาษาไทย
- เลือกวันและรอบรับสินค้า พร้อมแสดงจำนวนคิวที่เหลือและจำกัดความจุต่อรอบ
- API บันทึก order อย่าง atomic ใน `data/orders.json`
- ลูกค้าตรวจสอบและยกเลิก order ได้โดยใช้เลขออเดอร์กับเบอร์โทรศัพท์
- Dashboard แอดมินสำหรับดูยอดจอง, อัปเดตสถานะ/order payment, เพิ่มหรือปิดขายเมนู และตั้งค่าความจุ

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/menu` | เมนูและรอบรับสินค้า |
| `POST` | `/api/orders` | สร้างออเดอร์ |
| `POST` | `/api/order-lookup` | ค้นหาออเดอร์ด้วยเลขออเดอร์และเบอร์โทร |
| `POST` | `/api/orders/:id/cancel` | ยกเลิกออเดอร์ที่ยังใหม่/ยืนยันแล้ว |
| `GET` | `/api/admin/dashboard` | สรุปยอดและรายการออเดอร์ (header `X-Admin-Key`) |
| `PATCH` | `/api/admin/orders/:id` | เปลี่ยนสถานะ (header `X-Admin-Key`) |

การตั้งค่าเมนู/ความจุจะสร้างที่ `data/settings.json` หลังจากเปลี่ยนครั้งแรกในหน้าแอดมิน
จึงสำรอง `data/orders.json` และ `data/settings.json` พร้อมกันเสมอ

## Repository extras

โฟลเดอร์ `docs/`, `templates/`, `excel/`, และ `scripts/generate.sh` เก็บ Business-in-a-Box
framework ที่นำกลับมาใช้กับธุรกิจอื่นได้ ส่วนแอปที่ใช้งานจริงอยู่ใน `app.py` และ `web/`.
