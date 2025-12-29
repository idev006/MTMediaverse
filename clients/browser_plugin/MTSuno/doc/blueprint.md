# MTSuno Browser Extension - Blueprint

## Overview
MTSuno is a browser extension for automating song generation and downloading on Suno.ai platform.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Browser Extension (FE)                    │
├──────────────┬──────────────┬──────────────┬────────────────┤
│   App.js     │ Automation   │  ApiClient   │    State       │
│   (UI)       │  Service     │   (API)      │   Manager      │
└──────┬───────┴──────┬───────┴──────┬───────┴────────────────┘
       │              │              │
       │              │              ▼
       │              │      ┌───────────────┐
       │              │      │   Backend     │
       │              │      │  (FastAPI)    │
       │              │      │  Port 8000    │
       │              │      └───────┬───────┘
       │              │              │
       ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Suno.ai Website                         │
│  - Virtual DOM (React)                                       │
│  - clip-row elements                                         │
│  - Audio player                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Components

### 1. App.js (UI Builder)
- Renders floating panel UI
- Handles user settings (delay, download mode)
- Orchestrates automation flow via `startAutomation()`

### 2. AutomationService.js
- `fillForm()` - Fill song creation form
- `clickCreate()` - Trigger generation
- `waitForGeneration()` - Poll until complete
- `downloadLatestSongs()` - Click + download 2 songs
- `collectLatestSongIds()` - Fast ID collection (no click)
- `downloadSongsByIds()` - Download by IDs at end
- `sendToBackend()` - Send data to backend API

### 3. ApiClient.js
- `sendSongEvent()` - POST to `/api/suno/webhook`
- Payload format: `{ events: [{ message: { payload: { audio_base64, image_base64, metadata } } }] }`

### 4. StateManager.js
- Global state management
- UI updates
- Log management

---

## Download Modes

| Mode | Behavior |
|------|----------|
| **Manual** | No auto-download, send metadata only |
| **Download Each 2 Songs** | After each generation → click + download 2 songs immediately |
| **Download All at End** | Fast loop (collect IDs only) → download all at end |

---

## Flow: Download Each 2 Songs

```
Loop for each CSV row:
  1. fillForm(title, style, lyrics)
  2. clickCreate()
  3. waitForGeneration() - poll until spinner gone
  4. sendToBackend(songData) - send metadata
  5. downloadLatestSongs(2):
     - Find top 2 clip-rows
     - Click each to capture audio URL
     - Download each to backend
  6. Random delay (anti-bot)
```

## Flow: Download All at End

```
Loop for each CSV row:
  1. fillForm → clickCreate → waitForGeneration
  2. collectLatestSongIds(2) - fast, no click
  3. Push IDs to collection
  4. Random delay

After loop:
  1. Wait 5 seconds (UI stabilize)
  2. downloadSongsByIds(collectedIds):
     - Find each row by ID
     - Click to capture audio URL
     - Download to backend
```

---

## Backend API

### Endpoint: POST /api/suno/webhook

**Request:**
```json
{
  "events": [{
    "type": "message",
    "message": {
      "type": "audio",
      "id": "song-uuid",
      "payload": {
        "audio_base64": "data:audio/mpeg;base64,...",
        "image_base64": "data:image/jpeg;base64,...",
        "metadata": {
          "title": "Song Title",
          "tags": "pop, electronic, ..."
        }
      }
    }
  }]
}
```

**Response:**
```json
{
  "message": "Batch processed",
  "results": [{ "id": "...", "status": "success", "path": "..." }]
}
```

---

## File Structure

```
MTSuno/
├── manifest.json        # Extension config
├── src/
│   ├── App.js           # UI + orchestration
│   ├── AutomationService.js  # Core automation
│   ├── ApiClient.js     # Backend communication
│   ├── StateManager.js  # State management
│   └── styles.css       # UI styles
├── doc/
│   ├── blueprint.md     # This file
│   └── lessons_learned.md
└── mt_suno.csv          # Sample CSV input
```

---

## Settings Persistence

Settings saved to `localStorage` under key `mts_suno_settings`:
```json
{
  "delay": {
    "itemDelayMin": 3,
    "itemDelayMax": 8,
    "stepDelayMin": 500,
    "stepDelayMax": 1500
  },
  "downloadMode": "each"
}
```
