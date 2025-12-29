# MTSuno - Lessons Learned

## 📅 Date: 2025-12-28

---

## 1. Virtual DOM Challenges

### Problem
Suno.ai uses React with virtual scrolling. Songs not visible in viewport may not exist in DOM.

### Solution
- Use `loadAndCollectAllSongs()` with scroll-to-bottom approach
- Wait for DOM updates after scrolling
- Use `clip-row` selector with fallback: `[data-testid="clip-row"], .clip-row`

---

## 2. Audio URL Capture

### Problem
Audio URLs are not directly available in DOM. They load dynamically when song is clicked/played.

### Solution
- Click on song image container to trigger audio loading
- Wait 2 seconds for audio element to load
- Capture URL from `<audio>` element's `src` attribute
- Fallback: construct URL as `https://cdn2.suno.ai/{songId}.mp3`

---

## 3. Download Mode Design

### User Requirements
1. **Manual** - User controls everything
2. **Each 2 Songs** - Download immediately after each generation
3. **All at End** - Fast generation loop, download at end

### Key Insight
"Download all at end" should NOT re-scan entire history. Instead:
- Collect song IDs during loop (fast, no click)
- Download only collected IDs at end

### Implementation
- `collectLatestSongIds()` - Fast ID collection (no click)
- `downloadSongsByIds()` - Download by specific IDs

---

## 4. API Payload Format

### Problem
Initial payload format didn't match backend schema, causing HTTP 422 errors.

### Backend Expected Format
```json
{
  "events": [{
    "type": "message",
    "message": {
      "type": "audio",
      "id": "song-id",
      "payload": {
        "audio_base64": "...",
        "image_base64": "...",
        "metadata": { "title": "...", "tags": "..." }
      }
    }
  }]
}
```

### Lesson
Always verify backend schema before implementing frontend API calls.

---

## 5. Zero-Byte File Validation

### Problem
Sometimes audio files download as 0 bytes due to network issues or timing.

### Solution
- Frontend: Retry up to 3 times with 2-second delay
- Backend: Validate decoded file size > 0 before saving
- Return error if file is empty

---

## 6. Settings Persistence

### Problem
Settings reset on page reload.

### Solution
- Save to `localStorage` on every change
- Load settings on extension initialization
- Key: `mts_suno_settings`

---

## 7. Anti-Bot Delays

### Strategy
- Random delays between operations (configurable min/max)
- Item delay: Between CSV rows (3-8 seconds default)
- Step delay: Between clicks/downloads (500-1500ms default)

---

## 8. Code Organization

### Best Practices Learned
1. **Single Responsibility**: Each method does one thing
2. **Wrapper Methods**: `downloadSingleSong()` wraps `sendToBackend()` for clarity
3. **Consolidate Logic**: Use one API method instead of duplicating send logic
4. **Fast vs Thorough**: Separate fast collection (IDs only) from thorough extraction (with click)

---

## 9. Error Handling

### Patterns Used
- Try-catch in loops (don't stop entire batch on one failure)
- Retry logic for network operations
- Status updates per item (processing/completed/error)
- Detailed logging for debugging

---

## 10. DOM Selector Stability

### Problem
Suno may change class names or data attributes.

### Solution
- Use multiple selectors with fallbacks
- Prefer `data-testid` when available
- Use semantic patterns like `a[href*="/song/"]`

---

## Summary Checklist

✅ Always wait for DOM updates after actions  
✅ Click to trigger lazy-loaded content  
✅ Validate file sizes before saving  
✅ Use retry logic for network operations  
✅ Persist user settings  
✅ Match backend API schema exactly  
✅ Separate fast collection from downloading  
✅ Use random delays to appear human-like  
✅ Use `scrollIntoView` for Virtual List elements  
✅ Detect end-of-list indicators (Reset filters button)  

---

## 11. Virtual List - Deep Dive (2025-12-28)

### Problem
Suno uses Virtual List that ONLY renders rows visible in viewport. When scrolling by pixels (`scrollTop += N`), elements scroll out of view and get **removed from DOM** before they can be clicked.

**Symptoms:**
- Expected 96 songs, only got 15-21
- Works when user manually scrolls along with automation
- Log shows: `No new songs after 5 scroll attempts`

### Root Cause
- Virtual List recycles DOM elements
- Elements outside viewport don't exist in DOM
- Scroll by pixels → element disappears before click

### Solution
**Use `scrollIntoView` for each row individually:**
```javascript
for (const wrapper of rowWrappers) {
    wrapper.scrollIntoView({ behavior: 'instant', block: 'center' });
    await this.sleep(300); // Wait for render
    // Now click and collect data
}
```

**Key Changes:**
| Before | After |
|--------|-------|
| `scroller.scrollTop += 500` | `row.scrollIntoView()` |
| Scroll then query | Query, scroll to row, then click |
| 5 attempt tolerance | 15 attempt tolerance |

---

## 12. End-of-List Indicator Detection

### Problem
No reliable way to know when scroll reached the end of song list.

### Discovery
At the bottom of Suno's song list, there's a **"Reset filters"** button:
```html
<button><span>Reset filters</span></button>
```

### Solution
Detect this button to know we've reached the end:
```javascript
const resetFiltersBtn = document.querySelector('button span');
const isEndOfList = resetFiltersBtn?.textContent?.includes('Reset filters');
if (isEndOfList) {
    console.log('Reached end of list!');
    maxAttempts = 3; // Stop faster
}
```

### Benefit
- Faster completion (stop after 3 attempts instead of 15)
- Definitive end detection
- Clear log message for debugging

---

## 13. Browser Tab Throttling

### Problem
When browser tab is not active (user switches to another app/tab), JavaScript execution is **throttled** or **paused**.

### Symptoms
- Automation stops progressing when tab is in background
- User must "scroll along" with automation manually

### Workaround
- **Keep Suno tab in active window** during automation
- Use separate browser window (not just tab) if need to multitask
- Consider: Pop out tab to new window → arrange side by side

### Note
This is a browser-level limitation, not easily fixable in content scripts.
