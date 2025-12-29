/**
 * AutomationEngine - Orchestrates the steps
 */
(function (FBU) {
    'use strict';

    class AutomationEngine {
        constructor() {
            this.human = new FBU.HumanLike();
            this.pageHandle = new FBU.PageHandler(this.human);
            this.initialized = false;
        }

        init() {
            if (this.initialized) return;
            this.initialized = true;
            console.log('[FBU] Automation Engine Initialized');

            // Listen for commands? Or auto-run?
            // Since this is a dev test, maybe auto-run step 2 if we are on the page?
            // User said "Working steps start from Step 2".
            // We'll expose a global method to trigger it for testing.

            window.FBU_RunStep2 = (videoUrl) => this.runStep2(videoUrl);
        }

        async getTestVideoFile(url) {
            const response = await fetch(url);
            const blob = await response.blob();
            return new File([blob], "video.mp4", { type: "video/mp4" });
        }

        async runStep2(prodCode) {
            this.log(`Running Step 2 for ${prodCode || 'TEST'}...`);
            try {
                // Fetch from BE if not provided
                let videoFile;

                // Request from background
                this.log('Requesting video from background...');
                const codeToFetch = prodCode || 'TEST';

                const response = await chrome.runtime.sendMessage({ action: 'getVideo', prodCode: codeToFetch });
                if (response.success && response.data) {
                    this.log(`Video received: ${response.data.filename || 'Unknown'} (${response.data.size_mb || '?'} MB)`);

                    const base64Data = response.data.payload;
                    if (!base64Data) throw new Error("Server response missing 'payload' (base64 video)");

                    this.log('Converting Base64 to File...');

                    // Robust conversion: atob + Uint8Array (Matches Tiktok3)
                    // Avoids 'Failed to fetch' on large data URIs
                    const byteCharacters = atob(base64Data);
                    const byteNumbers = new Array(byteCharacters.length);
                    for (let i = 0; i < byteCharacters.length; i++) {
                        byteNumbers[i] = byteCharacters.charCodeAt(i);
                    }
                    const byteArray = new Uint8Array(byteNumbers);
                    const blob = new Blob([byteArray], { type: 'video/mp4' });

                    videoFile = new File([blob], response.data.filename || "video.mp4", { type: "video/mp4" });

                    // Store metadata for Step 4
                    this.currentVideoMetadata = {
                        prodCode: prodCode,
                        description: response.data.prod_descr || '',
                        tags: response.data.prod_tags || ''
                    };

                    this.log(`Conversion complete. Metadata: ${this.currentVideoMetadata.description.substring(0, 20)}...`);

                } else {
                    throw new Error("Could not get video from BE: " + (response.error || 'Unknown error'));
                }

                await this.pageHandle.handleStep2_InjectVideo(videoFile);
                this.log('Video injected. Waiting for upload to process...');

                // 2.2 First Next Click
                await this.pageHandle.handleStep2_ClickNext();
                this.log('Clicked Next 1 -> Moved to Next Page');

                // Wait for page transition
                await this.human.sleep(2000);

                // Step 3: Second Next Click
                this.log('Waiting for Second Next button...');
                await this.pageHandle.handleStep2_ClickNext();
                this.log('Clicked Next 2 -> Moved to Details Page');

                await this.human.sleep(2000);

                // Step 4: Fill Description & Tags (Final Page)
                let description = '';
                if (this.currentVideoMetadata) {
                    description = `${this.currentVideoMetadata.description}\n\n${this.currentVideoMetadata.tags}`;
                } else {
                    description = `Product: ${prodCode}\n\n#Reels #Trending #Viral`;
                }

                this.log('Filling Description & Tags...');
                await this.pageHandle.handleStep3_FillDescription(description);
                this.log('Description Filled');

                this.log('Sequence Complete. Ready to Post.');

            } catch (e) {
                console.error('[FBU] Step 2 Failed:', e);
                this.log(`Step 2 Failed: ${e.message}`, 'error');
                throw e; // Propagate to App
            }
        }

        log(msg, type = 'info') {
            console.log(`[FBU] ${msg}`);
            // App overwrites this to show in UI
        }

        async runFullFlow() {
            console.log('[FBU] Starting Full Flow...');
            try {
                // Step 1: Open Popup
                await this.pageHandle.handleStep1_ClickCreateReel();

                // Wait for popup
                await this.human.sleep(2000);

                // Step 2: Inject
                await this.runStep2();

            } catch (e) {
                console.error('[FBU] Full Flow Failed:', e);
            }
        }
    }

    FBU.AutomationEngine = AutomationEngine;
})(window.FBReelsUploader || (window.FBReelsUploader = {}));
