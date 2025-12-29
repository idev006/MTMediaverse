/**
 * AppViewModel - Main ViewModel (MVVM)
 * Binds Model (StateManager, SceneManager) to View (Vue UI)
 * Orchestrates the upload workflow
 * 
 * @memberof YouTubeUploader
 */
(function (YTU) {
    'use strict';

    class AppViewModel {
        constructor(stateManager, sceneManager, apiStub, pageHandler) {
            this.state = stateManager;
            this.scene = sceneManager;
            this.api = apiStub;
            this.page = pageHandler;

            // Bind API client code
            this.api.setClientCode(this.state.config.clientCode);
        }

        // ============================================
        // SERVER OPERATIONS
        // ============================================

        async checkServer() {
            this.state.addLog('🔍 Checking server...');
            const result = await this.api.healthCheck();
            this.state.setServerStatus(result.success);
            this.state.addLog(
                result.success
                    ? `✅ Server: ${result.videoCount} videos`
                    : '❌ Server offline',
                result.success ? 'info' : 'error'
            );
            return result;
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
                return result;
            }
            this.state.addLog(`❌ Video failed: ${result.error}`, 'error');
            return null;
        }

        // ============================================
        // WORKFLOW ORCHESTRATION
        // ============================================

        async processProduct(product, isFirst = false) {
            this.state.setCurrentProduct(product);
            this.state.addLog(`\n${'═'.repeat(35)}`);
            this.state.addLog(`🎯 ${product.prod_code}`);

            const maxRetries = 2;

            for (let attempt = 1; attempt <= maxRetries + 1; attempt++) {
                try {
                    if (attempt > 1) {
                        this.state.addLog(`🔄 Retry ${attempt - 1}/${maxRetries}...`, 'warning');
                        await this._delay(2000 * Math.pow(2, attempt - 2));
                    }

                    // Product delay (skip for first)
                    if (!isFirst && attempt === 1) {
                        await this._productDelay();
                    }

                    // Step 1: Fetch video
                    this.state.updateScene('fetch', 1, 'Fetching video...');
                    const videoResult = await this.fetchVideo(product.prod_code);
                    if (!videoResult) throw new Error('Video fetch failed');

                    // Context for scenes
                    const context = {
                        videoFile: videoResult.file,
                        title: product.prod_title || product.prod_code,
                        description: product.prod_descr || '',
                        tags: product.prod_tags || ''
                    };

                    // Step 2: Navigate to upload
                    await this.scene.executeScene('navigate', context);
                    await this._stepDelay();

                    // Step 3: Upload video
                    await this.scene.executeScene('upload', context);
                    await this._delay(3000); // Wait for YouTube to process

                    // Step 4: Fill details
                    await this.scene.executeScene('details', context);
                    await this._stepDelay();

                    // Step 5: Submit
                    if (this.state.config.autoPost) {
                        await this.scene.executeScene('submit', context);
                    } else {
                        this.state.addLog('⏸️ Auto-post disabled, waiting...');
                    }

                    this.state.addLog(`🎉 ${product.prod_code} DONE!`);
                    return { success: true };

                } catch (error) {
                    this.state.addLog(`❌ Attempt ${attempt} failed: ${error.message}`, 'error');

                    if (attempt >= maxRetries + 1) {
                        return { success: false, error: error.message };
                    }
                }
            }

            return { success: false, error: 'Max retries exceeded' };
        }

        async startBatch() {
            this.state.startProcessing();
            await this.api.clearStop();

            this.state.addLog('🚀 Starting automation...');
            this.state.initProgress(0);

            let processed = 0, success = 0, failed = 0;
            let isFirst = true;

            // Main loop
            while (!this.state.shouldStop) {
                // Check pause
                await this._waitWhilePaused();
                if (this.state.shouldStop) break;

                // Fetch if queue empty
                if (this.state.products.length === 0) {
                    const fetchResult = await this.fetchProducts();
                    if (!fetchResult.success || fetchResult.products.length === 0) {
                        this.state.addLog('✅ All jobs completed!', 'success');
                        break;
                    }
                }

                // Process next product
                const product = this.state.shiftProduct();
                const result = await this.processProduct(product, isFirst);
                isFirst = false;

                processed++;
                result.success ? success++ : failed++;
                this.state.updateProgress(processed, success, failed);

                // Report to server
                const reportData = await this.api.reportUpload(
                    product.prod_code,
                    result.success ? 'success' : 'failed',
                    result.error || ''
                );

                if (reportData.shouldStop) {
                    this.state.stopProcessing();
                    break;
                }

                await this._waitWhilePaused();
            }

            this.state.finishProcessing();
            this.state.addLog(`\n🎉 Done: ${success}/${processed}, Failed: ${failed}`);
        }

        stopBatch() {
            this.state.stopProcessing();
            this.state.addLog('🛑 Stopping...', 'warning');
        }

        togglePause() {
            if (this.state.isPaused) {
                this.state.resumeProcessing();
                this.state.addLog('▶️ Resumed');
            } else {
                this.state.pauseProcessing();
                this.state.addLog('⏸️ Paused');
            }
        }

        async resetAll() {
            await this.api.resetStatus();
            this.state.addLog('✅ Reset complete');
        }

        // ============================================
        // HELPERS
        // ============================================

        async _waitWhilePaused() {
            while (this.state.isPaused && !this.state.shouldStop) {
                this.state.updateScene('paused', 0, '⏸️ Paused - waiting...');
                await this._delay(1000);
            }
        }

        async _productDelay() {
            const { min, max } = this.state.config.productDelay;
            const delay = Math.floor(Math.random() * (max - min + 1)) + min;
            this.state.addLog(`🎯 Product delay: ${(delay / 1000).toFixed(1)}s`);
            await this._delay(delay);
        }

        async _stepDelay() {
            const { min, max } = this.state.config.stepDelay;
            const delay = Math.floor(Math.random() * (max - min + 1)) + min;
            await this._delay(delay);
        }

        _delay(ms) {
            return new Promise(r => setTimeout(r, ms));
        }
    }

    // Register with namespace
    YTU.AppViewModel = AppViewModel;

})(window.YouTubeUploader || (window.YouTubeUploader = {}));
