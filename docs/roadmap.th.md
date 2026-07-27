# Roadmap: Business-in-a-Box Generator Framework

## เป้าหมาย

เปลี่ยนไฟล์ตั้งค่าธุรกิจเพียงไฟล์เดียวให้เป็นชุดเริ่มต้นที่พร้อมใช้งาน: แผนธุรกิจ
คู่มือปฏิบัติงาน การตลาด แบรนด์ ข้อมูลการเงิน และไฟล์สำหรับพิมพ์

## ลำดับการส่งมอบ

1. พื้นฐาน repository และเอกสารสองภาษา
2. เนื้อหาหลัก: แผนธุรกิจ สูตรปฏิบัติงาน การตลาด และแบรนด์
3. Generator: schema, template และสคริปต์
4. Automation: ตรวจสอบ สร้าง package และ release
5. ปรับแต่ง asset และ archive ให้พร้อมส่งมอบ

## เกณฑ์สำเร็จ

`./scripts/generate.sh examples/cafe.yaml output/cafe` สร้าง business kit
ฉบับสมบูรณ์โดยไม่แก้ template ต้นทาง และ `./scripts/package.sh output/cafe`
สร้าง ZIP สำหรับส่งต่อได้
