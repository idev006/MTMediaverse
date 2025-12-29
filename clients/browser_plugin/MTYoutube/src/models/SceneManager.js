/**
 * SceneManager - Scene/Step Orchestrator Model
 * Manages the "Movie → Scenes → Steps" architecture
 * Each Step has fallback selectors for resilience
 * 
 * @memberof YouTubeUploader.Model
 */
(function (YTU) {
    'use strict';

    class SceneManager {
        constructor(stateManager, apiStub) {
            this.state = stateManager;
            this.api = apiStub;

            // Scene registry
            this.scenes = new Map();

            // Current execution context
            this.currentScene = null;
            this.currentStepIndex = 0;

            // Register all YouTube scenes
            this._registerScenes();
        }

        /**
         * Register all YouTube upload scenes
         */
        _registerScenes() {
            // Scene 1: Navigate to Upload
            this.registerScene('navigate', [
                {
                    name: 'Click Create Button',
                    selector: [
                        'ytcp-button-shape[innerText="Create"]', // Custom handler needed for innerText
                        '#create-icon',
                        'ytcp-button-shape#create-button'
                    ],
                    action: async (el) => {
                        // Special handling for finding button by text as per youtube.txt
                        const btns = Array.from(document.querySelectorAll('ytcp-button-shape'));
                        const createBtn = btns.find(b => b.innerText.trim() === 'Create');
                        if (createBtn) createBtn.click();
                        else throw new Error("Create button not found");
                    },
                    waitAfter: 1000
                },
                {
                    name: 'Click Upload Videos',
                    selector: 'tp-yt-paper-listbox#paper-list', // Context menu container
                    action: async () => {
                        const menuItems = Array.from(document.querySelectorAll('tp-yt-paper-item'));
                        const uploadBtn = menuItems.find(el => el.innerText.includes('Upload videos'));
                        if (uploadBtn) uploadBtn.click();
                        else throw new Error("Upload videos menu item not found");
                    },
                    waitAfter: 2000
                }
            ]);

            // Scene 2: Upload File
            this.registerScene('upload', [
                {
                    name: 'Wait for Upload Modal',
                    selector: '.ytcp-uploads-dialog', // From youtube.txt
                    action: 'waitFor',
                    waitAfter: 1000
                },
                {
                    name: 'Inject Video File',
                    selector: 'input[type="file"]',
                    action: 'injectFile',
                    waitAfter: 5000 // Wait for upload to start
                }
            ]);

            // Scene 3: Details (Title, Description, Kids, Tags)
            this.registerScene('details', [
                {
                    name: 'Fill Title',
                    selector: 'div[aria-label*="Add a title"]',
                    action: 'typeText', // Uses HumanLike typing
                    value: (p) => p.prod_name,
                    waitAfter: 1000
                },
                {
                    name: 'Fill Description',
                    selector: 'div[aria-label*="Tell viewers about your video"]',
                    action: 'typeText',
                    value: (p) => `${p.prod_name}\n\n${p.prod_desc || ''}`,
                    waitAfter: 1000
                },
                {
                    name: 'Set Not Made for Kids',
                    selector: 'tp-yt-paper-radio-button[name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]',
                    action: 'click',
                    waitAfter: 500
                },
                {
                    name: 'Show More Options',
                    selector: 'ytcp-button-shape#toggle-button', // "Show more"
                    action: async (el) => {
                        if (el.innerText.includes('Show more')) el.click();
                    },
                    optional: true, // Might already be open
                    waitAfter: 1000
                },
                {
                    name: 'Clear & Add Tags',
                    selector: 'input[placeholder="Add tag"]',
                    action: async (el, product) => {
                        // 1. Clear old tags (as per youtube.txt)
                        const container = document.querySelector('#tags-container');
                        if (container) {
                            // Find any delete button inside tags container
                            const deleteBtns = () => container.querySelectorAll('ytcp-chip #delete-button, ytcp-chip #delete-icon');
                            let btns = deleteBtns();
                            let safeGuard = 0;
                            while (btns.length > 0 && safeGuard++ < 50) {
                                btns[0].click();
                                await new Promise(r => setTimeout(r, 50)); // Small delay
                                btns = deleteBtns();
                            }
                        }

                        // 2. Add new tags
                        if (product.prod_tags) {
                            const tags = product.prod_tags.split(',').map(t => t.trim()).filter(t => t);
                            for (const tag of tags) {
                                el.focus();
                                // Simulate typing
                                el.value = tag;
                                el.dispatchEvent(new Event('input', { bubbles: true }));
                                await new Promise(r => setTimeout(r, 50));
                                // Press Enter
                                el.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', keyCode: 13, bubbles: true }));
                                await new Promise(r => setTimeout(r, 100));
                            }
                        }
                    },
                    waitAfter: 1000
                }
            ]);

            // Scene 4: Submit (Review -> Checks -> Visibility)
            this.registerScene('submit', [
                {
                    name: 'Go to Checks',
                    selector: 'ytcp-button-shape#next-button',
                    action: 'click',
                    waitAfter: 1000
                },
                {
                    name: 'Go to Visibility',
                    selector: 'ytcp-button-shape#next-button',
                    action: 'click',
                    waitAfter: 1000
                },
                {
                    name: 'Go to Publish', // Sometimes there's an extra step
                    selector: 'ytcp-button-shape#next-button',
                    action: 'click',
                    optional: true,
                    waitAfter: 1000
                },
                {
                    name: 'Select Public',
                    action: 'click',
                    waitAfter: 500
                },
                {
                    name: 'Click Publish/Save',
                    selectors: [
                        "#done-button",
                        "ytcp-button#done-button"
                    ],
                    action: 'click',
                    waitAfter: 3000
                }
            ]);
        }

        /**
         * Register a scene with its steps
         */
        registerScene(sceneName, steps) {
            this.scenes.set(sceneName, {
                name: sceneName,
                steps: steps
            });
        }

        /**
         * Execute a scene by name
         */
        async executeScene(sceneName, context = {}) {
            const scene = this.scenes.get(sceneName);
            if (!scene) {
                throw new Error(`Scene "${sceneName}" not found`);
            }

            this.currentScene = sceneName;
            this.state.addLog(`🎬 Scene: ${sceneName}`);

            for (let i = 0; i < scene.steps.length; i++) {
                if (this.state.shouldStop) {
                    throw new Error('Stopped by user');
                }

                this.currentStepIndex = i;
                const step = scene.steps[i];

                this.state.updateScene(sceneName, i + 1, step.name);
                this.state.addLog(`  📍 Step ${i + 1}: ${step.name}`);

                try {
                    await this.executeStep(step, context);
                } catch (error) {
                    if (step.optional) {
                        this.state.addLog(`  ⚠️ Optional step failed: ${error.message}`, 'warning');
                        continue;
                    }
                    throw error;
                }

                // Wait after step if specified
                if (step.waitAfter) {
                    await this._delay(step.waitAfter);
                }
            }

            this.state.addLog(`✅ Scene "${sceneName}" completed`);
        }

        /**
         * Execute a single step
         */
        async executeStep(step, context) {
            const { action, selectors, timeout = 10000 } = step;

            switch (action) {
                case 'click':
                    const clickEl = await this.findElement(selectors, timeout);
                    if (clickEl) {
                        clickEl.click();
                    } else {
                        throw new Error(`Element not found for: ${step.name}`);
                    }
                    break;

                case 'waitFor':
                    const waitEl = await this.findElement(selectors, timeout);
                    if (!waitEl) {
                        throw new Error(`Timeout waiting for: ${step.name}`);
                    }
                    break;

                case 'typeText':
                    const inputEl = await this.findElement(selectors, timeout);
                    if (inputEl) {
                        const text = context[step.dataKey] || '';
                        inputEl.focus();
                        document.execCommand('selectAll', false, null);
                        document.execCommand('insertText', false, text);
                    } else {
                        throw new Error(`Input not found for: ${step.name}`);
                    }
                    break;

                case 'injectFile':
                    const fileInput = await this.findElement(selectors, timeout);
                    if (fileInput && context.videoFile) {
                        const dt = new DataTransfer();
                        dt.items.add(context.videoFile);
                        fileInput.files = dt.files;
                        fileInput.dispatchEvent(new Event('change', { bubbles: true }));
                    } else {
                        throw new Error(`File input not found or no video for: ${step.name}`);
                    }
                    break;

                default:
                    this.state.addLog(`Unknown action: ${action}`, 'warning');
            }
        }

        /**
         * Find element using fallback selectors
         */
        async findElement(selectors, timeout = 10000) {
            const startTime = Date.now();

            while (Date.now() - startTime < timeout) {
                for (const selector of selectors) {
                    let element = null;

                    try {
                        // Check if XPath
                        if (selector.startsWith('//') || selector.startsWith('(')) {
                            const result = document.evaluate(
                                selector,
                                document,
                                null,
                                XPathResult.FIRST_ORDERED_NODE_TYPE,
                                null
                            );
                            element = result.singleNodeValue;
                        }
                        // Check for :has-text() pseudo selector
                        else if (selector.includes(':has-text(')) {
                            const match = selector.match(/(.+):has-text\(['"](.+)['"]\)/);
                            if (match) {
                                const [, baseSelector, text] = match;
                                const elements = document.querySelectorAll(baseSelector);
                                element = Array.from(elements).find(el =>
                                    el.textContent.includes(text)
                                );
                            }
                        }
                        // Standard CSS selector
                        else {
                            element = document.querySelector(selector);
                        }

                        if (element && this._isVisible(element)) {
                            return element;
                        }
                    } catch (e) {
                        // Continue to next selector
                    }
                }

                // Wait before retry
                await this._delay(300);
            }

            return null;
        }

        /**
         * Check if element is visible
         */
        _isVisible(element) {
            if (!element) return false;
            const style = window.getComputedStyle(element);
            return (
                element.offsetWidth > 0 &&
                element.offsetHeight > 0 &&
                style.display !== 'none' &&
                style.visibility !== 'hidden'
            );
        }

        /**
         * Delay helper
         */
        _delay(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
        }

        /**
         * Get all registered scene names
         */
        getSceneNames() {
            return Array.from(this.scenes.keys());
        }
    }

    // Register with namespace
    YTU.SceneManager = SceneManager;

})(window.YouTubeUploader || (window.YouTubeUploader = {}));
