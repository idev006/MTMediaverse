# prod.json Schema v2.0

## โครงสร้างหลัก

```
prod.json
├── schema_version: "2.0"
├── prod_detail: { ... }          # ข้อมูลสินค้า
└── platforms: {                  # ตั้งค่าแยกตาม platform
        youtube: { ... }
        tiktok: { ... }
        facebook: { ... }
        shopee: { ... }
        lazada: { ... }
    }
```

---

## prod_detail

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `prod_code` | string | ✅ | รหัสสินค้า (unique) |
| `prod_name` | string | ✅ | ชื่อสินค้า |
| `prod_short_descr` | string | ❌ | คำอธิบายสั้น |
| `prod_long_descr` | string | ❌ | คำอธิบายยาว (รองรับ markdown) |
| `prod_tags` | array | ❌ | แท็กสินค้า |
| `category_id` | int | ❌ | หมวดหมู่ (YouTube) |

---

## platforms.{platform}

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `enabled` | bool | ✅ | เปิด/ปิด platform นี้ |
| `platform_type` | string | ❌ | ประเภท: shorts, video, reels |
| `privacy` | string | ❌ | public, unlisted, private |
| `schedule` | object | ❌ | ตารางเวลาโพสต์ตามวัน |
| `props` | object | ❌ | ตั้งค่าเฉพาะ platform |
| `playlist` | object | ❌ | (YouTube) ตั้งค่า playlist |
| `aff_urls` | array | ❌ | Affiliate links |

---

## schedule format

```json
{
    "sun": ["10:00", "14:00"],
    "mon": ["10:00", "14:00"],
    "tue": ["10:00"],
    ...
}
```

---

## aff_urls format

```json
{
    "label": "ร้านค้า ABC",
    "url": "https://...",
    "aff_prod_code": "12345",  // optional
    "is_primary": true
}
```

---

## Platform-specific props

### YouTube
```json
{
    "made_for_kids": false,
    "notify_subscribers": true,
    "embeddable": true
}
```

### TikTok
```json
{
    "allow_comments": true,
    "allow_duet": false,
    "allow_stitch": false
}
```

### Facebook
```json
{
    "audience": "public"
}
```

### Shopee
```json
{
    "shop_id": "123456"
}
```

---

## ตัวอย่างไฟล์

ดู: `app/data/products/new_design_prod.json`
