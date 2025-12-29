# System Architecture V6: Media Library & Orchestrator

## 1. Core Concept
The system acts as a **Central Media Hub** that manages a library of video assets and dispenses them to **Distribution Bots** (Clients) via a unified "Order" system.

## 2. Key Components
### A. The Brain (Backend)
- **MediaVM:** Handles importing video files, calculating SHA256 hashes to prevent duplicates, and organizing media by Product/Category.
- **OrderVM:** Managing the "Billing" process. It picks available media, assigns it to a specific platform (YouTube, TikTok, etc.), and generates a specific `posting_config` JSON.
- **Message Orchestrator:** The Central Nervous System. It acts as a singleton hub that routes traffic between the API (Webhook) and the GUI (Monitor). It uses the **Message Envelope** pattern.

### B. The Experts (Platform Managers)
Stategy Pattern to handle platform-specific rules.
- **`BasePlatformManager`**: Interface.
- **`YoutubeManager`**: Generates Titles, Descriptions (w/ Affiliate Links), Tags, Privacy settings.
- **`TiktokManager`**: Generates Captions (w/ Hashtags), Duet/Stitch settings.
- **`ReelsManager`**: Handles Share-to-Feed logic.

### C. The Interface
- **API Stub (`/api/webhook`):** Single entry point for all bots.
- **GUI (Desktop):**
    - **Library Tab:** Manage Assets.
    - **Orders Tab:** Manual Order Generation.
    - **Monitor Tab:** Real-time visibility into the Orchestrator.

## 3. Workflow (Just-in-Time)
1.  **Bot** comes online and sends `request_job` event.
2.  **Orchestrator** checks DB for pending orders.
3.  **If no orders:** System triggers **Auto-Generate** logic (OrderVM creates 1 set based on defaults).
4.  **System** returns `job_assignment` message with a Config Payload (Title, Tags, etc.).
5.  **Bot** uploads -> Sends `report_job` (Done/Fail).
6.  **System** marks as Done -> Adds to `posting_history` (Duplicate Guard).
