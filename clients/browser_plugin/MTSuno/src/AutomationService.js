/**
 * AutomationService - DOM interaction with Suno page
 * @memberof MTSuno
 */
(function (MTS) {
    'use strict';

    class AutomationService {
        constructor(state) {
            this.state = state;
            this.selectors = {
                titleInput: 'input[placeholder="Song Title (Optional)"]',
                clipRow: 'div[data-testid="clip-row"], .clip-row'
            };
        }

        sleep(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
        }

        setNativeValue(element, value) {
            const valueSetter = Object.getOwnPropertyDescriptor(element, 'value')?.set;
            const prototype = Object.getPrototypeOf(element);
            const prototypeValueSetter = Object.getOwnPropertyDescriptor(prototype, 'value')?.set;

            if (valueSetter && valueSetter !== prototypeValueSetter) {
                prototypeValueSetter.call(element, value);
            } else if (valueSetter) {
                valueSetter.call(element, value);
            } else {
                element.value = value;
            }
            element.dispatchEvent(new Event('input', { bubbles: true }));
        }

        findTextareaByPlaceholder(keywords) {
            const textareas = document.querySelectorAll('textarea');
            for (const ta of textareas) {
                const ph = (ta.placeholder || '').toLowerCase();
                if (keywords.some(k => ph.includes(k))) {
                    return ta;
                }
            }
            return null;
        }

        async fillForm(title, style, lyrics) {
            this.state.setStepLabel('Filling Form...');

            // 1. Title - input with specific placeholder
            const titleInput = document.querySelector('input[placeholder="Song Title (Optional)"]');
            if (titleInput) {
                this.setNativeValue(titleInput, title);
                this.state.addLog(`Set title: ${title.substring(0, 30)}...`);
            } else {
                this.state.addLog('Title input not found', 'warning');
            }

            // 2. Find all visible textareas and identify them by order/content
            const allTextareas = Array.from(document.querySelectorAll('textarea'))
                .filter(ta => ta.offsetParent !== null); // Only visible textareas

            this.state.addLog(`Found ${allTextareas.length} textareas`);

            // Log placeholders for debugging
            allTextareas.forEach((ta, i) => {
                const ph = ta.placeholder || '(no placeholder)';
                console.log(`[MTS] Textarea ${i}: ${ph.substring(0, 50)}`);
            });

            // In Suno's custom mode:
            // - First visible textarea is often Lyrics (placeholder: "Write some lyrics...")
            // - Second visible textarea is often Styles (placeholder: "voice man, smooth...")
            let lyricsArea = null;
            let styleArea = null;

            for (const ta of allTextareas) {
                const ph = (ta.placeholder || '').toLowerCase();
                // Lyrics: contains "lyrics" or "write" or "prompt"
                if (ph.includes('lyrics') || ph.includes('write some') || (ph.includes('prompt') && !styleArea)) {
                    lyricsArea = ta;
                }
                // Style: contains numbers (like "165 bpm") or music terms
                else if (ph.includes('bpm') || ph.includes('voice') || ph.includes('punk') || ph.includes('singing')) {
                    styleArea = ta;
                }
            }

            // Fallback: if no specific match, use by index (Lyrics=0, Style=1 typically)
            if (!lyricsArea && allTextareas.length >= 1) {
                lyricsArea = allTextareas[0];
                this.state.addLog('Using first textarea as Lyrics (fallback)');
            }
            if (!styleArea && allTextareas.length >= 2) {
                styleArea = allTextareas[1];
                this.state.addLog('Using second textarea as Style (fallback)');
            }

            // 3. Fill Style
            if (styleArea) {
                this.setNativeValue(styleArea, style || 'Pop');
                this.state.addLog(`Set style: ${(style || 'Pop').substring(0, 30)}...`);
            } else {
                this.state.addLog('Style textarea not found', 'warning');
            }

            // 4. Fill Lyrics
            if (lyricsArea) {
                if (lyrics) {
                    this.setNativeValue(lyricsArea, lyrics);
                    this.state.addLog(`Set lyrics (${lyrics.length} chars)`);
                } else {
                    this.setNativeValue(lyricsArea, '');
                    this.state.addLog('No lyrics provided (Instrumental)', 'info');
                }
            } else {
                this.state.addLog('Lyrics textarea not found', 'warning');
            }

            await this.sleep(500);
        }

        async clickCreate() {
            this.state.setStepLabel('Clicking Create...');

            // Method 1: Use aria-label (most stable)
            let createBtn = document.querySelector('button[aria-label="Create song"]');

            // Method 2: Find by text content
            if (!createBtn) {
                const buttons = Array.from(document.querySelectorAll('button'));
                createBtn = buttons.find(b => {
                    const text = b.textContent.toLowerCase();
                    return text.includes('create') && !b.disabled;
                });
            }

            if (createBtn && !createBtn.disabled) {
                createBtn.click();
                this.state.addLog('Clicked Create button');
                return true;
            } else {
                this.state.addLog('Create button not found or disabled', 'error');
                throw new Error('Create button not found');
            }
        }

        async waitForGeneration(timeout = 180000) {
            this.state.setStepLabel('Waiting for generation...');
            const startTime = Date.now();
            const checkInterval = 3000;

            // Remember current top song ID to detect new song
            const getTopSongId = () => {
                const topRow = document.querySelector('[data-testid="clip-row"], .clip-row');
                if (!topRow) return null;
                const link = topRow.querySelector('a[href*="/song/"]');
                if (!link) return null;
                const match = link.href.match(/\/song\/([a-f0-9-]+)/);
                return match ? match[1] : null;
            };

            // Check if song has a duration (means generation complete)
            const hasDuration = (row) => {
                if (!row) return false;
                // Find duration text like "0:30", "1:06", "2:15" etc.
                const allText = row.textContent || '';
                // Duration pattern: digits:digits (like 0:30, 1:45)
                return /\d+:\d{2}/.test(allText);
            };

            // Check if row is still generating (has spinner)
            const isGenerating = (row) => {
                if (!row) return true;
                // Check for spinner with animate-spin class
                const spinner = row.querySelector('.animate-spin, [class*="animate-spin"]');
                if (spinner) return true;
                // Fallback: check text
                const text = (row.textContent || '').toLowerCase();
                return text.includes('generating') || text.includes('loading');
            };

            const initialSongId = getTopSongId();
            this.state.addLog(`Current top song: ${initialSongId ? initialSongId.substring(0, 8) + '...' : 'none'}`);

            return new Promise((resolve, reject) => {
                const check = () => {
                    const elapsed = Date.now() - startTime;
                    if (elapsed > timeout) {
                        reject(new Error('Generation timeout after ' + Math.round(timeout / 1000) + 's'));
                        return;
                    }

                    // Get top 2 clip rows (Suno generates 2 songs per prompt)
                    const clipRows = document.querySelectorAll('[data-testid="clip-row"], .clip-row');
                    const topRows = Array.from(clipRows).slice(0, 2);

                    if (topRows.length < 2) {
                        // Not enough songs yet, keep waiting
                        setTimeout(check, checkInterval);
                        return;
                    }

                    // Check if both top 2 songs are fully generated
                    let allComplete = true;
                    let spinnerCount = 0;
                    let durationCount = 0;

                    for (const row of topRows) {
                        if (isGenerating(row)) {
                            spinnerCount++;
                            allComplete = false;
                        }
                        if (hasDuration(row)) {
                            durationCount++;
                        } else {
                            allComplete = false;
                        }
                    }

                    // Update progress
                    const pct = Math.round((elapsed / timeout) * 100);
                    this.state.setStepLabel(`Generating... ${pct}% (${durationCount}/2 complete)`);

                    if (allComplete && durationCount >= 2) {
                        // Both songs have duration and no spinners
                        this.state.addLog(`✅ Both songs generated successfully!`);
                        resolve();
                        return;
                    }

                    // Still waiting
                    setTimeout(check, checkInterval);
                };

                // Start checking
                setTimeout(check, checkInterval);
            });
        }

        /**
         * Wait for ALL songs to finish generating (no spinners visible)
         * Used by 'Download all at end' mode
         */
        async waitForAllGenerations(timeout = 600000) { // 10 minutes max
            const checkInterval = 5000; // Check every 5 seconds
            const startTime = Date.now();

            return new Promise((resolve, reject) => {
                const check = () => {
                    const elapsed = Date.now() - startTime;

                    if (elapsed > timeout) {
                        this.state.addLog('Timeout waiting for all songs to generate', 'warning');
                        resolve(); // Continue anyway
                        return;
                    }

                    // Check for any spinners in any clip-row
                    const clipRows = document.querySelectorAll('[data-testid="clip-row"], .clip-row');
                    let spinnerCount = 0;

                    for (const row of clipRows) {
                        const svg = row.querySelector('svg.animate-spin, svg[class*="animate"]');
                        const circleProgress = row.querySelector('[role="progressbar"]');
                        if (svg || circleProgress) {
                            spinnerCount++;
                        }
                    }

                    if (spinnerCount === 0 && clipRows.length > 0) {
                        this.state.addLog(`All ${clipRows.length} visible songs generated!`);
                        resolve();
                        return;
                    }

                    // Update UI
                    const mins = Math.floor(elapsed / 60000);
                    const secs = Math.floor((elapsed % 60000) / 1000);
                    this.state.setStepLabel(`Waiting for generation... ${mins}m ${secs}s (${spinnerCount} pending)`);

                    // Continue polling
                    setTimeout(check, checkInterval);
                };

                // Start checking after a short delay
                setTimeout(check, 2000);
            });
        }

        /**
         * Extract song data from the top clip row
         */
        extractSongData() {
            this.state.setStepLabel('Extracting song data...');
            const clipRow = document.querySelector('[data-testid="clip-row"], .clip-row');
            if (!clipRow) {
                this.state.addLog('Clip row not found', 'warning');
                return null;
            }

            try {
                // Extract image URL - prefer data-src for full quality, fallback to src
                const img = clipRow.querySelector('img');
                let imageUrl = '';
                if (img) {
                    // data-src often has higher quality (image_large_xxx)
                    imageUrl = img.dataset.src || img.src || '';
                    // Remove width params
                    imageUrl = imageUrl.split('?')[0];
                }

                // Extract title and song ID from the link
                const titleLink = clipRow.querySelector('a[href*="/song/"]');
                const title = titleLink ? titleLink.textContent.trim() : 'Untitled';

                // Extract song ID from URL (e.g., /song/62790257-748b-477b-b82a-6f0a2ac50176)
                const songIdMatch = titleLink?.href?.match(/\/song\/([a-f0-9-]+)/);
                const songId = songIdMatch ? songIdMatch[1] : `song_${Date.now()}`;

                // Extract tags - find the div after the title row that contains commas (tags are comma-separated)
                let tags = '';
                const allDivs = clipRow.querySelectorAll('div');
                for (const div of allDivs) {
                    const text = div.textContent || '';
                    // Tags div contains genres: usually has commas and BPM
                    if (text.includes(',') && text.includes('BPM') && text.length < 300) {
                        tags = text.trim();
                        break;
                    }
                    // Fallback: look for Thai characters in a short div (style often has Thai tags)
                    if (text.includes(',') && /[\u0E00-\u0E7F]/.test(text) && text.length < 300) {
                        tags = text.trim();
                        break;
                    }
                }

                // Construct audio URL (Suno pattern: cdn2.suno.ai/{songId}.mp3)
                const audioUrl = songId ? `https://cdn2.suno.ai/${songId}.mp3` : '';

                const songData = {
                    id: songId,
                    title,
                    tags,
                    imageUrl,
                    audioUrl
                };

                this.state.addLog(`Extracted: ${title} (${songId.substring(0, 8)}...)`);
                console.log('[MTS] Song data:', songData);
                return songData;
            } catch (e) {
                this.state.addLog(`Extract error: ${e.message}`, 'error');
                return null;
            }
        }

        /**
         * Download the latest N songs (typically 2 after generation)
         * Clicks each to capture real audio URL, then downloads
         * @param {number} count - Number of latest songs to download (default 2)
         * @param {Object} delaySettings - delay settings for randomization
         */
        async downloadLatestSongs(count = 2, delaySettings = {}) {
            const stepDelayMin = delaySettings.stepDelayMin || 500;
            const stepDelayMax = delaySettings.stepDelayMax || 1500;
            const randomDelay = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min;

            this.state.addLog(`Downloading ${count} latest songs...`);

            // Get the first N clip rows (most recent are at top)
            const clipRows = document.querySelectorAll('[data-testid="clip-row"], .clip-row');
            const songsToDownload = [];

            for (let i = 0; i < Math.min(count, clipRows.length); i++) {
                const row = clipRows[i];
                try {
                    // Get song info
                    const titleLink = row.querySelector('a[href*="/song/"]');
                    const songId = titleLink?.href?.match(/\/song\/([a-f0-9-]+)/)?.[1];
                    const title = titleLink?.textContent?.trim() || 'Untitled';

                    if (!songId) continue;

                    // Get image
                    const img = row.querySelector('img');
                    let imageUrl = '';
                    if (img) {
                        imageUrl = img.dataset.src || img.src || '';
                        imageUrl = imageUrl.split('?')[0];
                    }

                    // Get tags
                    let tags = '';
                    const allDivs = row.querySelectorAll('div');
                    for (const div of allDivs) {
                        const text = div.textContent || '';
                        if (text.includes(',') && text.length > 10 && text.length < 200) {
                            tags = text.trim();
                            break;
                        }
                    }

                    // Click to trigger audio loading
                    const imageContainer = row.querySelector('.clip-image-container');
                    if (imageContainer) {
                        imageContainer.click();
                        this.state.addLog(`Clicked song ${i + 1}: ${title}`);
                        await this.sleep(2000); // Wait for audio to load
                    }

                    // Capture real audio URL from audio element
                    let audioUrl = '';
                    const audioElement = document.querySelector('audio');
                    if (audioElement && audioElement.src) {
                        audioUrl = audioElement.src;
                        console.log(`[MTS] Captured audio URL: ${audioUrl.substring(0, 50)}...`);
                    }

                    if (!audioUrl) {
                        audioUrl = `https://cdn2.suno.ai/${songId}.mp3`;
                    }

                    songsToDownload.push({
                        id: songId,
                        title,
                        tags,
                        imageUrl,
                        audioUrl,
                        thumbUrl: img?.src || imageUrl
                    });

                    await this.sleep(randomDelay(stepDelayMin, stepDelayMax));
                } catch (e) {
                    console.error('[MTS] Error processing song:', e);
                }
            }

            // Now download each song
            for (const song of songsToDownload) {
                try {
                    await this.downloadSingleSong(song);
                    this.state.addLog(`✅ Downloaded: ${song.title}`, 'success');
                } catch (e) {
                    this.state.addLog(`❌ Failed: ${song.title} - ${e.message}`, 'error');
                }
                await this.sleep(randomDelay(stepDelayMin, stepDelayMax));
            }

            return songsToDownload.length;
        }

        /**
         * Quickly collect song IDs without clicking (fast, for 'end' mode)
         * Returns array of song ID strings
         */
        collectLatestSongIds(count = 2) {
            const clipRows = document.querySelectorAll('[data-testid="clip-row"], .clip-row');
            const songIds = [];

            for (let i = 0; i < Math.min(count, clipRows.length); i++) {
                const row = clipRows[i];
                try {
                    const titleLink = row.querySelector('a[href*="/song/"]');
                    const songId = titleLink?.href?.match(/\/song\/([a-f0-9-]+)/)?.[1];
                    if (songId && !songIds.includes(songId)) {
                        songIds.push(songId);
                    }
                } catch (e) {
                    console.error('[MTS] Error collecting song ID:', e);
                }
            }
            return songIds;
        }

        /**
         * Collect the latest N songs without downloading
         * Used for 'Download all at end' mode
         */
        async collectLatestSongs(count = 2, delaySettings = {}) {
            const stepDelayMin = delaySettings.stepDelayMin || 500;
            const stepDelayMax = delaySettings.stepDelayMax || 1500;

            // Get the first N clip rows (most recent are at top)
            const clipRows = document.querySelectorAll('[data-testid="clip-row"], .clip-row');
            const collectedSongs = [];

            for (let i = 0; i < Math.min(count, clipRows.length); i++) {
                const row = clipRows[i];
                try {
                    // Get song info
                    const titleLink = row.querySelector('a[href*="/song/"]');
                    const songId = titleLink?.href?.match(/\/song\/([a-f0-9-]+)/)?.[1];
                    const title = titleLink?.textContent?.trim() || 'Untitled';

                    if (!songId) continue;

                    // Get image
                    const img = row.querySelector('img');
                    let imageUrl = '';
                    if (img) {
                        imageUrl = img.dataset.src || img.src || '';
                        imageUrl = imageUrl.split('?')[0];
                    }

                    // Get tags
                    let tags = '';
                    const allDivs = row.querySelectorAll('div');
                    for (const div of allDivs) {
                        const text = div.textContent || '';
                        if (text.includes(',') && text.length > 10 && text.length < 200) {
                            tags = text.trim();
                            break;
                        }
                    }

                    // Click to trigger audio loading
                    const imageContainer = row.querySelector('.clip-image-container');
                    if (imageContainer) {
                        imageContainer.click();
                        await this.sleep(2000); // Wait for audio to load
                    }

                    // Capture real audio URL from audio element
                    let audioUrl = '';
                    const audioElement = document.querySelector('audio');
                    if (audioElement && audioElement.src) {
                        audioUrl = audioElement.src;
                    }

                    if (!audioUrl) {
                        audioUrl = `https://cdn2.suno.ai/${songId}.mp3`;
                    }

                    collectedSongs.push({
                        id: songId,
                        title,
                        tags,
                        imageUrl,
                        audioUrl,
                        thumbUrl: img?.src || imageUrl
                    });

                    // Random delay between collections
                    const delay = Math.floor(Math.random() * (stepDelayMax - stepDelayMin + 1)) + stepDelayMin;
                    await this.sleep(delay);
                } catch (e) {
                    console.error('[MTS] Error collecting song:', e);
                }
            }

            return collectedSongs;
        }

        /**
         * Download a single song (Wrapper for sendToBackend)
         * Kept for backward compatibility and semantic clarity
         */
        async downloadSingleSong(song) {
            // Ensure we have an API client
            const api = window.MTSuno.Api || new MTS.ApiClient();
            return this.sendToBackend(song, api);
        }

        /**
         * Download multiple songs by their IDs
         * Finds each song in DOM, clicks to get audio URL, then downloads
         */
        async downloadSongsByIds(songIds, delaySettings = {}) {
            const stepDelayMin = delaySettings.stepDelayMin || 500;
            const stepDelayMax = delaySettings.stepDelayMax || 1500;
            const randomDelay = () => Math.floor(Math.random() * (stepDelayMax - stepDelayMin + 1)) + stepDelayMin;

            let successCount = 0;
            let failCount = 0;

            for (let idx = 0; idx < songIds.length; idx++) {
                const songId = songIds[idx];
                this.state.setStepLabel(`Downloading ${idx + 1}/${songIds.length}...`);

                try {
                    // Find the row with this song ID
                    const allRows = document.querySelectorAll('[data-testid="clip-row"], .clip-row');
                    let targetRow = null;

                    for (const row of allRows) {
                        const link = row.querySelector('a[href*="/song/"]');
                        if (link?.href?.includes(songId)) {
                            targetRow = row;
                            break;
                        }
                    }

                    if (!targetRow) {
                        this.state.addLog(`Song ${songId.substring(0, 8)}... not found in DOM`, 'warning');
                        failCount++;
                        continue;
                    }

                    // Extract data from row
                    const titleLink = targetRow.querySelector('a[href*="/song/"]');
                    const title = titleLink?.textContent?.trim() || 'Untitled';

                    const img = targetRow.querySelector('img');
                    let imageUrl = img?.dataset?.src || img?.src || '';
                    imageUrl = imageUrl.split('?')[0];

                    let tags = '';
                    const allDivs = targetRow.querySelectorAll('div');
                    for (const div of allDivs) {
                        const text = div.textContent || '';
                        if (text.includes(',') && text.length > 10 && text.length < 200) {
                            tags = text.trim();
                            break;
                        }
                    }

                    // Click to load audio
                    const imageContainer = targetRow.querySelector('.clip-image-container');
                    if (imageContainer) {
                        imageContainer.click();
                        await this.sleep(2000);
                    }

                    // Capture audio URL
                    let audioUrl = '';
                    const audioElement = document.querySelector('audio');
                    if (audioElement?.src) {
                        audioUrl = audioElement.src;
                    }
                    if (!audioUrl) {
                        audioUrl = `https://cdn2.suno.ai/${songId}.mp3`;
                    }

                    // Download
                    const songData = {
                        id: songId,
                        title,
                        tags,
                        imageUrl,
                        audioUrl,
                        thumbUrl: img?.src || imageUrl
                    };

                    await this.downloadSingleSong(songData);
                    successCount++;
                    this.state.addLog(`✅ Downloaded: ${title}`, 'success');

                } catch (e) {
                    failCount++;
                    this.state.addLog(`❌ Failed ID ${songId.substring(0, 8)}...: ${e.message}`, 'error');
                }

                await this.sleep(randomDelay());
            }

            this.state.setStepLabel('');
            this.state.addLog(`Download complete: ${successCount} success, ${failCount} failed`);
            return { successCount, failCount };
        }

        /**
         * Fetch file as base64 with Retry Logic
         */
        async fetchAsBase64(url, isAudio = false) {
            const maxRetries = isAudio ? 3 : 1;
            let retryCount = 0;

            while (retryCount < maxRetries) {
                try {
                    const res = await fetch(url);
                    if (!res.ok) throw new Error(`HTTP ${res.status}`);

                    const blob = await res.blob();

                    // Validation for Audio
                    if (isAudio && blob.size === 0) {
                        throw new Error('File size is 0 bytes');
                    }

                    return new Promise((resolve, reject) => {
                        const reader = new FileReader();
                        reader.onloadend = () => resolve(reader.result);
                        reader.onerror = reject;
                        reader.readAsDataURL(blob);
                    });

                } catch (e) {
                    retryCount++;
                    if (isAudio) {
                        console.warn(`[MTS] Fetch attempt ${retryCount}/${maxRetries} failed: ${e.message}`);
                        if (retryCount < maxRetries) await this.sleep(2000);
                    } else {
                        return null; // Fail fast for non-audio
                    }
                }
            }
            return null;
        }

        /**
         * Send extracted song data to Backend
         * Now includes robust downloading logic
         */
        async sendToBackend(songData, apiClient) {
            if (!songData) {
                this.state.addLog('No song data to send', 'warning');
                return false;
            }

            this.state.setStepLabel(`Sending: ${songData.title.substring(0, 20)}...`);
            this.state.addLog(`Processing: ${songData.title}...`);

            try {
                // Fetch audio with retry
                const audioBase64 = await this.fetchAsBase64(songData.audioUrl, true);
                if (!audioBase64) throw new Error('Failed to download audio after retries');

                // Fetch image (optional)
                const imageBase64 = await this.fetchAsBase64(songData.imageUrl, false);

                // Prepare webhook payload (Correct Backend Schema)
                // Schema: events -> message -> payload -> metadata
                const payload = {
                    events: [{
                        type: 'message',
                        message: {
                            type: 'audio',
                            id: songData.id,
                            payload: {
                                audio_base64: audioBase64,
                                image_base64: imageBase64 || '',
                                metadata: {
                                    title: songData.title,
                                    tags: songData.tags || ''
                                }
                            }
                        }
                    }]
                };

                // Send to API
                const result = await apiClient.sendSongEvent(payload);

                if (result.success) {
                    this.state.addLog(`✅ Saved to backend: ${songData.title}`, 'success');
                    return true;
                } else {
                    throw new Error(result.error || 'Backend error');
                }

            } catch (e) {
                this.state.addLog(`❌ Failed: ${songData.title} - ${e.message}`, 'error');
                return false;
            }
        }

        /**
         * Load and collect all songs by clicking their cover images
         * Suno uses lazy loading - this clicks to trigger load and collects data in one pass
         * @param {Function} onProgress - callback(count, total)
         * @param {Object} delaySettings - { stepDelayMin, stepDelayMax } in ms
         * @param {number} targetCount - Optional target number of songs to collect (0 = all)
         * Returns array of song objects with all data needed for download
         */
        async loadAndCollectAllSongs(onProgress, delaySettings = {}, targetCount = 0) {
            const stepDelayMin = delaySettings.stepDelayMin || 500;
            const stepDelayMax = delaySettings.stepDelayMax || 1500;

            // Random delay helper
            const randomDelay = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min;

            // Find the scroller container
            const scroller = document.querySelector('.clip-browser-list-scroller');
            if (!scroller) {
                console.log('[MTS] Cannot find scroller container');
                return [];
            }

            const collectedSongs = new Map(); // Map of songId -> song data

            // Helper function to collect data from all visible songs
            const collectVisibleSongs = async (shouldClick) => {
                const rowWrappers = document.querySelectorAll('.clip-browser-list-scroller [role="rowgroup"] > .relative');

                for (const wrapper of rowWrappers) {
                    try {
                        const titleLink = wrapper.querySelector('a[href*="/song/"]');
                        const songId = titleLink?.href?.match(/\/song\/([a-f0-9-]+)/)?.[1];

                        if (!songId || collectedSongs.has(songId)) continue;

                        // Get image
                        const img = wrapper.querySelector('img');
                        let imageUrl = '';
                        if (img) {
                            imageUrl = img.dataset.src || img.src || '';
                            imageUrl = imageUrl.split('?')[0];
                        }

                        // Get title
                        const title = titleLink?.textContent?.trim() || 'Untitled';

                        // Get tags - look for div with comma-separated text
                        let tags = '';
                        const allDivs = wrapper.querySelectorAll('div');
                        for (const div of allDivs) {
                            const text = div.textContent || '';
                            if (text.includes(',') && text.length > 10 && text.length < 200) {
                                if (/[A-Z][a-z]+/.test(text) || /[\u0E00-\u0E7F]/.test(text)) {
                                    tags = text.trim();
                                    break;
                                }
                            }
                        }

                        // Click to trigger loading and capture real audio URL
                        let audioUrl = '';
                        if (shouldClick) {
                            const imageContainer = wrapper.querySelector('.clip-image-container');
                            if (imageContainer) {
                                imageContainer.click();
                                console.log(`[MTS] Clicked & collecting song ${collectedSongs.size + 1}: ${songId.substring(0, 8)}...`);

                                // Wait for audio to start loading and capture the real URL
                                await this.sleep(1500);

                                // Try to get audio URL from audio element
                                const audioElement = document.querySelector('audio');
                                if (audioElement && audioElement.src) {
                                    audioUrl = audioElement.src;
                                    console.log(`[MTS] Captured audio URL: ${audioUrl.substring(0, 50)}...`);
                                }

                                await this.sleep(500); // Additional wait
                            }
                        }

                        // Fallback to constructed URL if we couldn't capture it
                        if (!audioUrl) {
                            audioUrl = `https://cdn2.suno.ai/${songId}.mp3`;
                        }

                        // Store song data
                        collectedSongs.set(songId, {
                            id: songId,
                            title,
                            tags,
                            imageUrl,
                            audioUrl,
                            thumbUrl: img?.src || imageUrl,
                            duration: '' // Will be empty but we have the audio URL
                        });

                        if (onProgress) {
                            onProgress(collectedSongs.size, '?');
                        }
                    } catch (e) {
                        // Skip errors for individual rows
                    }
                }
            };

            // ===== SINGLE PASS: SCROLL TO EACH ROW, CLICK, COLLECT =====
            console.log(`[MTS] Scrolling and collecting (target: ${targetCount || 'all'})...`);
            this.state.setStepLabel('Collecting songs one by one...');

            let lastKnownRowCount = 0;
            let noNewRowsCount = 0;
            let totalProcessed = 0;

            while (totalProcessed < 500) { // Safety limit
                // Check target
                if (targetCount > 0 && collectedSongs.size >= targetCount) {
                    console.log(`[MTS] Reached target: ${collectedSongs.size}`);
                    break;
                }

                // Get all current rows
                const rowWrappers = document.querySelectorAll('.clip-browser-list-scroller [role="rowgroup"] > .relative');

                // Check for end-of-list indicator (Reset filters button)
                const resetFiltersBtn = document.querySelector('button span');
                const isEndOfList = resetFiltersBtn && resetFiltersBtn.textContent?.includes('Reset filters');
                if (isEndOfList && collectedSongs.size > 0) {
                    console.log(`[MTS] Found 'Reset filters' button - reached end of list!`);
                    // Don't break immediately, process remaining visible rows first
                }

                if (rowWrappers.length === 0) {
                    console.log('[MTS] No rows found!');
                    break;
                }

                let foundNewSong = false;

                // Process each visible row
                for (const wrapper of rowWrappers) {
                    try {
                        const titleLink = wrapper.querySelector('a[href*="/song/"]');
                        const songId = titleLink?.href?.match(/\/song\/([a-f0-9-]+)/)?.[1];

                        if (!songId || collectedSongs.has(songId)) continue;

                        // SCROLL TO THIS ROW to ensure it's rendered
                        wrapper.scrollIntoView({ behavior: 'instant', block: 'center' });
                        await this.sleep(300);

                        // Get image
                        const img = wrapper.querySelector('img');
                        let imageUrl = '';
                        if (img) {
                            imageUrl = img.dataset.src || img.src || '';
                            imageUrl = imageUrl.split('?')[0];
                        }

                        // Get title
                        const title = titleLink?.textContent?.trim() || 'Untitled';

                        // Get tags
                        let tags = '';
                        const allDivs = wrapper.querySelectorAll('div');
                        for (const div of allDivs) {
                            const text = div.textContent || '';
                            if (text.includes(',') && text.length > 10 && text.length < 200) {
                                tags = text.trim();
                                break;
                            }
                        }

                        // Click to trigger audio loading
                        let audioUrl = '';
                        const imageContainer = wrapper.querySelector('.clip-image-container');
                        if (imageContainer) {
                            imageContainer.click();
                            await this.sleep(1500);

                            // Capture audio URL
                            const audioElement = document.querySelector('audio');
                            if (audioElement?.src) {
                                audioUrl = audioElement.src;
                            }
                            await this.sleep(500);
                        }

                        // Fallback URL
                        if (!audioUrl) {
                            audioUrl = `https://cdn2.suno.ai/${songId}.mp3`;
                        }

                        // Store song data
                        collectedSongs.set(songId, {
                            id: songId,
                            title,
                            tags,
                            imageUrl,
                            audioUrl,
                            thumbUrl: img?.src || imageUrl,
                            duration: ''
                        });

                        foundNewSong = true;
                        totalProcessed++;

                        // Update progress
                        this.state.setStepLabel(`Collected ${collectedSongs.size}/${targetCount || '?'} songs...`);
                        if (onProgress) {
                            onProgress(collectedSongs.size, targetCount || '?');
                        }

                        // Random delay
                        await this.sleep(randomDelay(stepDelayMin, stepDelayMax));

                    } catch (e) {
                        console.error('[MTS] Error processing row:', e);
                    }
                }

                // After processing all visible rows, scroll down to load more
                if (scroller) {
                    scroller.scrollTop = scroller.scrollTop + 800; // Increased scroll distance
                    await this.sleep(800); // Wait longer for Virtual List to render
                }

                // Check if we found any new songs
                if (!foundNewSong) {
                    noNewRowsCount++;
                    // Stop earlier if we detected end-of-list button
                    const maxAttempts = isEndOfList ? 3 : 15;
                    if (noNewRowsCount >= maxAttempts) {
                        console.log(`[MTS] No new songs after ${maxAttempts} scroll attempts, collected: ${collectedSongs.size}`);
                        break;
                    }
                } else {
                    noNewRowsCount = 0;
                }
            }

            const songs = Array.from(collectedSongs.values());
            console.log(`[MTS] Collected ${songs.length} unique songs`);
            this.state.addLog(`Collected ${songs.length} songs`);
            return songs;
        }

        /**
         * Scan all completed songs from the Suno page
         * Returns array of song data objects
         */
        scanAllSongs() {
            const songs = [];
            const clipRows = document.querySelectorAll('[data-testid="clip-row"], .clip-row');

            console.log(`[MTS] Found ${clipRows.length} clip rows in DOM`);

            let skippedSpinner = 0;
            let skippedNoDuration = 0;
            let skippedNoSongId = 0;

            for (const clipRow of clipRows) {
                try {
                    // Check if song is completed (has duration, not spinner)
                    const spinner = clipRow.querySelector('.animate-spin');
                    if (spinner) {
                        // Still generating, skip
                        skippedSpinner++;
                        continue;
                    }

                    // Check for duration pattern - search all divs for time format
                    let durationText = '';
                    const allDivsForDuration = clipRow.querySelectorAll('div');
                    for (const div of allDivsForDuration) {
                        const text = div.textContent?.trim() || '';
                        // Look for duration pattern like "1:54", "2:47", "12:34" 
                        // Check exact match first (most reliable)
                        if (/^\d{1,2}:\d{2}$/.test(text)) {
                            durationText = text;
                            break;
                        }
                    }

                    // Fallback: search for duration pattern anywhere in clipRow
                    if (!durationText) {
                        const rowText = clipRow.textContent || '';
                        const durationMatch = rowText.match(/\b(\d{1,2}:\d{2})\b/);
                        if (durationMatch) {
                            durationText = durationMatch[1];
                        }
                    }

                    if (!durationText) {
                        // No duration found, skip
                        skippedNoDuration++;
                        continue;
                    }

                    // Extract image URL
                    const img = clipRow.querySelector('img');
                    let imageUrl = '';
                    if (img) {
                        imageUrl = img.dataset.src || img.src || '';
                        imageUrl = imageUrl.split('?')[0];
                    }

                    // Extract title and song ID from the link
                    const titleLink = clipRow.querySelector('a[href*="/song/"]');
                    const title = titleLink ? titleLink.textContent.trim() : 'Untitled';

                    // Extract song ID
                    const songIdMatch = titleLink?.href?.match(/\/song\/([a-f0-9-]+)/);
                    const songId = songIdMatch ? songIdMatch[1] : null;

                    if (!songId) {
                        skippedNoSongId++;
                        continue;
                    }

                    // Extract tags
                    let tags = '';
                    const allDivs = clipRow.querySelectorAll('div');
                    for (const div of allDivs) {
                        const text = div.textContent || '';
                        if (text.includes(',') && text.length > 10 && text.length < 200) {
                            // Look for typical tag patterns
                            if (/[A-Z][a-z]+/.test(text) || /[\u0E00-\u0E7F]/.test(text)) {
                                tags = text.trim();
                                break;
                            }
                        }
                    }

                    // Construct audio URL
                    const audioUrl = `https://cdn2.suno.ai/${songId}.mp3`;

                    songs.push({
                        id: songId,
                        title,
                        tags,
                        duration: durationText,
                        imageUrl,
                        audioUrl,
                        thumbUrl: img?.src || imageUrl
                    });
                } catch (e) {
                    console.log('[MTS] Error scanning row:', e);
                }
            }

            console.log(`[MTS] Scan results: ${songs.length} songs found, skipped: ${skippedSpinner} spinner, ${skippedNoDuration} no-duration, ${skippedNoSongId} no-songId`);
            return songs;
        }

        /**
         * Fetch file as base64
         */
        async fetchAsBase64(url) {
            try {
                const res = await fetch(url);
                const blob = await res.blob();
                return new Promise((resolve, reject) => {
                    const reader = new FileReader();
                    reader.onloadend = () => resolve(reader.result);
                    reader.onerror = reject;
                    reader.readAsDataURL(blob);
                });
            } catch (e) {
                console.error('[MTS] Fetch base64 error:', e);
                return null;
            }
        }

        /**
         * Send extracted song data to Backend
         */
        async sendToBackend(songData, apiClient) {
            if (!songData) {
                this.state.addLog('No song data to send', 'warning');
                return false;
            }

            this.state.setStepLabel('Sending to backend...');

            try {
                // Fetch audio and image as base64
                this.state.addLog('Downloading audio...');
                const audioBase64 = await this.fetchAsBase64(songData.audioUrl);

                this.state.addLog('Downloading image...');
                const imageBase64 = await this.fetchAsBase64(songData.imageUrl);

                if (!audioBase64 || !imageBase64) {
                    throw new Error('Failed to download media files');
                }

                // Prepare webhook payload (matching BE schema)
                const payload = {
                    events: [{
                        type: 'message',
                        message: {
                            type: 'audio',
                            id: songData.id,
                            payload: {
                                audio_base64: audioBase64,
                                image_base64: imageBase64,
                                metadata: {
                                    title: songData.title,
                                    tags: songData.tags
                                }
                            }
                        }
                    }]
                };

                this.state.addLog('Sending to backend...');
                const result = await apiClient.sendSongEvent(payload);

                if (result.success) {
                    this.state.addLog(`✅ Saved to backend: ${songData.title}`, 'success');
                    return true;
                } else {
                    throw new Error(result.error || 'Backend error');
                }
            } catch (e) {
                this.state.addLog(`❌ Backend send failed: ${e.message}`, 'error');
                return false;
            }
        }

        // CSV Parsing
        parseCSV(text) {
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
                } else if ((char === '\n' || char === '\r') && !inQuotes) {
                    if (currentVal || currentRow.length > 0) {
                        currentRow.push(currentVal.trim());
                        rows.push(currentRow);
                        currentRow = [];
                        currentVal = '';
                    }
                } else {
                    currentVal += char;
                }
            }
            if (currentVal) currentRow.push(currentVal.trim());
            if (currentRow.length > 0) rows.push(currentRow);

            if (rows.length < 2) return [];

            const headers = rows[0].map(h => h.toLowerCase().replace(/['"]/g, ''));
            const data = [];

            for (let i = 1; i < rows.length; i++) {
                const rowData = rows[i];
                if (rowData.length === headers.length) {
                    const obj = {};
                    headers.forEach((h, idx) => {
                        obj[h] = (rowData[idx] || '').replace(/^"|"$/g, '');
                    });
                    data.push(obj);
                }
            }
            return data;
        }
    }

    MTS.AutomationService = AutomationService;

})(window.MTSuno || (window.MTSuno = {}));
