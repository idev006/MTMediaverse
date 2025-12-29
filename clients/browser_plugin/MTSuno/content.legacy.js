/**
 * MTSuno Automation Plugin
 * Handles CSV processing, Suno interaction, and data extraction.
 */

class SunoAutomation {
    constructor() {
        this.statusLog = [];
        this.isProcessing = false;
        this.processedCount = 0;
        this.apiUrl = "http://localhost:8000/api/suno/webhook";

        // Selectors based on analysis
        this.selectors = {
            lyricsTextarea: 'textarea[placeholder*="Write some lyrics"], textarea[placeholder*="Enter your lyrics"]',
            styleTextarea: 'textarea[placeholder*="kwaito"], textarea[placeholder*="Enter style of music"]',
            titleInput: 'input[placeholder="Song Title (Optional)"]',
            createButton: 'button[data-testid="create-button"], button:contains("Create")', // Need to verify specific text or ID
            clipRow: 'div[data-testid="clip-row"], .clip-row',
            publishContainer: 'div.css-1d74pf0', // For injection
        };

        this.initUI();
    }

    initUI() {
        const panel = document.createElement('div');
        panel.id = 'mt-suno-panel';
        panel.style.cssText = `
      position: fixed;
      top: 100px;
      right: 20px;
      width: 300px;
      background: #1a1a1a;
      color: white;
      border: 1px solid #333;
      padding: 15px;
      z-index: 9999;
      border-radius: 8px;
      font-family: sans-serif;
      box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    `;

        panel.innerHTML = `
      <h3 style="margin: 0 0 10px 0; font-size: 16px; font-weight: bold;">MTSuno Automation</h3>
      <div style="margin-bottom: 10px;">
        <label style="display: block; font-size: 12px; margin-bottom: 5px;">Upload CSV:</label>
        <input type="file" id="mt-csv-input" accept=".csv" style="width: 100%; font-size: 12px;">
      </div>
      <button id="mt-start-btn" style="
        width: 100%; 
        padding: 8px; 
        background: #007bff; 
        color: white; 
        border: none; 
        border-radius: 4px; 
        cursor: pointer;
        opacity: 0.5; 
        pointer-events: none;
      ">Start Automation</button>
      <div id="mt-status-log" style="
        margin-top: 10px;
        height: 150px;
        overflow-y: auto;
        background: #000;
        padding: 5px;
        font-size: 11px;
        font-family: monospace;
        border: 1px solid #444;
      "></div>
    `;

        document.body.appendChild(panel);

        // Event Listeners
        const fileInput = panel.querySelector('#mt-csv-input');
        const startBtn = panel.querySelector('#mt-start-btn');

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                startBtn.style.opacity = '1';
                startBtn.style.pointerEvents = 'auto';
                this.log("CSV File Selected: " + e.target.files[0].name);
            }
        });

        startBtn.addEventListener('click', () => {
            const file = fileInput.files[0];
            if (file) {
                this.processCSV(file);
            }
        });

        this.log("MTSuno Panel Initialized (Right Aligned)");
    }

    log(msg) {
        const logDiv = document.querySelector('#mt-status-log');
        const entry = document.createElement('div');
        entry.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
        entry.style.borderBottom = '1px solid #222';
        logDiv.appendChild(entry);
        logDiv.scrollTop = logDiv.scrollHeight;
        console.log("[MTSuno]", msg);
    }

    async processCSV(file) {
        this.isProcessing = true;
        this.log("Reading CSV...");

        const reader = new FileReader();
        reader.onload = async (e) => {
            const text = e.target.result;
            const rows = this.parseCSV(text);
            this.log(`Found ${rows.length} rows. Starting loop...`);

            for (let i = 0; i < rows.length; i++) {
                this.log(`--- Processing Row ${i + 1}/${rows.length} ---`);
                await this.processRow(rows[i]);
                // Wait between batches if needed
                await this.sleep(2000);
            }
            this.log("All rows processed!");
            this.isProcessing = false;
        };
        reader.readAsText(file);
    }

    parseCSV(text) {
        // Basic CSV Parser handling quotes
        const rows = [];
        let currentRow = [];
        let currentVal = '';
        let inQuotes = false;

        for (let i = 0; i < text.length; i++) {
            const char = text[i];
            if (char === '"') {
                inQuotes = !inQuotes;
            } else if (char === ',' && !inQuotes) {
                currentRow.push(currentVal.trim());
                currentVal = '';
            } else if (char === '\n' && !inQuotes) {
                currentRow.push(currentVal.trim());
                rows.push(currentRow);
                currentRow = [];
                currentVal = '';
            } else {
                currentVal += char;
            }
        }
        if (currentVal) currentRow.push(currentVal.trim());
        if (currentRow.length > 0) rows.push(currentRow);

        // Headers
        const headers = rows[0].map(h => h.toLowerCase().replace(/['"]/g, ''));
        const data = [];

        for (let i = 1; i < rows.length; i++) {
            const rowData = rows[i];
            if (rowData.length === headers.length) {
                const obj = {};
                headers.forEach((h, idx) => obj[h] = rowData[idx].replace(/^"|"$/g, ''));
                data.push(obj);
            }
        }
        return data;
    }

    async processRow(row) {
        // 1. Fill Inputs using User's Mapping
        // id,fashion,mood,lyrics,style,descr

        const title = row['descr'] || row['title'] || '';
        const style = row['style'] || '';
        const lyrics = row['lyrics'] || '';
        const isInstrumental = !lyrics; // Logic: Empty lyrics = Instrumental

        this.log(`Setting: Title="${title}", Style="${style}"`);

        // Select Elements
        const titleInput = document.querySelector(this.selectors.titleInput);
        if (!titleInput) { this.log("Error: Title input not found"); return; }

        // React input setter hack
        this.setNativeValue(titleInput, title);

        // Find Style and Lyrics areas
        const textareas = document.querySelectorAll('textarea');
        let styleArea, lyricsArea;

        textareas.forEach(ta => {
            const ph = ta.placeholder.toLowerCase();
            if (ph.includes('style') || ph.includes('tone')) styleArea = ta;
            if (ph.includes('lyrics') || ph.includes('prompt')) lyricsArea = ta;
        });

        if (styleArea && style) this.setNativeValue(styleArea, style);
        if (lyricsArea) {
            if (lyrics) {
                this.setNativeValue(lyricsArea, lyrics);
            } else {
                // Handle Instrumental Toggle if needed
                this.setNativeValue(lyricsArea, "");
                this.log("Info: Instrumental song (No lyrics provided)");

                // Try to click Instrumental button if available
                const buttons = Array.from(document.querySelectorAll('button'));
                const instrumentalBtn = buttons.find(b => b.textContent.includes('Instrumental'));
                if (instrumentalBtn) {
                    // Check if it's already active/inactive? 
                    // Difficult to know state without inspecting classes, but clicking might toggle
                    // For now, assume user might set it manually or accept default
                }
            }
        }

        // 2. Click Create
        // const createBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Create');
        // Using a more generic finder for "Create" button
        const createBtn = await this.waitForElement("button", "Create", true);

        if (createBtn) {
            // Count existing clips to detect new ones
            const initialCount = document.querySelectorAll(this.selectors.clipRow).length;

            createBtn.click();
            this.log("Clicked Create. Waiting for generation...");

            // 3. Poll for Completion (Wait for 2 new clips to be 'Ready')
            await this.waitForGeneration(initialCount + 2);

            // 4. Extract and Send
            await this.extractAndSend(2); // Send the top 2 items
        } else {
            this.log("Error: Create button not found");
        }
    }

    setNativeValue(element, value) {
        const valueSetter = Object.getOwnPropertyDescriptor(element, 'value').set;
        const prototype = Object.getPrototypeOf(element);
        const prototypeValueSetter = Object.getOwnPropertyDescriptor(prototype, 'value').set;

        if (valueSetter && valueSetter !== prototypeValueSetter) {
            prototypeValueSetter.call(element, value);
        } else {
            valueSetter.call(element, value);
        }

        element.dispatchEvent(new Event('input', { bubbles: true }));
    }

    async waitForElement(tag, text, exact = false) {
        // Simple finder
        return new Promise(resolve => {
            const check = () => {
                const els = Array.from(document.querySelectorAll(tag));
                const found = els.find(el => exact ? el.textContent.trim() === text : el.textContent.includes(text));
                if (found) resolve(found);
                else setTimeout(check, 500);
            };
            check();
        });
    }

    async waitForGeneration(targetCount) {
        // Wait for list length to increase
        // Then wait for "Generating" status to disappear from the top 2 items

        return new Promise(resolve => {
            const check = () => {
                const rows = document.querySelectorAll(this.selectors.clipRow);
                if (rows.length >= targetCount) {
                    // Check status of top 2
                    // Ideally check for play button or absence of spinner
                    // Assuming top 2 are the new ones
                    const r1 = rows[0];
                    const r2 = rows[1];

                    // Heuristic: If they have a play button or image loaded, they are ready
                    // Assuming 'Generating...' text is present when not ready
                    const ready1 = !r1.textContent.includes('Generating');
                    const ready2 = !r2.textContent.includes('Generating');

                    if (ready1 && ready2) {
                        this.log("Generation Complete!");
                        resolve();
                        return;
                    }
                } else {
                    this.log(`Waiting for items... Current: ${rows.length}, Target: ${targetCount}`);
                }
                setTimeout(check, 2000);
            };
            check();
        });
    }

    async extractAndSend(count) {
        this.log("Extracting data...");
        const rows = Array.from(document.querySelectorAll(this.selectors.clipRow)).slice(0, count);
        const events = [];

        for (const row of rows) {
            // Extract basic data
            const titleEl = row.querySelector('a[href^="/song/"]');
            const title = titleEl ? titleEl.textContent.trim() : "Unknown";
            const songId = titleEl ? titleEl.href.split('/').pop() : Date.now().toString(); // Extract UUID

            // Tags
            const tagsEl = row.querySelector('.css-ingj1g'); // Metadata div
            const tags = tagsEl ? tagsEl.textContent.trim() : "";

            // Image
            const img = row.querySelector('div.clip-image-container img');
            let imgBase64 = "";
            if (img && img.src) {
                try {
                    imgBase64 = await this.urlToBase64(img.src);
                } catch (e) { console.error("Img fetch failed", e); }
            }

            // Audio
            let audioBase64 = "";
            // Try CDN construction
            const audioUrl = `https://cdn1.suno.ai/${songId}.mp3`;
            try {
                audioBase64 = await this.urlToBase64(audioUrl);
            } catch (e) {
                this.log(`Error fetching audio ${audioUrl}: ${e.message}`);
            }

            events.push({
                type: "message",
                message: {
                    type: "audio",
                    id: songId,
                    payload: {
                        audio_base64: audioBase64,
                        image_base64: imgBase64,
                        metadata: {
                            title: title,
                            tags: tags
                        }
                    }
                }
            });
        }

        // Send Batch
        if (events.length > 0) {
            this.log(`Sending batch of ${events.length} songs...`);
            try {
                const resp = await fetch(this.apiUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ events: events })
                });
                const resJson = await resp.json();
                this.log("Backend Response: " + JSON.stringify(resJson));
            } catch (e) {
                this.log("API Error: " + e.message);
            }
        }
    }

    async urlToBase64(url) {
        const response = await fetch(url);
        const blob = await response.blob();
        return new Promise((resolve) => {
            const reader = new FileReader();
            reader.onloadend = () => resolve(reader.result);
            reader.readAsDataURL(blob);
        });
    }

    sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
}

// Initialize
window.addEventListener('load', () => {
    // Wait a bit for Suno app to load
    setTimeout(() => {
        new SunoAutomation();
    }, 3000);
});