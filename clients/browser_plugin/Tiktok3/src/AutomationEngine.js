/**
 * AutomationEngine - Main automation logic controller
 * Orchestrates the upload workflow
 * 
 * @memberof TikTokUploader
 */
(function (TTU) {
    'use strict';

    class AutomationEngine {
        constructor(state, api, pageHandler) {
            this.state = state;
            this.api = api;
            this.page = pageHandler;
        }

        async checkServer() {
            this.state.addLog('🔍 Checking server...');
            const result = await this.api.healthCheck();
            this.state.setServerStatus(result.success);
            this.state.addLog(result.success ? `✅ Server: ${result.videoCount} videos` : '❌ Server offline', result.success ? 'info' : 'error');
            return result;
        }

        startHeartbeatLoop() {
            this.state.addLog('💓 Starting Heartbeat...');
            this.heartbeatFailCount = 0; // Initialize failure counter

            const loop = async () => {
                try {
                    // Only check if we have a client code configured
                    if (this.state.config.clientCode) {
                        await this.api.checkStatus();

                        // Success - reset counter and update status
                        if (this.heartbeatFailCount > 0) {
                            this.state.addLog('✅ Backend reconnected!', 'success');
                        }
                        this.heartbeatFailCount = 0;
                        this.state.setServerStatus(true);
                    }
                } catch (e) {
                    // Heartbeat failed
                    this.heartbeatFailCount++;
                    this.state.setServerStatus(false);

                    if (this.heartbeatFailCount === 1) {
                        this.state.addLog(`⚠️ Heartbeat failed (1/3)`, 'warning');
                    } else if (this.heartbeatFailCount === 2) {
                        this.state.addLog(`⚠️ Heartbeat failed (2/3)`, 'warning');
                    } else if (this.heartbeatFailCount >= 3) {
                        this.state.addLog(`❌ Backend Offline! Auto-pausing...`, 'error');

                        // Auto-pause if processing
                        if (this.state.isProcessing && !this.state.isPaused) {
                            this.state.pauseProcessing();
                            this.state.addLog(`⏸️ Automation paused due to backend offline`, 'error');
                        }
                    }
                }

                // Schedule next
                const interval = this.state.config.heartbeatInterval || 5000;
                setTimeout(loop, interval);
            };
            loop();
        }

        startProgressBackup() {
            /**
             * Auto-save progress every 30s to localStorage
             * Enables session recovery after browser refresh
             */
            this.state.addLog('💾 Starting Progress Backup...');

            const backup = () => {
                try {
                    if (this.state.isProcessing || this.state.products.length > 0) {
                        const snapshot = {
                            products: this.state.products,
                            processed: this.state.progress.completed,
                            success: this.state.progress.success,
                            failed: this.state.progress.failed,
                            total: this.state.progress.total,
                            timestamp: Date.now(),
                            clientCode: this.state.config.clientCode
                        };

                        localStorage.setItem('ttu_session_backup', JSON.stringify(snapshot));
                        console.log('[ProgressBackup] Saved:', snapshot.products.length, 'items');
                    }
                } catch (e) {
                    console.error('[ProgressBackup] Failed:', e);
                }

                // Schedule next (30s)
                setTimeout(backup, 30000);
            };

            backup(); // First backup immediately
        }

        loadSessionBackup() {
            /**
             * Attempt to restore previous session from localStorage
             * Returns backup data if found and valid (< 1 hour old)
             */
            try {
                const saved = localStorage.getItem('ttu_session_backup');
                if (!saved) return null;

                const backup = JSON.parse(saved);
                const age = Date.now() - backup.timestamp;

                // Expire after 1 hour (3600000 ms)
                if (age > 3600000) {
                    this.state.addLog('⚠️ Session backup too old (>1h), discarding', 'warning');
                    localStorage.removeItem('ttu_session_backup');
                    return null;
                }

                // Validate client code match
                if (backup.clientCode !== this.state.config.clientCode) {
                    this.state.addLog('⚠️ Session backup belongs to different client, discarding', 'warning');
                    return null;
                }

                this.state.addLog(`📂 Found session backup: ${backup.products.length} items (${Math.round(age / 1000)}s ago)`, 'info');
                return backup;

            } catch (e) {
                console.error('[SessionBackup] Load failed:', e);
                return null;
            }
        }

        clearSessionBackup() {
            localStorage.removeItem('ttu_session_backup');
            this.state.addLog('🗑️ Session backup cleared');
        }

        startModalWatcher() {
            /**
             * Periodic Modal Watcher (Every 2 seconds)
             * Automatically detects and handles:
             * - Exit confirmation dialog
             * - Discard draft dialog
             */
            this.state.addLog('👁️ Starting Modal Watcher...');

            this.modalWatcherInterval = setInterval(async () => {
                if (this.state.isProcessing && !this.state.isPaused) {
                    // Check for exit dialog
                    await this.page._checkExitDialog();
                }
            }, 2000); // Every 2 seconds
        }

        stopModalWatcher() {
            if (this.modalWatcherInterval) {
                clearInterval(this.modalWatcherInterval);
                this.modalWatcherInterval = null;
                this.state.addLog('👁️ Modal Watcher stopped');
            }
        }


        async fetchProducts() {
            this.state.addLog('📦 Fetching products...');
            const result = await this.api.fetchProducts();
            if (result.success) {
                this.state.setProducts(result.products);
                this.state.addLog(`✅ Got ${result.products.length} pending`);
            } else {
                this.state.addLog('❌ Fetch failed', 'error');
            }
            return result;
        }

        async fetchVideo(prodCode) {
            this.state.addLog(`📥 Fetching video: ${prodCode}...`);
            const result = await this.api.fetchVideo(prodCode);
            if (result.success) {
                this.state.addLog(`✅ Video: ${result.sizeMb?.toFixed(2)}MB`);
                return result.file;
            }
            this.state.addLog(`❌ Video failed: ${result.error}`, 'error');
            return null;
        }

        async productDelay() {
            const { min, max } = this.state.config.productDelay;
            const delay = Math.floor(Math.random() * (max - min + 1)) + min;
            this.state.addLog(`🎯 Product delay: ${(delay / 1000).toFixed(1)}s`);
            await new Promise(r => setTimeout(r, delay));
        }

        async stepDelay() {
            const { min, max } = this.state.config.stepDelay;
            const delay = Math.floor(Math.random() * (max - min + 1)) + min;
            await new Promise(r => setTimeout(r, delay));
        }

        async processProduct(product, isFirst = false) {
            this.state.setCurrentProduct(product);
            this.state.addLog(`\n${'═'.repeat(35)}`);
            this.state.addLog(`🎯 ${product.prod_code}`);

            const maxRetries = this.state.config.maxRetries || 2;

            for (let attempt = 1; attempt <= maxRetries + 1; attempt++) {
                try {
                    if (attempt > 1) {
                        this.state.addLog(`🔄 Retry ${attempt - 1}/${maxRetries}...`, 'warning');
                        // Exponential backoff: 2s, 4s, 8s...
                        const backoff = Math.min(2000 * Math.pow(2, attempt - 2), 10000);
                        await new Promise(r => setTimeout(r, backoff));
                    }

                    // Skip delay for first product
                    if (!isFirst && attempt === 1) {
                        await this.productDelay();
                    } else if (attempt === 1) {
                        this.state.addLog('⚡ First product - no delay');
                    }

                    this.state.updateStep(1, 'Fetching video...');
                    const videoFile = await this.fetchVideo(product.prod_code);
                    if (!videoFile) throw new Error('Video fetch failed');
                    await this.stepDelay();

                    this.state.updateStep(2, 'Page 1: Upload');
                    await this.page.handlePage1_ClickUpload();
                    await this.stepDelay();

                    this.state.updateStep(3, 'Page 2: Inject video');
                    await this.page.handlePage2_InjectVideo(videoFile);

                    // Wait for TikTok to process video (use videoProcessDelay from config)
                    const { min = 2000, max = 5000 } = this.state.config.videoProcessDelay || {};
                    const processDelay = Math.max(2000, min + Math.random() * (max - min));
                    await new Promise(r => setTimeout(r, processDelay));

                    this.state.updateStep(4, 'Page 3: Fill & Submit');
                    await this.page.handlePage3_FillDetails(product);

                    this.state.addLog(`🎉 ${product.prod_code} DONE!`);
                    return { success: true };

                } catch (error) {
                    this.state.addLog(`❌ Attempt ${attempt} failed: ${error.message}`, 'error');

                    if (attempt >= maxRetries + 1) {
                        // Final failure
                        return { success: false, error: error.message };
                    }
                    // Continue to next retry
                }
            }

            // Should never reach here but just in case
            return { success: false, error: 'Max retries exceeded' };
        }

        /**
         * Wait while paused
         */
        async waitWhilePaused() {
            while (this.state.isPaused && !this.state.shouldStop) {
                this.state.updateStep(0, '⏸️ Paused - waiting...');
                await new Promise(r => setTimeout(r, 1000));
            }
        }

        async startBatch() {
            // REMOVED: Initial empty check to allow polling mode starting empty

            this.state.startProcessing();
            await this.api.clearStop();

            // Start Session
            this.state.addLog('🔄 Starting session...');
            const sessRes = await this.api.startSession();
            if (sessRes.success) {
                this.state.addLog(`✅ Session: ${sessRes.session.session_id}`);
            } else {
                this.state.addLog('⚠️ Failed to start session tracking', 'warning');
            }

            this.state.initProgress(0); // Indeterminate or Accumulating
            this.state.addLog('🚀 Starting automation loop...');

            // Start progress backup loop (Auto-save every 30s)
            this.startProgressBackup();

            // Start modal watcher (Check modals every 2s)
            this.startModalWatcher();

            let processed = 0, success = 0, failed = 0;
            let isFirst = true;

            // OUTER LOOP: Continuous Fetching
            while (!this.state.shouldStop) {
                // Check pause
                await this.waitWhilePaused();
                if (this.state.shouldStop) break;

                // 1. Fetch Batch (ONLY IF QUEUE IS EMPTY)
                if (this.state.products.length === 0) {
                    const fetchResult = await this.fetchProducts();
                    if (!fetchResult.success || fetchResult.products.length === 0) {
                        // NO POLLING: Finish immediately if no jobs
                        this.state.addLog('✅ All jobs completed (No new items)', 'success');
                        this.state.shouldStop = true; // Signal to break outer loop
                        break;
                    }
                    this.state.addLog(`📦 Batch loaded: ${this.state.products.length} items`);
                } else {
                    this.state.addLog(`▶️ Processing existing queue: ${this.state.products.length} items`);
                }

                // INNER LOOP: Process Batch
                while (this.state.products.length > 0 && !this.state.shouldStop) {
                    // Check pause before processing
                    await this.waitWhilePaused();
                    if (this.state.shouldStop) break;

                    const product = this.state.shiftProduct();
                    const result = await this.processProduct(product, isFirst);
                    isFirst = false; // Only first is true for first product

                    processed++;
                    result.success ? success++ : failed++;
                    this.state.updateProgress(processed, success, failed);

                    const reportData = await this.api.reportUpload(product.prod_code, result.success ? 'success' : 'failed', result.error || '');

                    if (reportData.shouldStop) {
                        this.state.stopProcessing();
                        break;
                    }

                    // Check pause after processing
                    await this.waitWhilePaused();
                    if (this.state.shouldStop) break;

                    if (this.state.products.length > 0 && !this.state.shouldStop) {
                        // Inter-product delay (use productDelay config, minimum 2s)
                        const { min, max } = this.state.config.productDelay;
                        const interDelay = Math.max(2000, min + Math.random() * (max - min));
                        await new Promise(r => setTimeout(r, interDelay));

                        try {
                            await this.page.waitForElement(this.page.selectors.uploadButton, { timeout: 30000 });
                        } catch (e) {
                            const { min: sMin, max: sMax } = this.state.config.stepDelay || { min: 300, max: 500 };
                            await new Promise(r => setTimeout(r, sMin + Math.random() * (sMax - sMin)));
                        }
                    }
                } // End Inner Loop
            } // End Outer Loop

            // Stop modal watcher
            this.stopModalWatcher();

            this.state.finishProcessing();
            this.state.updateStep(0, this.state.shouldStop ? 'Stopped' : 'Completed ✓');
            this.state.addLog(`\n🎉 Done: ${success}/${processed}, Failed: ${failed}`);
        }

        stopBatch() {
            this.state.stopProcessing();
            this.state.addLog('🛑 Stopping...', 'warning');
        }

        async resetAll() {
            await this.api.resetStatus();
            this.state.addLog('✅ Reset complete');
        }
    }

    // Register with namespace
    TTU.AutomationEngine = AutomationEngine;

})(window.TikTokUploader || (window.TikTokUploader = {}));
