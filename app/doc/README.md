# MediaVerse Documentation Index

## Quick Start

> **IMPORTANT:** ใช้ Python จาก venv เท่านั้น: `D:\dev\MTMediaverse\Scripts\python.exe`

```bash
# 1. Install dependencies
D:\dev\MTMediaverse\Scripts\pip.exe install -r requirements.txt

# 2. Initialize database
D:\dev\MTMediaverse\Scripts\python.exe -c "from app.core.database import init_database; init_database()"

# 3. Run GUI
D:\dev\MTMediaverse\Scripts\python.exe run_gui.py
# or
run_gui.bat

# 4. Run API Server (for bots)
D:\dev\MTMediaverse\Scripts\python.exe run_api.py

# 5. Run Tests
D:\dev\MTMediaverse\Scripts\pytest.exe tests/ -v
```

---

## Environment Paths

| Path | Description |
|------|-------------|
| `D:\dev\MTMediaverse\Scripts\python.exe` | Python (venv) |
| `D:\dev\MTMediaverse\Scripts\pip.exe` | Pip (venv) |
| `D:\dev\MTMediaverse\Scripts\pytest.exe` | Pytest (venv) |
| `D:\libs\ffmpeg\bin` | FFmpeg binaries |

---

## Documentation Files

| File | Description |
|------|-------------|
| [system_design.md](system_design.md) | Architecture, Classes, Design Patterns |
| [actors.md](actors.md) | Actors, Permissions, Interactions |
| [use_cases.md](use_cases.md) | Use Case descriptions |
| [workflows.md](workflows.md) | Flowcharts and process diagrams |
| [sequence_diagrams.md](sequence_diagrams.md) | Detailed sequence diagrams |
| [prod_json_schema_v2.md](prod_json_schema_v2.md) | prod.json file format |

---

## Directory Structure

```
MTMediaverse/
├── app/
│   ├── api/              # FastAPI endpoints
│   │   └── bot_api.py
│   ├── core/             # Core infrastructure
│   │   ├── database.py
│   │   ├── event_bus.py
│   │   ├── prod_config.py
│   │   ├── message_orchestrator.py
│   │   ├── log_orchestrator.py
│   │   ├── error_orchestrator.py
│   │   └── path_manager.py
│   ├── gui/              # Desktop GUI
│   │   ├── main_window.py
│   │   ├── store.py
│   │   ├── theme_manager.py
│   │   └── components/
│   │       ├── dashboard_panel.py
│   │       ├── products_panel.py
│   │       ├── orders_panel.py
│   │       ├── clients_panel.py
│   │       └── settings_panel.py
│   ├── viewmodels/       # Business logic
│   │   ├── product_vm.py
│   │   ├── order_vm.py
│   │   ├── media_vm.py
│   │   └── order_builder.py
│   ├── platforms/        # Platform-specific
│   │   ├── base_manager.py
│   │   ├── youtube_manager.py
│   │   ├── tiktok_manager.py
│   │   └── facebook_manager.py
│   ├── data/             # Data files
│   │   ├── products/     # prod.json files
│   │   └── media/        # Video files
│   └── doc/              # Documentation
│
├── tests/                # Unit & Integration Tests
│   ├── __init__.py
│   ├── conftest.py       # Pytest fixtures
│   ├── test_prod_config.py
│   ├── test_product_vm.py
│   ├── test_order_builder.py
│   └── test_api.py
│
├── build/                # Build Scripts
│   ├── build.py          # Main build script
│   ├── build.spec        # PyInstaller spec
│   └── pyarmor_config.py # PyArmor settings
│
├── dist/                 # Build Output (generated)
│
├── config/               # Configuration
│   ├── config.json
│   └── theme.json
│
├── logs/                 # Log files
├── requirements.txt
├── run_gui.py
├── run_api.py
└── run_gui.bat
```

---

## Key Concepts

### IRON RULES (OrderBuilder)
1. **RULE #1:** ห้าม clip ซ้ำกับ platform เดียวกัน
2. **RULE #2:** ห้าม clip ซ้ำใน order เดียวกัน

### Anti-Bot-Detection
- Shuffle tags order
- Random affiliate link selection (70% primary)
- Vary descriptions slightly
- Random emoji suffix

### Just-in-Time Orders
Bot ขอ order ตอนพร้อมทำงาน ไม่ queue ล่วงหน้า

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/stats` | Get statistics |
| POST | `/api/bot/create-order` | Bot requests new order |
| GET | `/api/bot/video/{hash}` | Bot downloads video |
| POST | `/api/bot/confirm/{job_id}` | Bot confirms job |
| POST | `/api/bot/report` | Bot reports completion |

---

## Configuration

### config/config.json
```json
{
  "database_path": "data/mediaverse.db",
  "media_storage_path": "app/data/media",
  "products_storage_path": "app/data/products"
}
```

### config/theme.json
```json
{
  "current_theme": "dark"
}
```

---

## Contact

Project: MediaVerse  
Repository: https://github.com/idev006/MTMediaverse
