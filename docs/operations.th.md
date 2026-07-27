# คู่มือปฏิบัติการ — หมูปิ้ววว

## หน้าจอและสิทธิ์

| บทบาท | URL | Secret | ทำอะไรได้ |
| --- | --- | --- | --- |
| Owner | `/admin.html` | `ADMIN_KEY` | เมนู ความจุ การเงิน สถานะทั้งหมด และ audit log |
| Staff | `/ops.html` | `EMPLOYEE_KEY` | ยืนยันรายการและส่งมอบสินค้า |
| Kitchen | `/ops.html?role=kitchen` | `KITCHEN_KEY` | ดูคิวและเปลี่ยนเป็นพร้อมรับ |

ตั้งค่า secret ทั้งสามค่าให้ต่างกันเสมอใน `.env.production` และให้ไฟล์มี permission `0600`.

## ฐานข้อมูลและการสำรอง

ข้อมูลอยู่ที่ `data/moopiew.sqlite3` ใน WAL mode. เมื่อเริ่มแอปครั้งแรก ระบบจะ import
`data/orders.json` และ `data/settings.json` เดิมเข้า SQLite โดยไม่ลบข้อมูลเก่า.

```bash
./scripts/backup-database.sh
```

ไฟล์สำรองจะอยู่ใต้ `output/backups/` พร้อม permission `0600`. การกู้คืนต้องหยุด service ก่อน
แล้วแทนที่ `data/moopiew.sqlite3` ด้วยไฟล์สำรองที่ตรวจสอบแล้ว จากนั้นเริ่ม service ใหม่.

## ลำดับงานประจำวัน

1. Staff เปิดหน้า `/ops.html`, ยืนยันออเดอร์ใหม่ และตรวจการชำระเงินกับ Owner เมื่อจำเป็น
2. Kitchen เปิด `/ops.html?role=kitchen`, เตรียมคิวที่ยืนยันแล้ว และกด “พร้อมรับ”
3. Staff ส่งมอบออเดอร์และกด “ส่งมอบแล้ว”
4. Owner ตรวจ dashboard และ audit log ก่อนปิดวัน
