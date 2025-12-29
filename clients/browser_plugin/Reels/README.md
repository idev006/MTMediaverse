# Facebook Reels Uploader Plugin

## Implementation Status
- **Base Structure**: Created following `Tiktok3` pattern.
- **Step 2 Logic**: Implemented video injection and upload trigger.
- **Step 1 Logic**: Implemented clicking the "Reel" button to open popup.

## Files
- `manifest.json`: Extension configuration.
- `content.js`: Main entry point.
- `src/PageHandler.js`: Contains selectors from `webpart.txt`.
- `src/AutomationEngine.js`: Logic to run flows.

## How to use
1. Load this folder as an Unpacked Extension in Chrome.
2. Go to Facebook (e.g. `https://www.facebook.com/profile.php?id=61584964285304&sk=reels_tab`).
3. **Test Full Flow**: Click the green "Test Full Flow (Step 1->2)" button. This will click "Reel" -> Wait -> Inject Video.
4. **Test Step 2 Only**: Manually open "Create Reel", then click "Test Step 2: Inject Video".
4. Ensure the backend is running if fetching videos from localhost.
