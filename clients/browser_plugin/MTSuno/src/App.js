/**
 * App - Main UI Application with Pure DOM (No Vue)
 * @memberof MTSuno
 */
(function (MTS) {
    'use strict';

    MTS.initApp = function () {
        console.log('[MTS] Initializing App...');

        // 1. Initialize Core Classes
        MTS.State = new MTS.StateManager();
        MTS.Api = new MTS.ApiClient('http://localhost:8000');
        MTS.Automation = new MTS.AutomationService(MTS.State);

        // 2. Inject Styles
        MTS.injectStyles();

        // 3. Create Container
        const containerId = 'mt-suno-root';
        if (document.getElementById(containerId)) return;

        const container = document.createElement('div');
        container.id = containerId;
        document.body.appendChild(container);

        // 4. Build the UI
        MTS.UI = new MTS.UIBuilder(container);

        // 5. Subscribe to state changes
        MTS.State.subscribe((state) => {
            MTS.UI.update(state);
        });

        // 6. Initial server check
        MTS.checkServer();

        console.log('[MTS] App Initialized');
    };

    MTS.checkServer = async function () {
        const res = await MTS.Api.healthCheck();
        MTS.State.setServerOnline(res.success);
        MTS.State.addLog(res.success ? 'Server online' : 'Server offline', res.success ? 'success' : 'error');
    };

    // UI Builder Class
    class UIBuilder {
        constructor(container) {
            this.container = container;
            this.elements = {};
            this.isCollapsed = false;
            this.build();
        }

        build() {
            this.container.innerHTML = `
                <div class="mts-panel">
                    <div class="mts-header">
                        <span class="mts-header-title">🎵 MTSuno</span>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <div class="mts-header-status offline" id="mts-status-dot" title="Offline"></div>
                            <button class="mts-collapse-btn" id="mts-collapse-btn">−</button>
                        </div>
                    </div>
                    <div class="mts-body" id="mts-body">
                        <!-- File Upload -->
                        <div class="mts-section">
                            <div class="mts-label">Upload CSV</div>
                            <input type="file" accept=".csv" class="mts-file-input" id="mts-file-input" />
                        </div>

                        <!-- Delay Settings -->
                        <div class="mts-section">
                            <div class="mts-label">⏱️ Delay Settings (Anti-Bot)</div>
                            <div style="display: flex; gap: 6px; align-items: center; margin-bottom: 6px;">
                                <span style="font-size: 11px; color: #888; width: 80px;">Item Delay:</span>
                                <input type="number" id="mts-item-delay-min" class="mts-input-small" value="3" min="1" max="60" /> 
                                <span style="color: #888;">-</span>
                                <input type="number" id="mts-item-delay-max" class="mts-input-small" value="8" min="1" max="120" />
                                <span style="font-size: 10px; color: #666;">sec</span>
                            </div>
                            <div style="display: flex; gap: 6px; align-items: center;">
                                <span style="font-size: 11px; color: #888; width: 80px;">Step Delay:</span>
                                <input type="number" id="mts-step-delay-min" class="mts-input-small" value="500" min="100" max="5000" step="100" />
                                <span style="color: #888;">-</span>
                                <input type="number" id="mts-step-delay-max" class="mts-input-small" value="1500" min="100" max="10000" step="100" />
                                <span style="font-size: 10px; color: #666;">ms</span>
                            </div>
                            <div style="margin-top: 10px;">
                                <div class="mts-label" style="margin-bottom: 6px;">📥 Download Mode</div>
                                <label style="display: flex; align-items: center; gap: 6px; cursor: pointer; margin-bottom: 4px;">
                                    <input type="radio" name="mts-download-mode" value="none" checked style="width: 14px; height: 14px;" />
                                    <span style="font-size: 11px; color: #aaa;">🖐️ Manual (ผู้ใช้ดำเนินการเอง)</span>
                                </label>
                                <label style="display: flex; align-items: center; gap: 6px; cursor: pointer; margin-bottom: 4px;">
                                    <input type="radio" name="mts-download-mode" value="each" style="width: 14px; height: 14px;" />
                                    <span style="font-size: 11px; color: #aaa;">Download each 2 songs (after generation)</span>
                                </label>
                                <label style="display: flex; align-items: center; gap: 6px; cursor: pointer;">
                                    <input type="radio" name="mts-download-mode" value="end" style="width: 14px; height: 14px;" />
                                    <span style="font-size: 11px; color: #aaa;">Download all at end</span>
                                </label>
                            </div>
                        </div>
                        <!-- Stats -->
                        <div class="mts-stats">
                            <div class="mts-stat">
                                <div class="mts-stat-value" id="mts-stat-total">0</div>
                                <div class="mts-stat-label">Total</div>
                            </div>
                            <div class="mts-stat success">
                                <div class="mts-stat-value" id="mts-stat-success">0</div>
                                <div class="mts-stat-label">Done</div>
                            </div>
                            <div class="mts-stat error">
                                <div class="mts-stat-value" id="mts-stat-failed">0</div>
                                <div class="mts-stat-label">Failed</div>
                            </div>
                        </div>

                        <!-- Step Label -->
                        <div id="mts-step-label" style="text-align: center; margin-bottom: 10px; color: #fbbf24; display: none;"></div>

                        <!-- Start Button -->
                        <button class="mts-btn mts-btn-primary" id="mts-start-btn" disabled>🚀 Start Automation</button>
                        
                        <!-- Load All Button (triggers lazy loading) -->
                        <button class="mts-btn mts-btn-secondary" id="mts-load-btn" style="margin-top: 8px;">🔄 Load All Songs</button>
                        
                        <!-- Scan Songs Button -->
                        <button class="mts-btn mts-btn-download" id="mts-download-btn" style="margin-top: 8px;">🔍 Scan Songs</button>

                        <!-- Table -->
                        <div class="mts-table-wrap" id="mts-table-wrap" style="margin-top: 12px; display: none;">
                            <table class="mts-table">
                                <thead>
                                    <tr>
                                        <th style="width: 30px;">#</th>
                                        <th>Title</th>
                                        <th style="width: 80px;">Status</th>
                                    </tr>
                                </thead>
                                <tbody id="mts-table-body"></tbody>
                            </table>
                        </div>

                        <!-- Logs -->
                        <div class="mts-log-wrap" id="mts-log-wrap"></div>

                        <!-- Check Server Button -->
                        <button class="mts-btn mts-btn-secondary" id="mts-check-btn" style="margin-top: 8px;">🔌 Check Server</button>
                    </div>
                </div>
            `;

            // Cache elements
            this.elements = {
                panel: this.container.querySelector('.mts-panel'),
                body: this.container.querySelector('#mts-body'),
                statusDot: this.container.querySelector('#mts-status-dot'),
                collapseBtn: this.container.querySelector('#mts-collapse-btn'),
                fileInput: this.container.querySelector('#mts-file-input'),
                startBtn: this.container.querySelector('#mts-start-btn'),
                loadBtn: this.container.querySelector('#mts-load-btn'),
                downloadBtn: this.container.querySelector('#mts-download-btn'),
                checkBtn: this.container.querySelector('#mts-check-btn'),
                statTotal: this.container.querySelector('#mts-stat-total'),
                statSuccess: this.container.querySelector('#mts-stat-success'),
                statFailed: this.container.querySelector('#mts-stat-failed'),
                stepLabel: this.container.querySelector('#mts-step-label'),
                tableWrap: this.container.querySelector('#mts-table-wrap'),
                tableBody: this.container.querySelector('#mts-table-body'),
                logWrap: this.container.querySelector('#mts-log-wrap'),
                // Delay settings inputs
                itemDelayMin: this.container.querySelector('#mts-item-delay-min'),
                itemDelayMax: this.container.querySelector('#mts-item-delay-max'),
                stepDelayMin: this.container.querySelector('#mts-step-delay-min'),
                stepDelayMax: this.container.querySelector('#mts-step-delay-max')
            };

            // Event Listeners
            this.elements.collapseBtn.addEventListener('click', () => this.toggleCollapse());
            this.elements.fileInput.addEventListener('change', (e) => this.handleFileChange(e));
            this.elements.startBtn.addEventListener('click', () => this.startAutomation());
            this.elements.loadBtn.addEventListener('click', () => this.triggerLoad());
            this.elements.downloadBtn.addEventListener('click', () => this.showDownloadModal());
            this.elements.checkBtn.addEventListener('click', () => MTS.checkServer());

            // Add Save Settings Listeners
            const inputs = [
                this.elements.itemDelayMin, this.elements.itemDelayMax,
                this.elements.stepDelayMin, this.elements.stepDelayMax
            ];
            inputs.forEach(input => input.addEventListener('change', () => this.saveSettings()));

            const radios = this.container.querySelectorAll('input[name="mts-download-mode"]');
            radios.forEach(radio => radio.addEventListener('change', () => this.saveSettings()));

            // Load saved settings
            this.loadSettings();
        }

        /**
         * Get selected download mode from radio buttons
         * Returns: 'none', 'each', or 'end'
         */
        getDownloadMode() {
            const selected = this.container.querySelector('input[name="mts-download-mode"]:checked');
            return selected ? selected.value : 'none';
        }

        /**
         * Get current delay settings from UI
         */
        /**
         * Get current delaying settings from UI
         */
        getDelaySettings() {
            return {
                itemDelayMin: parseInt(this.elements.itemDelayMin.value) || 3,
                itemDelayMax: parseInt(this.elements.itemDelayMax.value) || 8,
                stepDelayMin: parseInt(this.elements.stepDelayMin.value) || 500,
                stepDelayMax: parseInt(this.elements.stepDelayMax.value) || 1500
            };
        }

        /**
         * Save settings to localStorage
         */
        saveSettings() {
            const settings = {
                delay: this.getDelaySettings(),
                downloadMode: this.getDownloadMode()
            };
            localStorage.setItem('mts_suno_settings', JSON.stringify(settings));
        }

        /**
         * Load settings from localStorage
         */
        loadSettings() {
            try {
                const saved = localStorage.getItem('mts_suno_settings');
                if (saved) {
                    const settings = JSON.parse(saved);

                    if (settings.delay) {
                        this.elements.itemDelayMin.value = settings.delay.itemDelayMin;
                        this.elements.itemDelayMax.value = settings.delay.itemDelayMax;
                        this.elements.stepDelayMin.value = settings.delay.stepDelayMin;
                        this.elements.stepDelayMax.value = settings.delay.stepDelayMax;
                    }

                    if (settings.downloadMode) {
                        const radio = this.container.querySelector(`input[name="mts-download-mode"][value="${settings.downloadMode}"]`);
                        if (radio) radio.checked = true;
                    }
                }
            } catch (e) {
                console.warn('[MTS] Failed to load settings', e);
            }
        }

        /**
         * Generate random delay in range
         */
        randomDelay(min, max) {
            return Math.floor(Math.random() * (max - min + 1)) + min;
        }

        toggleCollapse() {
            this.isCollapsed = !this.isCollapsed;
            this.elements.body.style.display = this.isCollapsed ? 'none' : 'block';
            this.elements.collapseBtn.textContent = this.isCollapsed ? '+' : '−';
            this.elements.panel.style.width = this.isCollapsed ? 'auto' : '400px';
        }

        /**
         * Load all songs and show download modal directly
         */
        async triggerLoad() {
            MTS.State.addLog('Starting to load and collect all songs...');
            this.elements.loadBtn.disabled = true;
            this.elements.loadBtn.textContent = '⏳ Loading...';
            this.elements.downloadBtn.disabled = true;

            try {
                const delaySettings = this.getDelaySettings();
                const songs = await MTS.Automation.loadAndCollectAllSongs((loaded, total) => {
                    MTS.State.setStepLabel(`Collecting song ${loaded}...`);
                }, delaySettings);

                MTS.State.setStepLabel('');

                if (songs.length === 0) {
                    MTS.State.addLog('No songs found!', 'error');
                } else {
                    MTS.State.addLog(`Collected ${songs.length} songs! Showing download dialog...`, 'success');
                    // Store collected songs and show modal directly
                    this.scannedSongs = songs;
                    this.showDownloadModalWithSongs(songs);
                }
            } catch (e) {
                MTS.State.addLog(`Error loading: ${e.message}`, 'error');
            }

            this.elements.loadBtn.disabled = false;
            this.elements.loadBtn.textContent = '🔄 Load All Songs';
            this.elements.downloadBtn.disabled = false;
        }

        handleFileChange(e) {
            const file = e.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = (ev) => {
                const text = ev.target.result;
                const parsed = MTS.Automation.parseCSV(text);
                const songList = parsed.map((row, i) => ({
                    id: i + 1,
                    title: row['descr'] || row['title'] || 'Untitled',
                    style: row['style'] || '',
                    lyrics: row['lyrics'] || '',
                    status: 'pending',
                    msg: ''
                }));
                MTS.State.setSongs(songList);
                MTS.State.addLog(`Loaded ${songList.length} songs from CSV`);
            };
            reader.readAsText(file);
        }

        async startAutomation() {
            const songs = MTS.State.state.songs;
            if (MTS.State.state.isProcessing) return;
            if (songs.length === 0) {
                MTS.State.addLog('No songs loaded. Please upload CSV first.', 'warning');
                return;
            }

            MTS.State.setProcessing(true);
            MTS.State.addLog('Starting automation...');
            this.elements.startBtn.disabled = true;
            this.elements.startBtn.textContent = '⏳ Running...';

            const downloadMode = this.getDownloadMode();
            MTS.State.addLog(`Download mode: ${downloadMode}`);

            // Collection for 'end' mode (stores song IDs only for speed)
            this.generatedSongIds = [];

            for (let i = 0; i < songs.length; i++) {
                MTS.State.setCurrentSong(i);
                MTS.State.updateSongStatus(i, 'processing');

                const song = songs[i];

                try {
                    await MTS.Automation.fillForm(song.title, song.style, song.lyrics);
                    await MTS.Automation.clickCreate();

                    if (downloadMode === 'end') {
                        // Mode 'end': Fast mode - don't wait for generation
                        MTS.State.updateSongStatus(i, 'queued', 'Queued');
                        MTS.State.addLog(`Queued: ${song.title}`);
                        MTS.State.incrementSuccess();
                    } else {
                        // Mode 'each' or 'none': Wait for generation to complete
                        MTS.State.updateSongStatus(i, 'generating');
                        await MTS.Automation.waitForGeneration();

                        // Extract song data from Suno
                        MTS.State.updateSongStatus(i, 'extracting');
                        const songData = MTS.Automation.extractSongData();

                        // Handle Download Modes
                        const settings = this.getDelaySettings();

                        if (downloadMode === 'each') {
                            // Mode 'each': Send to backend immediately + download
                            if (songData && MTS.State.state.serverOnline) {
                                MTS.State.updateSongStatus(i, 'uploading');
                                await MTS.Automation.sendToBackend(songData, MTS.Api);
                            }
                            MTS.State.updateSongStatus(i, 'downloading');
                            await MTS.Automation.downloadLatestSongs(2, settings);
                        } else {
                            // Mode 'none': Send metadata only (no download)
                            if (songData && MTS.State.state.serverOnline) {
                                MTS.State.updateSongStatus(i, 'uploading');
                                await MTS.Automation.sendToBackend(songData, MTS.Api);
                            }
                        }

                        MTS.State.updateSongStatus(i, 'completed', 'OK');
                        MTS.State.incrementSuccess();
                    }
                } catch (err) {
                    MTS.State.updateSongStatus(i, 'error', err.message);
                    MTS.State.incrementFailed();
                    MTS.State.addLog(`Error: ${err.message}`, 'error');
                }

                // Random delay between songs (anti-bot)
                if (i < songs.length - 1) {
                    const settings = this.getDelaySettings();
                    const delay = this.randomDelay(settings.itemDelayMin * 1000, settings.itemDelayMax * 1000);
                    MTS.State.addLog(`Waiting ${(delay / 1000).toFixed(1)}s before next song...`);
                    await new Promise(r => setTimeout(r, delay));
                }
            }

            // Download all at end if mode is 'end'
            if (downloadMode === 'end') {
                const totalSongsToDownload = songs.length * 2; // Each prompt generates 2 songs

                MTS.State.addLog('All create commands sent! Waiting for songs to generate...');
                MTS.State.setStepLabel('Waiting for generation...');

                // Wait for all songs to finish generating (poll until no spinners)
                await MTS.Automation.waitForAllGenerations();

                MTS.State.addLog(`All songs generated! Loading ${totalSongsToDownload} songs...`);
                MTS.State.setStepLabel('Scrolling to load all songs...');

                // Scroll down to load all songs (Virtual List)
                const settings = this.getDelaySettings();
                const allSongs = await MTS.Automation.loadAndCollectAllSongs((loaded) => {
                    MTS.State.setStepLabel(`Loading song ${loaded}...`);
                }, settings, totalSongsToDownload);

                // Take only the expected number of songs (newest first)
                const songsToDownload = allSongs.slice(0, totalSongsToDownload);

                MTS.State.addLog(`Loaded ${allSongs.length} songs. Downloading ${songsToDownload.length}...`);

                // Download each song
                let successCount = 0;
                let failCount = 0;
                for (let i = 0; i < songsToDownload.length; i++) {
                    const song = songsToDownload[i];
                    MTS.State.setStepLabel(`Downloading ${i + 1}/${songsToDownload.length}: ${song.title.substring(0, 20)}...`);
                    try {
                        await MTS.Automation.downloadSingleSong(song);
                        successCount++;
                        MTS.State.addLog(`✅ Downloaded: ${song.title}`, 'success');
                    } catch (e) {
                        failCount++;
                        MTS.State.addLog(`❌ Failed: ${song.title} - ${e.message}`, 'error');
                    }
                    await MTS.Automation.sleep(settings.stepDelayMin + Math.random() * (settings.stepDelayMax - settings.stepDelayMin));
                }

                MTS.State.addLog(`Download complete: ${successCount} success, ${failCount} failed`);
            }

            MTS.State.setProcessing(false);
            MTS.State.setStepLabel('');
            MTS.State.addLog('Automation finished!', 'success');
            this.elements.startBtn.disabled = false;
            this.elements.startBtn.textContent = '🚀 Start Automation';
        }

        update(state) {
            // Server Status
            this.elements.statusDot.className = 'mts-header-status ' + (state.serverOnline ? 'online' : 'offline');
            this.elements.statusDot.title = state.serverOnline ? 'Online' : 'Offline';

            // Stats
            this.elements.statTotal.textContent = state.progress.total;
            this.elements.statSuccess.textContent = state.progress.success;
            this.elements.statFailed.textContent = state.progress.failed;

            // Step Label
            if (state.isProcessing) {
                this.elements.stepLabel.style.display = 'block';
                this.elements.stepLabel.textContent = '🔄 ' + state.progress.stepLabel;
            } else {
                this.elements.stepLabel.style.display = 'none';
            }

            // Start Button
            this.elements.startBtn.disabled = state.songs.length === 0 || state.isProcessing;

            // Table
            if (state.songs.length > 0) {
                this.elements.tableWrap.style.display = 'block';
                this.renderTable(state.songs, state.currentSongIndex);
            } else {
                this.elements.tableWrap.style.display = 'none';
            }

            // Logs
            this.renderLogs(state.logs);
        }

        renderTable(songs, currentIndex) {
            this.elements.tableBody.innerHTML = songs.map((song, idx) => `
                <tr class="${idx === currentIndex ? 'active' : ''}">
                    <td>${song.id}</td>
                    <td style="max-width: 150px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${song.title}">${song.title}</td>
                    <td><span class="mts-badge ${song.status}">${song.status}</span></td>
                </tr>
            `).join('');
        }

        renderLogs(logs) {
            const lastLogs = logs.slice(-15);
            this.elements.logWrap.innerHTML = lastLogs.map(log =>
                `<div class="mts-log-entry ${log.type}">[${log.timestamp}] ${log.message}</div>`
            ).join('');
            this.elements.logWrap.scrollTop = this.elements.logWrap.scrollHeight;
        }

        /**
         * Show Download Modal with scanned songs
         */
        showDownloadModal() {
            // Scan songs from Suno page
            const songs = MTS.Automation.scanAllSongs();
            this.scannedSongs = songs;

            if (songs.length === 0) {
                MTS.State.addLog('No completed songs found on page', 'warning');
                alert('ไม่พบเพลงที่สร้างเสร็จบนหน้านี้\n\nกรุณาเปิดหน้า Suno ที่มีเพลงที่ต้องการดาวน์โหลด');
                return;
            }

            MTS.State.addLog(`Found ${songs.length} completed songs`);

            // Build modal HTML
            const modalHtml = `
                <div class="mts-modal-overlay" id="mts-modal-overlay">
                    <div class="mts-modal">
                        <div class="mts-modal-header">
                            <h3>📥 Download All Songs</h3>
                            <button class="mts-modal-close" id="mts-modal-close">&times;</button>
                        </div>
                        <div class="mts-modal-body">
                            <div class="mts-summary-text">
                                พบเพลงที่พร้อมดาวน์โหลด <strong>${songs.length}</strong> รายการ
                            </div>
                            <table class="mts-dl-table">
                                <thead>
                                    <tr>
                                        <th style="width: 50px;">Image</th>
                                        <th>Title</th>
                                        <th style="width: 60px;">Duration</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${songs.map(song => `
                                        <tr>
                                            <td><img class="song-thumb" src="${song.thumbUrl}" alt="" /></td>
                                            <td>
                                                <div class="song-title">${song.title}</div>
                                                <div class="song-tags">${song.tags}</div>
                                            </td>
                                            <td>${song.duration}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                        <div class="mts-modal-footer">
                            <button class="mts-btn mts-btn-secondary" id="mts-modal-cancel">ยกเลิก</button>
                            <button class="mts-btn mts-btn-download" id="mts-modal-confirm">✅ ยืนยันดาวน์โหลด</button>
                        </div>
                    </div>
                </div>
            `;

            // Insert modal into DOM
            const modalContainer = document.createElement('div');
            modalContainer.id = 'mts-modal-container';
            modalContainer.innerHTML = modalHtml;
            document.body.appendChild(modalContainer);

            // Attach event listeners
            document.getElementById('mts-modal-close').addEventListener('click', () => this.closeModal());
            document.getElementById('mts-modal-cancel').addEventListener('click', () => this.closeModal());
            document.getElementById('mts-modal-confirm').addEventListener('click', () => this.startBulkDownload());
            document.getElementById('mts-modal-overlay').addEventListener('click', (e) => {
                if (e.target.id === 'mts-modal-overlay') this.closeModal();
            });
        }

        /**
         * Show Download Modal with provided songs (used by loadAndCollectAllSongs)
         */
        showDownloadModalWithSongs(songs) {
            if (!songs || songs.length === 0) {
                MTS.State.addLog('No songs to display', 'warning');
                return;
            }

            // Build modal HTML
            const modalHtml = `
                <div class="mts-modal-overlay" id="mts-modal-overlay">
                    <div class="mts-modal">
                        <div class="mts-modal-header">
                            <h3>📥 Download All Songs</h3>
                            <button class="mts-modal-close" id="mts-modal-close">&times;</button>
                        </div>
                        <div class="mts-modal-body">
                            <div class="mts-summary-text">
                                พบเพลงที่พร้อมดาวน์โหลด <strong>${songs.length}</strong> รายการ
                            </div>
                            <table class="mts-dl-table">
                                <thead>
                                    <tr>
                                        <th style="width: 50px;">Image</th>
                                        <th>Title</th>
                                        <th style="width: 200px;">Tags</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${songs.map(song => `
                                        <tr>
                                            <td><img class="song-thumb" src="${song.thumbUrl}" alt="" /></td>
                                            <td class="song-title">${song.title}</td>
                                            <td class="song-tags" style="font-size: 10px; color: #888;">${song.tags.substring(0, 50)}...</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                        <div class="mts-modal-footer">
                            <button class="mts-btn mts-btn-secondary" id="mts-modal-cancel">ยกเลิก</button>
                            <button class="mts-btn mts-btn-download" id="mts-modal-confirm">✅ ยืนยันดาวน์โหลด ${songs.length} เพลง</button>
                        </div>
                    </div>
                </div>
            `;

            // Insert modal into DOM
            const modalContainer = document.createElement('div');
            modalContainer.id = 'mts-modal-container';
            modalContainer.innerHTML = modalHtml;
            document.body.appendChild(modalContainer);

            // Attach event listeners
            document.getElementById('mts-modal-close').addEventListener('click', () => this.closeModal());
            document.getElementById('mts-modal-cancel').addEventListener('click', () => this.closeModal());
            document.getElementById('mts-modal-confirm').addEventListener('click', () => this.startBulkDownload());
            document.getElementById('mts-modal-overlay').addEventListener('click', (e) => {
                if (e.target.id === 'mts-modal-overlay') this.closeModal();
            });
        }

        /**
         * Close the modal
         */
        closeModal() {
            const modal = document.getElementById('mts-modal-container');
            if (modal) {
                modal.remove();
            }
        }

        /**
         * Start bulk download process
         */
        async startBulkDownload() {
            const songs = this.scannedSongs || [];
            this.closeModal();

            if (songs.length === 0) {
                MTS.State.addLog('No songs to download', 'warning');
                return;
            }

            MTS.State.addLog(`Starting download of ${songs.length} songs...`);
            this.elements.downloadBtn.disabled = true;
            this.elements.downloadBtn.textContent = '⏳ Downloading...';

            let successCount = 0;
            let failCount = 0;

            for (let i = 0; i < songs.length; i++) {
                const song = songs[i];
                MTS.State.setStepLabel(`Downloading ${i + 1}/${songs.length}: ${song.title}`);

                try {
                    const result = await MTS.Automation.sendToBackend(song, MTS.Api);
                    if (result) {
                        successCount++;
                        MTS.State.addLog(`✅ Saved: ${song.title}`, 'success');
                    } else {
                        failCount++;
                        MTS.State.addLog(`❌ Failed: ${song.title}`, 'error');
                    }
                } catch (e) {
                    failCount++;
                    MTS.State.addLog(`❌ Error: ${song.title} - ${e.message}`, 'error');
                }

                // Small delay between downloads
                await MTS.Automation.sleep(500);
            }

            MTS.State.setStepLabel('');
            MTS.State.addLog(`Download complete: ${successCount} success, ${failCount} failed`);
            this.elements.downloadBtn.disabled = false;
            this.elements.downloadBtn.textContent = '🔍 Scan Songs';
        }

        /**
         * Start bulk download programmatically (no modal)
         * Used when download mode is 'end'
         */
        async startBulkDownloadProgrammatic(songs) {
            if (!songs || songs.length === 0) {
                MTS.State.addLog('No songs to download', 'warning');
                return;
            }

            MTS.State.addLog(`Starting programmatic download of ${songs.length} songs...`);

            let successCount = 0;
            let failCount = 0;
            const delaySettings = this.getDelaySettings();

            for (let i = 0; i < songs.length; i++) {
                const song = songs[i];
                MTS.State.setStepLabel(`Downloading ${i + 1}/${songs.length}: ${song.title}`);

                try {
                    await MTS.Automation.downloadSingleSong(song);
                    successCount++;
                    MTS.State.addLog(`✅ Saved: ${song.title}`, 'success');
                } catch (e) {
                    failCount++;
                    MTS.State.addLog(`❌ Error: ${song.title} - ${e.message}`, 'error');
                }

                // Random delay between downloads
                const delay = this.randomDelay(delaySettings.stepDelayMin, delaySettings.stepDelayMax);
                await MTS.Automation.sleep(delay);
            }

            MTS.State.setStepLabel('');
            MTS.State.addLog(`Download complete: ${successCount} success, ${failCount} failed`);
        }
    }

    MTS.UIBuilder = UIBuilder;

})(window.MTSuno || (window.MTSuno = {}));
