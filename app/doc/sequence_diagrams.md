# MediaVerse Sequence Diagrams

## Sequence 1: Product Import

```mermaid
sequenceDiagram
    actor Admin
    participant GUI as ProductsPanel
    participant PVM as ProductVM
    participant PC as ProdConfig
    participant MVM as MediaVM
    participant DB as Database
    participant EB as EventBus

    Admin->>GUI: Click "Import Folder"
    Admin->>GUI: Select folder path
    GUI->>PVM: import_product_folder(path)
    
    PVM->>PVM: read_prod_json(path)
    PVM->>PC: ProdConfig.from_file(prod.json)
    PC-->>PVM: ProdConfig object
    
    PVM->>DB: Check product exists (by sku)
    alt Product exists
        PVM->>DB: UPDATE Product
    else New product
        PVM->>DB: INSERT Product
    end
    
    PVM->>MVM: import_folder(path, product_id)
    loop Each video file
        MVM->>MVM: Calculate SHA256 hash
        MVM->>DB: Check hash exists
        alt Duplicate
            MVM->>MVM: Skip
        else New
            MVM->>DB: INSERT MediaAsset
        end
    end
    MVM-->>PVM: FolderImportResult
    
    PVM->>PVM: copy_prod_json_to_storage()
    PVM->>EB: publish("product/created" or "product/updated")
    PVM-->>GUI: ProductImportResult
    
    GUI->>Admin: Show success message
```

---

## Sequence 2: Bot Create Order

```mermaid
sequenceDiagram
    participant Bot as Browser Bot
    participant API as FastAPI
    participant OB as OrderBuilder
    participant PVM as ProductVM
    participant PC as ProdConfig
    participant PM as PlatformManager
    participant DB as Database

    Bot->>API: POST /api/bot/create-order
    Note over Bot,API: {client_code, platform, quantity}
    
    API->>OB: create_order(client_code, platform, qty)
    OB->>DB: Get ClientAccount
    OB->>DB: Get available clips (RANDOM)
    
    loop Each clip
        OB->>PVM: get_prod_config(sku)
        PVM->>PC: ProdConfig.from_file()
        PC-->>PVM: ProdConfig
        PVM-->>OB: ProdConfig
        
        OB->>PVM: get_platform_config(sku, platform)
        PVM->>PC: get_platform(platform)
        PC-->>PVM: PlatformConfig
        PVM-->>OB: PlatformConfig
        
        OB->>OB: shuffle_tags()
        OB->>OB: pick_random_affiliate()
        OB->>OB: vary_description()
        
        OB->>DB: INSERT OrderItem
    end
    
    OB->>DB: COMMIT Order
    OB-->>API: CreatedOrder
    API-->>Bot: JSON Response
```

---

## Sequence 3: Bot Complete Job

```mermaid
sequenceDiagram
    participant Bot as Browser Bot
    participant API as FastAPI
    participant DB as Database
    participant EB as EventBus

    Note over Bot: Upload video complete
    
    Bot->>API: POST /api/bot/confirm/{job_id}
    API->>DB: UPDATE OrderItem.status = 'confirmed'
    API-->>Bot: {success: true}
    
    Note over Bot: Get post URL from platform
    
    Bot->>API: POST /api/bot/report
    Note over Bot,API: {job_id, status, post_url}
    
    API->>DB: UPDATE OrderItem.status = 'done'
    API->>DB: INSERT PostingHistory
    Note over DB: Records: client_id, media_id, platform, post_url
    Note over DB: Prevents future duplicate (IRON RULE)
    
    API->>EB: publish("order/item-completed")
    API-->>Bot: {success: true}
```

---

## Sequence 4: Real-time GUI Update

```mermaid
sequenceDiagram
    participant OB as OrderBuilder
    participant EB as EventBus
    participant QT as QtEventBridge
    participant GUI as DashboardPanel
    participant DB as Database

    OB->>EB: publish("order/created", payload)
    EB->>EB: Find subscribers
    EB->>QT: Deliver message
    
    Note over QT: Route to Qt main thread
    QT->>QT: emit order_created signal
    
    QT->>GUI: Signal received
    GUI->>DB: Query stats
    GUI->>GUI: Update cards
    GUI->>GUI: Refresh OrderTable
```

---

## Sequence 5: Theme Change

```mermaid
sequenceDiagram
    actor Admin
    participant SP as SettingsPanel
    participant TM as ThemeManager
    participant MW as MainWindow
    participant FS as FileSystem

    Admin->>SP: Select theme from dropdown
    SP->>TM: set_theme("ocean")
    TM->>TM: Update current_theme
    TM->>FS: Save to config/theme.json
    TM->>SP: notify callbacks
    SP->>MW: apply_theme()
    MW->>TM: generate_stylesheet()
    TM-->>MW: CSS stylesheet
    MW->>MW: setStyleSheet(css)
    MW->>MW: Update status bar
```
