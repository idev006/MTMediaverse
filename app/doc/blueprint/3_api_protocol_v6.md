# API Protocol V6: Message Envelope

Inspired by **LINE Messaging API**, all communication is wrapped in a standard JSON envelope.

**Base URL:** `POST /api/webhook`

## 1. Request Structure (Bot -> System)
```json
{
  "client_code": "BOT-001",
  "events": [
    {
      "type": "request_job",
      "replyToken": "rt_generated_by_bot",
      "timestamp": 1234567890,
      "payload": {
          "limit": 1
      }
    }
  ]
}
```

## 2. Response Structure (System -> Bot)
```json
{
  "replyToken": "rt_generated_by_bot",
  "messages": [
    {
      "type": "job_assignment", 
      "job_id": 501,
      "media_url": "http://server/api/video/hash123", # or file path
      "payload": {
          "title": "Super Product Review",
          "description": "Buy here! http://aff...",
          "tags": ["tech", "review"],
          "privacy": "public"
      }
    }
  ]
}
```
*Note: If no job is available, `messages` array may be empty or contain a text message ("Standby").*

## 3. Reporting Results
**Request:**
```json
{
  "client_code": "BOT-001",
  "events": [
    {
      "type": "report_job",
      "replyToken": "rt_report_1",
      "job_id": 501,
      "status": "done", // or "failed"
      "log": "Uploaded successfully at url..."
    }
  ]
}
```

## 4. Other Events
- **`heartbeat`**: Bot pings to say "I'm alive". System updates `last_seen`.
- **`log`**: Bot sends debug logs. System saves to text file/monitor.
