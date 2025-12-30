# MediaVerse Actors

## Primary Actors

### 1. Admin (Human User)

| Attribute | Value |
|-----------|-------|
| **Type** | Human |
| **Interface** | Desktop GUI (PySide6) |
| **Goals** | จัดการ Products, ติดตาม Orders, ควบคุม Bots |

**Responsibilities:**
- Import product folders
- Monitor dashboard
- Manage clients (bots)
- View order history
- Configure system settings

---

### 2. Bot (Browser Plugin)

| Attribute | Value |
|-----------|-------|
| **Type** | Automated Software Agent |
| **Interface** | REST API (FastAPI) |
| **Goals** | Upload videos to platforms automatically |

**Responsibilities:**
- Request orders from API (Just-in-Time)
- Download video files
- Upload to target platform
- Report success/failure

**Bot States:**
```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Requesting: Request order
    Requesting --> Working: Got jobs
    Requesting --> Idle: No jobs
    Working --> Uploading: Download video
    Uploading --> Confirming: Upload complete
    Confirming --> Reporting: Confirm job
    Reporting --> Working: More jobs
    Reporting --> Idle: All done
```

---

### 3. System (Internal Actor)

| Attribute | Value |
|-----------|-------|
| **Type** | Software System |
| **Interface** | EventBus, MessageOrchestrator |
| **Goals** | Route messages, handle events |

**Components Acting as System:**
- EventBus: Pub/Sub messaging
- MessageOrchestrator: Request/Response validation
- LogOrchestrator: Logging
- ErrorOrchestrator: Error handling

---

## Actor Interactions

```mermaid
graph LR
    subgraph Human
        A[Admin]
    end
    
    subgraph Automated
        B[Bot 1 - YouTube]
        C[Bot 2 - TikTok]
        D[Bot 3 - Shopee]
    end
    
    subgraph System
        E[MediaVerse]
    end
    
    A -->|GUI| E
    B -->|API| E
    C -->|API| E
    D -->|API| E
    
    E -->|Events| A
    E -->|Orders| B
    E -->|Orders| C
    E -->|Orders| D
```

---

## Actor Permissions Matrix

| Action | Admin | Bot | System |
|--------|-------|-----|--------|
| Import Products | ✅ | ❌ | ❌ |
| View Dashboard | ✅ | ❌ | ❌ |
| Create Orders | ❌ | ✅ | ❌ |
| Download Videos | ❌ | ✅ | ❌ |
| Report Status | ❌ | ✅ | ❌ |
| Publish Events | ❌ | ❌ | ✅ |
| Route Messages | ❌ | ❌ | ✅ |
| Add Clients | ✅ | ❌ | ❌ |
| Change Settings | ✅ | ❌ | ❌ |
