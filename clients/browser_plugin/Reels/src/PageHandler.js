/**
 * PageHandler - DOM manipulation for Facebook Reels
 */
(function (FBU) {
    'use strict';

    class PageHandler {
        constructor(humanLike) {
            this.human = humanLike;
            this.selectors = {
                // Step 1: Reel Button (Reference)
                // div[aria-label="Reel"][role="button"]
                createReelButton: 'div[aria-label="Reel"][role="button"]',

                // Step 2: Create Reel Popup
                createReelHeader: 'h2 span', // Checks for "Create reel" text

                // 2.1 Video Input
                fileInput: 'input[type="file"][accept*="video"]',

                // 2.2 Next Button
                nextButton: 'div[aria-label="Next"][role="button"]',

                // Step 3: Description Input
                // role="textbox" aria-placeholder="Describe your reel..."
                descriptionInput: 'div[role="textbox"][aria-placeholder="Describe your reel..."][contenteditable="true"]',

                // Old Upload Button (reference only, removing usage if redundant)
                uploadButton: 'div[aria-label="Upload video for reel"][role="button"]'
            };
        }

        async waitForElement(selector, timeout = 30000) {
            return new Promise((resolve, reject) => {
                const startTime = Date.now();
                const interval = setInterval(() => {
                    const el = document.querySelector(selector);
                    if (el) {
                        clearInterval(interval);
                        resolve(el);
                        return;
                    }
                    if (Date.now() - startTime > timeout) {
                        clearInterval(interval);
                        reject(new Error(`Timeout finding ${selector}`));
                    }
                }, 500);
            });
        }

        async isCreateReelPopupVisible() {
            // Check for H2 header "Create reel"
            const headers = Array.from(document.querySelectorAll('h2 span'));
            return headers.some(h => h.textContent.trim() === 'Create reel');
        }

        async handleStep2_InjectVideo(videoFile) {
            console.log('[FBU] Starting Step 2: Inject Video');

            const fileInput = await this.waitForElement(this.selectors.fileInput);
            if (!fileInput) throw new Error('File input not found');

            console.log('[FBU] Found file input, injecting...');

            const dt = new DataTransfer();
            dt.items.add(videoFile);
            fileInput.files = dt.files;

            // Dispatch events
            fileInput.dispatchEvent(new Event('change', { bubbles: true }));
            fileInput.dispatchEvent(new Event('input', { bubbles: true }));

            console.log('[FBU] Video injected.');
        }

        async handleStep2_ClickNext() {
            console.log('[FBU] Waiting for "Next" button...');
            // Wait up to 60s for upload processing
            const nextBtn = await this.waitForElement(this.selectors.nextButton, 60000);

            if (nextBtn) {
                console.log('[FBU] Next button found, clicking...');
                await this.human.humanClick(nextBtn);
                return true;
            } else {
                throw new Error("Next button not found after timeout");
            }
        }

        async handleStep3_FillDescription(text) {
            console.log('[FBU] Looking for description input...');
            const input = await this.waitForElement(this.selectors.descriptionInput);

            if (input) {
                console.log(`[FBU] Found description input.`);

                // 0. Store text in clipboard
                try {
                    await navigator.clipboard.writeText(text);
                    console.log('[FBU] Copied text to clipboard');
                } catch (err) {
                    console.warn('[FBU] Clipboard write failed:', err);
                }

                // 1. Click on reels description area (Focus)
                await this.human.humanClick(input);
                input.focus();

                // 2. CTRL+A then Delete
                // Simulating via execCommand is most reliable for contenteditable
                document.execCommand('selectAll', false, null);
                await this.human.sleep(200);
                document.execCommand('delete', false, null);
                await this.human.sleep(200);

                // 3. Paste it
                // We use insertText which acts like a paste for text content
                // Attempt actual paste first (requires permission), fallback to insertText
                try {
                    const success = document.execCommand('paste');
                    if (!success) throw new Error('Paste command failed');
                    console.log('[FBU] Pasted via execCommand');
                } catch (e) {
                    console.log('[FBU] Fallback to insertText');
                    document.execCommand('insertText', false, text);
                }

                // Trigger events to be safe
                input.dispatchEvent(new Event('input', { bubbles: true }));

                return true;
            } else {
                throw new Error("Description input not found");
            }
        }

        async handleStep1_ClickCreateReel() {
            console.log('[FBU] Looking for "Reel" button...');
            // Try specific selector from webpart first
            let reelBtn = await this.waitForElement(this.selectors.createReelButton, 5000).catch(() => null);

            // Fallback: Look for any text "Reel" inside a button role if exact selector fails
            if (!reelBtn) {
                console.log('[FBU] Exact match not found, trying text match...');
                const buttons = Array.from(document.querySelectorAll('[role="button"]'));
                reelBtn = buttons.find(b => b.innerText.includes('Reel') || b.getAttribute('aria-label') === 'Reel');
            }

            if (reelBtn) {
                console.log('[FBU] Found Reel button, clicking...');
                await this.human.humanClick(reelBtn);
                return true;
            } else {
                throw new Error('Reel button not found');
            }
        }
    }

    FBU.PageHandler = PageHandler;
})(window.FBReelsUploader || (window.FBReelsUploader = {}));
