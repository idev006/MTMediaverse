# Database Schema V6 (mt_media.db)

## 1. Concept
- **Strict Duplicate Prevention:** `posting_history` table ensures a Client never posts the same Media Asset to the same Platform twice.
- **JSON Flexibility:** `posting_config` stores all platform-specific metadata, allowing the schema to remain clean.

## 2. Table Structure

### Core Assets
```sql
CREATE TABLE categories (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE
);

CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    category_id INTEGER,
    sku TEXT UNIQUE,
    name TEXT,
    description TEXT,
    affiliate_link TEXT,
    tags TEXT, -- JSON Array
    price REAL
);

CREATE TABLE media_assets (
    id INTEGER PRIMARY KEY,
    product_id INTEGER,
    filename TEXT,
    file_path TEXT,
    file_hash TEXT UNIQUE, -- SHA256 (Prevent Duplicate Files)
    duration INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Order System
```sql
CREATE TABLE client_accounts (
    id INTEGER PRIMARY KEY,
    client_code TEXT UNIQUE, -- e.g. "BOT-001"
    name TEXT,
    platform TEXT, -- 'youtube', 'tiktok'
    settings TEXT -- JSON
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    client_id INTEGER,
    target_platform TEXT, -- 'youtube', 'tiktok'
    status TEXT, -- 'pending', 'completed'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE order_items (
    id INTEGER PRIMARY KEY,
    order_id INTEGER,
    media_id INTEGER,
    status TEXT, -- 'new', 'processing', 'done', 'failed'
    posting_config TEXT, -- JSON Payload (Title, Caption, etc.)
    error_log TEXT,
    attempt_count INTEGER DEFAULT 0
);
```

### Safety Layer
```sql
CREATE TABLE posting_history (
    id INTEGER PRIMARY KEY,
    client_id INTEGER,
    media_id INTEGER,
    platform TEXT,
    posted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(client_id, media_id, platform) -- THE COMPOSITE KEY GUARD
);
```
