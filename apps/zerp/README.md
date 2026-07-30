# zERP — ZEAZ Operations ERP

zERP เป็น owner-only workspace สำหรับดูข้อมูล ERP ปฏิบัติการจาก MooPiew API โดยใช้ข้อมูลจริงจากแหล่งข้อมูลเดียวกัน ไม่สร้างฐานข้อมูลหรือ credential ชุดที่สอง:

- **Accounting**: ใบเสร็จ ใบกำกับภาษี และ balanced receipt journal projection จาก operations API
- **Inventory & WMS**: คงเหลือ จุดเตือน และสูตรตัดสต็อกที่บันทึกไว้จริง
- **Manufacturing (MRP)**: รายการสูตรเมนู/วัตถุดิบจากระบบร้าน
- **CRM & Sales**: ใบสมัครร้านค้าและเมนูที่เปิดขาย
- **HRM**: สถานะไรเดอร์และความพร้อมรับงาน

หน้าจอทุก module ต้องเชื่อมต่อด้วย Owner key ก่อนอ่านข้อมูล และไม่เก็บ key ใน local storage, URL หรือฐานข้อมูล เบราว์เซอร์จะถือ key ไว้เฉพาะ memory ของแท็บนั้น

ขอบเขตบัญชีคู่, payroll, Kanban, lot/serial, BOM หลายระดับ และ workflow แบบ Odoo ยังไม่ถูกอ้างว่าเสร็จจนกว่าจะมี backend model, authorization, migration และ test ครบตาม SSOT

## Deployment

The public route is `https://zerp.zeaz.dev/`. Cloudflare DNS is a proxied CNAME
to the existing Cloudflare Tunnel. Tunnel ingress targets Caddy at
`127.0.0.1:80`; Caddy routes the `zerp.zeaz.dev` host to the local zERP web
server at `127.0.0.1:3001`. Do not expose port 3001 directly or bypass Caddy.
Build and run the production preview with `npm run build` followed by
`npm run preview`; the reviewed systemd unit is
`deploy/systemd/zerp.service`.
