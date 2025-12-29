/**
 * PageHandler - YouTube Studio DOM interactions
 * Higher-level page operations using SceneManager
 * 
 * @memberof YouTubeUploader.Utils
 */
(function (YTU) {
    'use strict';

    class PageHandler {
        constructor(humanLike, stateManager) {
            this.human = humanLike;
            this.state = stateManager;

            // YouTube Studio selectors (fallbacks defined in SceneManager)
            this.selectors = {
                // Upload dialog
                uploadDialog: '.ytcp-uploads-dialog',
                fileInput: 'input[type="file"]',

                // Form elements
                titleInput: "ytcp-social-suggestions-textbox[id='title'] #textbox",
                descriptionInput: "ytcp-social-suggestions-textbox[id='description'] #textbox",

                // Buttons
                nextButton: '#next-button',
                doneButton: '#done-button',

                // Spinners
                spinners: '[data-icon="Loading"], .loading, [class*="spinner"]'
            };
        }

        /**
         * Check if element is visible
         */
        isElementVisible(element) {
            if (!element) return false;
            const style = window.getComputedStyle(element);
            return (element.offsetWidth > 0 || element.offsetHeight > 0) &&
                style.display !== 'none' && style.visibility !== 'hidden';
        }

        /**
         * Wait for page to be ready (no spinners)
         */
        async waitForPageReady(timeout = 30000) {
            const startTime = Date.now();
            while (Date.now() - startTime < timeout) {
                if (this.state.shouldStop) throw new Error('Stopped');
                const spinners = document.querySelectorAll(this.selectors.spinners);
                if (Array.from(spinners).filter(s => this.isElementVisible(s)).length === 0) {
                    await this.human.sleep(500);
                    return true;
                }
                await this.human.sleep(300);
            }
            return true;
        }

        /**
         * Wait for element with timeout
         */
        waitForElement(selector, options = {}) {
            const { timeout = 30000, checkReady = true, pollInterval = 500 } = options;

            return new Promise((resolve, reject) => {
                const startTime = Date.now();
                const check = setInterval(() => {
                    if (this.state.shouldStop) {
                        clearInterval(check);
                        reject(new Error('Stopped by user'));
                        return;
                    }

                    let element;
                    if (selector.startsWith('//') || selector.startsWith('(')) {
                        const result = document.evaluate(selector, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                        element = result.singleNodeValue;
                    } else {
                        element = document.querySelector(selector);
                    }

                    if (element && (!checkReady || this.isElementVisible(element))) {
                        clearInterval(check);
                        resolve(element);
                        return;
                    }

                    if (Date.now() - startTime > timeout) {
                        clearInterval(check);
                        reject(new Error(`Timeout: ${selector}`));
                    }
                }, pollInterval);
            });
        }

        /**
         * Check and handle any modal dialogs
         */
        async handleModals() {
            try {
                // Check for "Exit" confirmation
                const exitModal = document.querySelector('div[role="dialog"][aria-modal="true"]');
                if (exitModal) {
                    const exitBtn = Array.from(exitModal.querySelectorAll('button'))
                        .find(btn => btn.textContent.trim().toLowerCase() === 'exit');
                    if (exitBtn) {
                        await this.human.humanClick(exitBtn);
                        await this.human.sleep(1000);
                        return true;
                    }
                }
            } catch (e) {
                // Silent fail
            }
            return false;
        }

        /**
         * Clear any existing draft
         */
        async clearDraft() {
            try {
                const discardBtn = document.querySelector('button:has-text("Discard")');
                if (discardBtn && this.isElementVisible(discardBtn)) {
                    await this.human.humanClick(discardBtn);
                    await this.human.sleep(1000);
                    this.state.addLog('🗑️ Cleared draft');
                    return true;
                }
            } catch (e) {
                // No draft to clear
            }
            return false;
        }
    }

    // Register with namespace
    YTU.PageHandler = PageHandler;

})(window.YouTubeUploader || (window.YouTubeUploader = {}));
