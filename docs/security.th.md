# Security controls — Moopiew

## Network boundary

แอป bind ที่ `127.0.0.1` โดยค่าเริ่มต้น และรับ public traffic ผ่าน Cloudflare
Tunnel เท่านั้น; ห้ามตั้ง `HOST=0.0.0.0` บน production โดยไม่มี firewall และ reverse proxy
ที่ได้รับการทบทวนแล้ว

Cloudflare Tunnel ส่งเข้า Caddy ที่ `127.0.0.1:8080` ก่อน แล้ว Caddy ส่งต่อเข้าแอปที่
`127.0.0.1:8000` โดยรักษา `Host`, `X-Real-IP`, `X-Forwarded-For` และ
`X-Forwarded-Proto` ตาม proxy contract ของ zeaz-platform.

## Application controls

- บังคับ `ADMIN_KEY`, `EMPLOYEE_KEY` และ `KITCHEN_KEY` ที่แตกต่างจากค่าเริ่มต้น เมื่อ `REQUIRE_ADMIN_KEY=true`
- ใช้ constant-time comparison สำหรับ role key และการตรวจเบอร์โทรของ order
- จำกัดสิทธิ์ Owner, Staff และ Kitchen ที่ API; ทุกการเปลี่ยนแปลงเมนู ตั้งค่า และสถานะถูกบันทึก audit log
- จำกัดขนาด request JSON ที่ 100 KB และจำกัด request ต่อ IP สำหรับการสั่ง, ค้นหา และ dashboard
- ส่ง CSP, anti-framing, MIME sniffing, referrer และ permissions headers
- เก็บ SQLite database ด้วย permission `0600`; directory `data/` ใช้ `0700`. SQLite WAL และ foreign keys ทำให้การเขียนออเดอร์เป็น transaction-safe

## Operations

- `.env.production` และ `.env.cloudflare` ต้องเป็น `0600` และไม่อยู่ใน Git
- user services เปิด `Restart=always`, `NoNewPrivileges`, `PrivateTmp`, `ProtectSystem` และ `UMask=0077`
- ตรวจสถานะด้วย `./scripts/production-check.sh` หลังเปลี่ยน config หรือ restart service
- เก็บ Cloudflare API/tunnel token ใน secret store และหมุน token เมื่อสงสัยว่าถูกเปิดเผย
