# MediaVerse Use Cases

## UC01: Import Product Folder

**Actor:** Admin  
**Precondition:** มีโฟลเดอร์ที่มี `prod.json` และ video files

### Main Flow:
1. Admin เปิด GUI → Products Tab
2. กด "📁 Import Folder"
3. เลือกโฟลเดอร์
4. System อ่าน `prod.json` via ProdConfig
5. System upsert product ใน database
6. System import video files (skip duplicates)
7. แสดงผลสำเร็จ

### Alternative:
- 4a. ไม่พบ prod.json → แสดง error
- 6a. video ซ้ำ → skip แต่ไม่ error

---

## UC02: Bot Request Order (Just-in-Time)

**Actor:** Bot (Browser Plugin)  
**Precondition:** Bot registered ใน system

### Main Flow:
1. Bot เรียก `POST /api/bot/create-order`
2. API รับ request พร้อม client_code, platform
3. OrderBuilder สร้าง order ใหม่:
   - ดึง ProdConfig จาก ProductVM
   - ดึง PlatformConfig ของ target platform
   - Random select clips (IRON RULES)
   - Shuffle tags (Anti-Detection)
   - Pick random affiliate URL
4. บันทึก Order ใน database
5. Return order data พร้อม job items

### Alternative:
- 3a. ไม่มี clips available → return empty
- 3b. ถูก IRON RULE block → skip clip นั้น

---

## UC03: Bot Get Video

**Actor:** Bot  
**Precondition:** มี job_id จาก order

### Main Flow:
1. Bot เรียก `GET /api/bot/video/{hash}`
2. API ค้นหา video file จาก hash
3. อ่าน video file, encode base64
4. Return video data

---

## UC04: Bot Confirm Job

**Actor:** Bot  
**Precondition:** Bot uploaded video successfully

### Main Flow:
1. Bot เรียก `POST /api/bot/confirm/{job_id}`
2. API update job status = 'confirmed'
3. Return success

---

## UC05: Bot Report Completion

**Actor:** Bot  
**Precondition:** Job completed (success or fail)

### Main Flow:
1. Bot เรียก `POST /api/bot/report`
2. API รับ report data (job_id, status, post_url, error_msg)
3. Update OrderItem status
4. Record PostingHistory (IRON RULE tracking)
5. Return success

---

## UC06: Monitor Dashboard

**Actor:** Admin  
**Precondition:** GUI เปิดอยู่

### Main Flow:
1. Admin เปิด Dashboard Tab
2. GUI แสดง stats cards (Products, Clips, Orders, Clients Online)
3. GUI แสดง Recent Orders table
4. GUI แสดง Connected Clients table
5. Auto-refresh ทุก 5 วินาที
6. EventBus push updates real-time

---

## UC07: Change Theme

**Actor:** Admin  

### Main Flow:
1. Admin เปิด Settings Tab
2. เลือก Theme จาก dropdown
3. ThemeManager apply theme ทันที
4. บันทึกใน config/theme.json

---

## UC08: Add Client

**Actor:** Admin  

### Main Flow:
1. Admin เปิด Clients Tab
2. กด "➕ Add Client"
3. กรอก client_code, name, platform
4. กด OK
5. System สร้าง ClientAccount ใน database
6. Refresh client list
