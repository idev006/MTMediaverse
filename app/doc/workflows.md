# MediaVerse Workflows

## Workflow 1: Product Import

```mermaid
flowchart TD
    A[Start] --> B[Select Folder]
    B --> C{prod.json exists?}
    C -->|No| D[Show Error]
    C -->|Yes| E[ProdConfig.from_file]
    E --> F[ProductVM.upsert_product]
    F --> G{Product exists?}
    G -->|Yes| H[Update Product]
    G -->|No| I[Create Product]
    H --> J[Import Videos]
    I --> J
    J --> K{Video duplicate?}
    K -->|Yes| L[Skip]
    K -->|No| M[Import]
    L --> N{More videos?}
    M --> N
    N -->|Yes| J
    N -->|No| O[Copy prod.json to storage]
    O --> P[Show Success]
    P --> Q[End]
    D --> Q
```

---

## Workflow 2: Bot Order Flow

```mermaid
flowchart TD
    A[Bot Start] --> B[POST /create-order]
    B --> C[OrderBuilder.create_order]
    C --> D[Get available clips RANDOM]
    D --> E{Clips found?}
    E -->|No| F[Return empty]
    E -->|Yes| G[For each clip]
    G --> H[Get ProdConfig]
    H --> I[Get PlatformConfig]
    I --> J[Shuffle tags]
    J --> K[Pick random affiliate]
    K --> L[Vary description]
    L --> M[Create OrderItem]
    M --> N{More clips?}
    N -->|Yes| G
    N -->|No| O[Commit Order]
    O --> P[Return Order+Items]
    
    P --> Q[Bot: GET /video/hash]
    Q --> R[Return base64 video]
    R --> S[Bot: Upload to Platform]
    S --> T{Success?}
    T -->|Yes| U[POST /confirm]
    T -->|No| V[POST /report error]
    U --> W[POST /report success]
    W --> X[Record PostingHistory]
    V --> X
    X --> Y[End]
    F --> Y
```

---

## Workflow 3: Real-time Dashboard Update

```mermaid
sequenceDiagram
    participant GUI as Dashboard
    participant EB as EventBus
    participant QT as QtEventBridge
    participant OB as OrderBuilder
    participant DB as Database
    
    OB->>DB: Create Order
    OB->>EB: publish("order/created", data)
    EB->>QT: route to Qt thread
    QT->>GUI: emit order_created signal
    GUI->>DB: Refresh stats
    GUI->>GUI: Update tables
```

---

## Workflow 4: Platform Payload Preparation

```mermaid
flowchart LR
    A[ProdConfig] --> B[PlatformConfig]
    B --> C{Platform?}
    C -->|youtube| D[YouTubeManager]
    C -->|tiktok| E[TikTokManager]
    C -->|facebook| F[FacebookManager]
    C -->|shopee| G[ShopeeManager]
    
    D --> H[PreparedPayload]
    E --> H
    F --> H
    G --> H
    
    H --> I[Bot API Response]
```

---

## Workflow 5: IRON RULES Check

```mermaid
flowchart TD
    A[Select Clip] --> B{Posted to this platform before?}
    B -->|Yes| C[IRON RULE #1 BLOCK]
    B -->|No| D{Already in this order?}
    D -->|Yes| E[IRON RULE #2 BLOCK]
    D -->|No| F[ALLOW - Add to order]
    C --> G[Skip clip]
    E --> G
    G --> H[Try next clip]
```
