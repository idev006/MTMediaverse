/**
 * PageHandler - DOM manipulation and page navigation
 * Handles TikTok page-specific element interactions
 * 
 * @memberof TikTokUploader
 */
(function (TTU) {
    'use strict';

    class PageHandler {
        constructor(humanLike, state) {
            this.human = humanLike;
            this.state = state;

            this.selectors = {
                uploadButton: 'button[data-tt="Sidebar_Sidebar_Button"]',
                selectVideoButton: 'button[data-e2e="select_video_button"]',
                fileInput: 'input[type="file"][accept*="video"]',
                postButton: 'button[data-e2e="post_video_button"]',
                captionEditor: '[data-e2e="caption_container"] .public-DraftEditor-content[contenteditable="true"]',
                visibilityContainer: '[data-e2e="video_visibility_container"]',
                spinners: '[data-icon="Loading"], .loading, [class*="spinner"]'
            };
        }

        isElementVisible(element) {
            if (!element) return false;
            const style = window.getComputedStyle(element);
            return (element.offsetWidth > 0 || element.offsetHeight > 0) &&
                style.display !== 'none' && style.visibility !== 'hidden';
        }

        isButtonEnabled(button) {
            if (!button) return false;
            return button.getAttribute('aria-disabled') !== 'true' &&
                button.getAttribute('data-disabled') !== 'true' &&
                !button.disabled &&
                !button.classList.contains('Button__root--loading-true');
        }

        isButtonReady(button) {
            return this.isElementVisible(button) && this.isButtonEnabled(button);
        }

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

                    if (element && (!checkReady || this.isButtonReady(element))) {
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

        async handlePage1_ClickUpload() {
            this.state.addLog('📍 Page 1: Upload');

            // Check for potential exit confirmation from previous cycle
            await this._checkExitDialog();

            const uploadBtn = await this.waitForElement(this.selectors.uploadButton);

            const { min = 300, max = 500 } = this.state.config.stepDelay || {};
            await this.human.randomDelay(min, max);
            await this.human.humanClick(uploadBtn);

            await this.human.randomDelay(min, max);
            await this._checkExitDialog(); // Check again after click just in case

            this.state.addLog('✅ Clicked Upload');
            return true;
        }

        async handlePage2_InjectVideo(videoFile) {
            this.state.addLog('📍 Page 2: Select Video');
            await this.waitForPageReady();

            // Verify we're on the correct page (has "Select videos" button)
            const selectVideosXPath = "//button[@role='button'][@type='button'][.//text()='Select videos']";

            try {
                const selectVideosBtn = await this.waitForElement(selectVideosXPath, {
                    timeout: 15000,
                    checkReady: false // Just check existence, not enabled state
                });
                this.state.addLog('✅ Verified: On video upload page');
            } catch (e) {
                this.state.addLog('⚠️ Warning: "Select videos" button not found, continuing anyway...', 'warning');
            }

            // Clear local draft first (if exists)
            await this._clearLocalDraft();

            // Loop check for Discard dialogs/buttons until none remain
            // Important: Do this BEFORE trying to inject video
            let discardAttempts = 0;
            const maxDiscardAttempts = 3;

            while (discardAttempts < maxDiscardAttempts) {
                const discarded = await this._checkDiscardButton();
                if (!discarded) {
                    // No more discard buttons found
                    break;
                }

                // Wait a bit after discard before checking again
                await this.human.sleep(1000);
                discardAttempts++;
            }

            if (discardAttempts > 0) {
                this.state.addLog(`✅ Cleared ${discardAttempts} pending upload(s)`);
                // Wait for page to stabilize after discarding
                await this.waitForPageReady();
            }

            // Now safe to find and inject video
            try {
                await this.waitForElement(this.selectors.selectVideoButton, { timeout: 10000 });
            } catch (e) { }

            const fileInput = document.querySelector(this.selectors.fileInput) ||
                document.querySelector('input[type="file"]');
            if (!fileInput) throw new Error('File input not found');

            const { min = 300, max = 500 } = this.state.config.stepDelay || {};
            await this.human.randomDelay(min, max);

            const dt = new DataTransfer();
            dt.items.add(videoFile);
            fileInput.files = dt.files;
            fileInput.dispatchEvent(new Event('change', { bubbles: true }));
            fileInput.dispatchEvent(new Event('input', { bubbles: true }));

            this.state.addLog('✅ Video injected');
            return true;
        }

        async handlePage3_FillDetails(product) {
            this.state.addLog('📍 Page 3: Details');
            await this.waitForPageReady();
            await this.waitForElement(this.selectors.postButton, { timeout: 60000 });

            // Use stepDelay from config (default min/max if not set)
            const { min = 300, max = 500 } = this.state.config.stepDelay || {};
            await this.human.randomDelay(min, max);

            await this._setCaption(product);
            await this._checkExitDialog();
            await this.human.randomDelay(min, max);
            await this._setVisibility(product.visibility || 'Everyone');
            await this._checkExitDialog();
            await this.human.randomDelay(min, max);
            await this._setPostMode(product.when_to_post || 'now');
            await this._checkExitDialog();
            await this.human.randomDelay(min, max);

            if (product.when_to_post === 'schedule' && product.sched_date) {
                await this._setScheduleDate(product.sched_date);
                await this._checkExitDialog();
                if (product.sched_time) await this._setScheduleTime(product.sched_time);
                await this._checkExitDialog();
            }

            // Check for Allow modal that might appear after scheduling options
            await this._checkAllowModal();

            // Double Request: Ensure "Schedule" or "Post now" is still selected after modal interaction
            await this._setPostMode(product.when_to_post || 'now');
            if (product.when_to_post === 'schedule') {
                // Re-check schedule inputs if needed, though they usually persist.
                // The radio button is the most likely to be visually deselected by UI glitches.
            }

            // Affiliate Products
            if (product.aff_products && product.aff_products.length > 0) {
                await this._addAffiliateProducts(product.aff_products);
            }

            // 5. Submit
            // 5. Submit or Simulate
            if (this.state.config.skipRealPost) {
                // --- SIMULATION MODE ---
                this.state.addLog('🧪 Sim Mode: Skipping Post Button', 'info');
                await this.human.randomDelay(min, max);

                // Click Sidebar to simulate "Done" and exit page state
                // Trying specific selector first, then fallback to generic sidebar link
                const sidebarSelector = 'button[data-tt="Sidebar_Sidebar_Clickable"], a[href*="/upload"]';
                const sidebarBtn = document.querySelector(sidebarSelector) ||
                    document.querySelector(this.selectors.uploadButton);

                if (sidebarBtn) {
                    this.state.addLog('🔄 Sim Mode: Clicking Sidebar/Upload to finish...');
                    await this.human.humanClick(sidebarBtn);
                    this.state.addLog('✅ Sim Mode: Cycle Completed');
                } else {
                    this.state.addLog('⚠️ Sim Mode: Sidebar button not found', 'warning');
                }

            } else {
                // --- REAL MODE ---
                if (this.state.config.autoPost) {
                    await this._clickSubmit();
                } else {
                    this.state.addLog('⏸️ Waiting for user to click "🚀 Auto Click Post"...', 'warning');
                    this.state.setWaitingForManualPost(true);

                    // Wait loop
                    while (!this.state.manualPostTrigger && !this.state.shouldStop) {
                        await this.human.sleep(500);
                    }

                    this.state.setWaitingForManualPost(false);

                    if (this.state.manualPostTrigger) {
                        this.state.addLog('🚀 Manual Trigger received! Posting...');
                        this.state.manualPostTrigger = false; // Reset
                        await this._clickSubmit();
                    } else {
                        this.state.addLog('🛑 Stopped while waiting for manual post');
                    }
                }
            }
            // Post-submit delay (use stepDelay)
            await this.human.randomDelay(min, max);
            return true;
        }

        async _checkAllowModal() {
            try {
                const allowBtn = document.evaluate("//button[.//div[text()='Allow']]", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                if (allowBtn) {
                    this.state.addLog('⚠️ "Allow" modal detected. Clicking...');
                    await this.human.humanClick(allowBtn);
                    await this.human.sleep(1000);
                }
            } catch (e) { }
        }

        async _addAffiliateProducts(affList) {
            this.state.addLog(`🛒 Adding ${affList.length} affiliate items...`);

            // Loop entire flow for each product (Radio select implies single selection per session)
            for (const item of affList) {
                await this._checkAllowModal();

                // 1. Click Initial "Add" Button
                try {
                    // Match: <div class="...">...Add</div> inside button
                    const addBtn = await this.waitForElement("//button[.//div[contains(text(), 'Add')]]", { timeout: 5000 });
                    await this.human.humanClick(addBtn);
                    await this.human.sleep(1000);
                    await this._checkAllowModal();
                } catch (e) {
                    this.state.addLog("⚠️ 'Add' button not found (Affiliate)", 'warning');
                    continue; // Skip this item if can't start
                }

                // 2. Handle "Next" Alert (If exists)
                try {
                    // Match: <div class="TUXButton-label">Next</div>
                    const nextBtn = document.evaluate("//div[contains(@class, 'TUXButton-label')][contains(text(), 'Next')]/ancestor::button", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                    if (nextBtn) {
                        await this.human.humanClick(nextBtn);
                        await this.human.sleep(1000);
                        await this._checkAllowModal();
                    }
                } catch (e) { }

                // 3. Click "Showcase products" Tab
                try {
                    // Match: <button class="TUXTabBar-itemTitle"><div>Showcase products</div></button>
                    const showcaseTab = await this.waitForElement("//button[contains(@class, 'TUXTabBar-itemTitle')][.//div[contains(text(), 'Showcase products')]]", { timeout: 5000 });
                    await this.human.humanClick(showcaseTab);
                    await this.human.sleep(2000);
                    await this._checkAllowModal();
                } catch (e) {
                    this.state.addLog("❌ Showcase tab not found", 'error');
                    // Likely fatal for this iteration, try to close or just continue to fail safely
                    continue;
                }

                // 4. Search & Select
                const searchTerm = item.aff_prod_code || item.aff_prod_name;
                this.state.addLog(`🔎 Searching by Code: ${searchTerm}`);

                try {
                    // Strategy: Find Input Globally or in Modal (Prioritize Placeholder)
                    // XPath: //input[@placeholder='Search products']
                    const searchInput = await this.waitForElement("//input[@placeholder='Search products']", { timeout: 3000 });

                    if (searchInput) {
                        // 1. Focus and Click to activate
                        searchInput.focus();
                        searchInput.click();
                        await this.human.sleep(300);

                        // 2. Use React Setter to insert value (Reliable for controlled components)
                        try {
                            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                            nativeInputValueSetter.call(searchInput, searchTerm);
                            searchInput.dispatchEvent(new Event('input', { bubbles: true }));
                        } catch (err) {
                            // Fallback if setter fails
                            await this.human.humanType(searchInput, searchTerm);
                        }

                        await this.human.sleep(500);

                        // 3. Trigger Search via ENTER
                        this.state.addLog(`⌨️ Pressing Enter for: ${searchTerm}`);
                        const keyOpts = { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true, cancelable: true, view: window };

                        // Dispatch multiple events to ensure listener catches it
                        searchInput.dispatchEvent(new KeyboardEvent('keydown', keyOpts));
                        searchInput.dispatchEvent(new KeyboardEvent('keypress', keyOpts));
                        searchInput.dispatchEvent(new KeyboardEvent('keyup', keyOpts));
                        searchInput.dispatchEvent(new Event('change', { bubbles: true }));
                    } else {
                        this.state.addLog("⚠️ Search input not found", 'warning');
                        continue;
                    }

                    await this.human.sleep(2000); // Wait for results

                    // Select Radio using User's Cell-Finding Logic
                    // 1. Find all cells with class .product-tb-cell
                    // 2. Find cell matching search term
                    // 3. Get parent Row -> Radio Label
                    try {
                        // Execute directly in this context (injected script)
                        const productSelected = (() => {
                            const searchId = String(searchTerm).trim();
                            const allCells = Array.from(document.querySelectorAll('.product-tb-cell'));
                            const targetCell = allCells.find(cell => cell.textContent.trim() === searchId);

                            if (targetCell) {
                                const row = targetCell.closest('tr');
                                if (row) {
                                    const radioLabel = row.querySelector('.TUXRadio-label');
                                    if (radioLabel) {
                                        radioLabel.click();
                                        return true;
                                    }
                                }
                            }
                            return false;
                        })();

                        if (productSelected) {
                            this.state.addLog("✅ Selected product (via Cell match)");
                            await this.human.sleep(1000);

                            // 5. Click Intermediate "Next" Button logic
                            // Strategy: Use Footer context fro User's snippet for maximum precision
                            // Snippet: <div class="common-modal-footer"> ... <button class="TUXButton--primary">Next</button> </div>
                            const nextBtnSelector = "//div[contains(@class, 'common-modal-footer')]//button[contains(@class, 'TUXButton--primary')][not(@disabled) or @aria-disabled='false'][.//div[contains(text(), 'Next')]]";

                            const nextConfirmBtn = await this.waitForElement(nextBtnSelector, { timeout: 5000 });

                            if (nextConfirmBtn) {
                                // Scroll and Click
                                nextConfirmBtn.scrollIntoView({ behavior: 'smooth', block: 'center' });
                                await this.human.sleep(300);
                                await this.human.humanClick(nextConfirmBtn);
                                await this.human.sleep(1000);
                            } else {
                                this.state.addLog("⚠️ Next button not enabled/found (in Footer)", 'warning');
                            }

                        } else {
                            this.state.addLog("⚠️ Product not found (Cell match failed)", 'warning');
                        }
                    } catch (selErr) {
                        this.state.addLog(`⚠️ Selection failed: ${selErr.message}`, 'warning');
                    }

                } catch (e) {
                    this.state.addLog(`⚠️ Action failed for ${searchTerm}: ${e.message}`, 'warning');
                }

                // 6. Click Final "Add" Button
                // Match: <div class="common-modal-footer"> ... <button ...>Add</button>
                try {
                    const finalAddBtnSelector = "//div[contains(@class, 'common-modal-footer')]//button[contains(@class, 'TUXButton--primary')][not(@disabled) or @aria-disabled='false'][.//div[contains(text(), 'Add')]]";

                    const confirmAdd = await this.waitForElement(finalAddBtnSelector, { timeout: 3000 });

                    if (confirmAdd) {
                        // Scroll mostly not needed for footer but good practice
                        confirmAdd.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        await this.human.sleep(500);
                        await this.human.humanClick(confirmAdd);
                        await this.human.sleep(2000);
                    } else {
                        this.state.addLog("⚠️ Final Add button not found/enabled", 'warning');
                    }
                    this.state.addLog(`✨ Added: ${searchTerm}`);
                } catch (e) {
                    this.state.addLog("⚠️ Final 'Add' button not clicked", 'warning');
                }
            } // End Loop
        }

        async _setScheduleDate(dateStr) {
            const targetDate = new Date(dateStr);
            const targetMonth = targetDate.toLocaleString('en-US', { month: 'long' });
            const targetYear = targetDate.getFullYear().toString();
            const targetDay = targetDate.getDate();

            this.state.addLog(`📅 Setting date to: ${targetMonth} ${targetYear}, Day ${targetDay}`);

            // 1. Open Picker (Click the Input Wrapper as recommended)
            const inputs = Array.from(document.querySelectorAll('.scheduled-picker input'));
            const dateInput = inputs.find(i => i.value.includes('-'));

            if (dateInput) {
                // Try to click the specific TUX wrapper
                const wrapper = dateInput.closest('.TUXInputBox') || dateInput.closest('.TUXTextInput');
                if (wrapper) {
                    await this.human.humanClick(wrapper);
                } else {
                    await this.human.humanClick(dateInput);
                }
            } else {
                this.state.addLog('❌ Date input not found', 'error');
                return;
            }
            await this.human.sleep(1000); // Wait for animation

            // 2. Navigate Month/Year
            let loops = 0;
            const maxLoops = 15;

            while (loops < maxLoops) {
                // Find Header using specific classes
                // The structure is month-title and year-title inside title-wrapper
                const monthTitle = document.querySelector('.month-title');
                const yearTitle = document.querySelector('.year-title');

                let currentMonthText = '';
                let currentYearText = '';

                if (monthTitle) currentMonthText = monthTitle.innerText.trim();
                // year-title class sometimes has trailing space as per user dump "year-title "
                if (yearTitle) currentYearText = yearTitle.innerText.trim();

                const combinedHeader = `${currentMonthText} ${currentYearText}`;
                this.state.addLog(`📆 Calendar Header: ${combinedHeader}`, 'info');

                // Check exact match
                if (currentMonthText === targetMonth && currentYearText === targetYear) {
                    this.state.addLog('✅ Reached target month/year');
                    break;
                }

                // Click Next Month (SVG rotated -90deg)
                const svgs = Array.from(document.querySelectorAll('svg'));
                const nextArrow = svgs.find(s => {
                    const style = s.getAttribute('style') || '';
                    return style.includes('rotate(-90deg)');
                });

                if (nextArrow) {
                    const btn = nextArrow.parentElement; // Click parent
                    btn.click();
                    await this.human.sleep(800);
                } else {
                    this.state.addLog('⚠️ Next Month button not found', 'warning');
                    break;
                }
                loops++;
            }

            // 3. Select Day
            // XPath: find day number that is NOT disabled
            const dayXPath = `//span[contains(@class,'day') and not(contains(@class,'disabled')) and text()='${targetDay}']`;
            const dayEl = document.evaluate(dayXPath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;

            if (dayEl) {
                await this.human.humanClick(dayEl);
                this.state.addLog(`✅ Selected Day: ${targetDay}`);
            } else {
                this.state.addLog(`❌ Day ${targetDay} not found in this month`, 'error');
            }

            await this.human.sleep(1000); // Wait for close animation
        }

        async _setScheduleTime(timeStr) {
            let [h, m] = timeStr.split(':').map(Number);
            m = Math.round(m / 5) * 5;
            if (m >= 60) { m = 0; h++; }
            if (h >= 24) h = 0;

            const targetHour = String(h).padStart(2, '0');
            const targetMinute = String(m).padStart(2, '0');
            const targetTimeStr = `${targetHour}:${targetMinute}`;

            this.state.addLog(`🕒 Setting time to: ${targetTimeStr}`, 'info');

            // Retry Loop
            for (let attempt = 1; attempt <= 3; attempt++) {
                const inputs = Array.from(document.querySelectorAll('.scheduled-picker input'));
                const timeInput = inputs.find(i => i.value.includes(':'));

                if (!timeInput) {
                    this.state.addLog('❌ Time input not found', 'error');
                    return;
                }

                // Check if already correct
                if (timeInput.value.trim() === targetTimeStr) {
                    this.state.addLog('✅ Time already correct', 'success');
                    return;
                }

                this.state.addLog(`🔄 Attempt ${attempt}: Opening Picker...`);

                // Helper: Nuclear Click Strategy
                const triggerEvents = (el) => {
                    ['mousedown', 'mouseup', 'click'].forEach(evtType => {
                        const evt = new MouseEvent(evtType, {
                            bubbles: true,
                            cancelable: true,
                            view: window
                        });
                        el.dispatchEvent(evt);
                    });
                };

                // 1. Open Picker
                await this.human.humanClick(timeInput);
                await this.human.sleep(1000);

                // 2. Select Hour (Left Column)
                const hourXPath = `//span[contains(@class, 'tiktok-timepicker-left')][text()='${targetHour}']`;
                const hourEl = document.evaluate(hourXPath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;

                if (hourEl) {
                    hourEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    await this.human.sleep(300);

                    this.state.addLog(`⚡ Nuclear clicking Hour ${targetHour}...`);
                    triggerEvents(hourEl); // Use Nuclear Click

                } else {
                    this.state.addLog(`⚠️ Hour ${targetHour} not found`, 'warning');
                }

                await this.human.sleep(500);

                // 3. Select Minute (Right Column)
                const minuteXPath = `//span[contains(@class, 'tiktok-timepicker-right')][normalize-space(text())='${targetMinute}'] | //span[contains(@class, 'tiktok-timepicker-right')][contains(text(), '${targetMinute}')]`;
                const minuteEl = document.evaluate(minuteXPath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;

                if (minuteEl) {
                    minuteEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    const minuteItem = minuteEl.closest('.tiktok-timepicker-option-item') || minuteEl;
                    await this.human.sleep(300);

                    this.state.addLog(`⚡ Nuclear clicking minute ${targetMinute}...`);
                    triggerEvents(minuteEl); // Click text
                    if (minuteItem !== minuteEl) triggerEvents(minuteItem); // Click parent container

                    this.state.addLog(`👆 Clicked Minute: ${targetMinute}`);
                } else {
                    this.state.addLog(`⚠️ Minute ${targetMinute} not found`, 'warning');
                }

                await this.human.sleep(500);

                // 4. Close picker
                const label = document.querySelector('.scheduled-picker label');
                if (label) label.click();

                await this.human.sleep(1000); // Wait for update

                // 5. Verify
                const currentVal = timeInput.value.trim();
                if (currentVal === targetTimeStr) {
                    this.state.addLog(`✅ Time verify success: ${currentVal}`, 'success');
                    return;
                } else {
                    this.state.addLog(`❌ Time mismatch: Got ${currentVal}, Expected ${targetTimeStr}. Retrying...`, 'warning');
                }
            }

            this.state.addLog('❌ Failed to set time after 3 attempts', 'error');
        }

        async _checkExitDialog() {
            try {
                // Find Modal with role="dialog" and aria-modal="true"
                const modal = document.querySelector('div[role="dialog"][aria-modal="true"]');

                if (modal) {
                    // Check if the modal is the "Exit Confirmation" by looking for title
                    const titleEl = modal.querySelector('h1, .TUXModalTitle h1, ._TUXModalTitle h1');

                    if (titleEl && titleEl.textContent.includes('Are you sure you want to exit')) {
                        this.state.addLog('⚠️ Exit Confirmation Dialog Detected. Clicking Exit...', 'warning');

                        // Find all buttons inside THIS modal only
                        const buttons = modal.querySelectorAll('button');

                        // Loop to find the "Exit" button (case-insensitive)
                        for (const btn of buttons) {
                            const btnText = btn.textContent.trim();
                            if (btnText === 'Exit' || btnText.toLowerCase() === 'exit') {
                                await this.human.humanClick(btn);
                                await this.human.sleep(1000);
                                this.state.addLog('✅ Clicked Exit');
                                return true;
                            }
                        }
                    }
                }
            } catch (e) {
                // Silent fail
            }
            return false;
        }

        async _handleAnyModal() {
            /**
             * Generic Modal Handler
             * Detects any modal and attempts to click common action buttons
             * Priority order: Exit, Allow, Next, Continue, OK, Confirm
             */
            try {
                const modal = document.querySelector('div[role="dialog"][aria-modal="true"]');
                if (!modal) return false;

                // Define button priorities (order matters)
                const buttonTexts = ['Exit', 'Allow', 'Next', 'Continue', 'OK', 'Confirm'];

                for (const text of buttonTexts) {
                    const buttons = Array.from(modal.querySelectorAll('button'));
                    const targetBtn = buttons.find(btn => {
                        const btnText = btn.textContent.trim();
                        return btnText === text || btnText.toLowerCase() === text.toLowerCase();
                    });

                    if (targetBtn) {
                        // Get modal title for logging
                        const titleEl = modal.querySelector('h1, h2, h3, [class*="title"], [class*="Title"]');
                        const modalTitle = titleEl ? titleEl.textContent.trim().substring(0, 50) : 'Unknown';

                        this.state.addLog(`🎯 Modal: "${modalTitle}" → Clicking "${text}"`, 'info');
                        await this.human.humanClick(targetBtn);
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
 * URGENT FIX: Replace _checkDiscardButton method (lines 698-756)
 * 
 * PROBLEM: 
 * - Line 719: if (modal) - 'modal' is undefined
 * - Line 736: const discardBtn - duplicate declaration
 * 
 * This causes PageHandler class to fail loading!
 */

        async _checkDiscardButton() {
            /**
             * Check for Discard button/modal (pending upload from previous session)
             * TikTok shows this when there's an unfinished upload
             * 
             * Strategy: Find button with 'Discard' text inside TUXModal
             */
            try {
                // Primary: TUXModal with Discard button
                const tuxModalXPath = "//div[contains(@class, 'TUXModal')]//button[.//text()='Discard']";
                let discardBtn = document.evaluate(
                    tuxModalXPath,
                    document,
                    null,
                    XPathResult.FIRST_ORDERED_NODE_TYPE,
                    null
                ).singleNodeValue;

                if (discardBtn) {
                    this.state.addLog('⚠️ Found Discard button in TUXModal. Clicking...', 'warning');
                    await this.human.humanClick(discardBtn);
                    await this.human.sleep(1500);
                    this.state.addLog('✅ Discarded draft post');
                    return true;
                }

                // Fallback - Generic Discard button (standalone, no modal)
                const genericXPath = "//button[.//div[contains(text(), 'Discard')]]";
                discardBtn = document.evaluate(
                    genericXPath,
                    document,
                    null,
                    XPathResult.FIRST_ORDERED_NODE_TYPE,
                    null
                ).singleNodeValue;

                if (discardBtn) {
                    this.state.addLog('⚠️ Found standalone Discard button. Clicking...', 'warning');
                    await this.human.humanClick(discardBtn);
                    await this.human.sleep(1500);
                    this.state.addLog('✅ Discarded previous upload');
                    return true;
                }

            } catch (e) {
                // Silent fail
            }
            return false;
        }


        async _clearLocalDraft() {
            /**
             * Clear unsaved draft (2-step process):
             * Step 1: Click Discard on local-draft-card
             * Step 2: Confirm Discard in TUXModal
             */
            try {
                // --- Step 1: Find Discard button in local-draft-card ---
                const draftCard = document.querySelector('.local-draft-card');

                if (draftCard) {
                    // Find Discard button within draft card
                    const draftBtn = Array.from(draftCard.querySelectorAll('button'))
                        .find(btn => btn.textContent.trim() === 'Discard');

                    if (draftBtn) {
                        this.state.addLog('🗑️ Found local draft. Clicking Discard...');
                        await this.human.humanClick(draftBtn);

                        // Wait for confirmation modal to appear
                        await this.human.sleep(1000);

                        // --- Step 2: Find Discard button in TUXModal ---
                        const modal = document.querySelector('div[class*="TUXModal"]');

                        if (modal) {
                            // Find Discard button in modal
                            const confirmBtn = Array.from(modal.querySelectorAll('button'))
                                .find(btn => btn.textContent.trim() === 'Discard');

                            if (confirmBtn) {
                                await this.human.humanClick(confirmBtn);
                                this.state.addLog('✅ Confirmed: Local draft discarded');
                                await this.human.sleep(1500);
                                return true;
                            } else {
                                this.state.addLog('⚠️ Discard button not found in modal', 'warning');
                            }
                        } else {
                            this.state.addLog('⚠️ Confirmation modal did not appear', 'warning');
                        }
                    }
                }
                // No draft found - this is normal
                return false;

            } catch (e) {
                // Silent fail - draft clearing is optional
                return false;
            }
        }


        async _checkAllowModal() {
            // Use generic handler instead of hard-coded logic
            return await this._handleAnyModal();
        }

        async _clickSubmit() {
            // Helper to find "Post" or "Schedule" button
            const findPostButton = () => {
                // Determine if we are looking for Post or Schedule based on expected state?
                // Or just look for either since only one exists at a time.
                // Text can be "Post", "Post now", "Schedule"
                const xpath = "//button[contains(@class, 'TUXButton--primary') and (.//div[contains(text(), 'Post')] or .//div[contains(text(), 'Schedule')])] " +
                    "| //button[.//div[text()='Post'] or .//div[text()='Schedule']]"; // Fallback for stricter match if primary class missing

                return document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            };

            // 1. Initial Click
            let btn = findPostButton() || document.querySelector(this.selectors.postButton);
            if (btn) {
                this.state.addLog('🔹 Clicking Post Button...');
                await this.human.humanClick(btn);

                // 2. Wait and check for secondary "Continue to post?" dialog
                await this.human.sleep(2000); // Wait for potential dialog

                // [NEW] Check for "Are you sure you want to exit?" just in case navigation triggered early
                await this._checkExitDialog();

                btn = findPostButton(); // Look again
                if (btn) {
                    this.state.addLog('⚠️ "Continue to post?" detected. Clicking again...');
                    await this.human.humanClick(btn);
                    await this.human.sleep(2000);
                    await this._checkExitDialog();
                }

                this.state.addLog('✅ Submitted!');
            } else {
                this.state.addLog('❌ Post button not found', 'error');
                throw new Error('Post button not found');
            }
        }

        async _setCaption(product) {
            const caption = `${product.prod_descr || ''}\n\n${product.prod_tags || ''}`;
            this.state.addLog('📝 Setting caption (Clipboard Paste)...');

            try {
                // 1. Copy to System Clipboard (Fallback for user)
                try {
                    await navigator.clipboard.writeText(caption);
                    this.state.addLog('📋 Copied to clipboard');
                } catch (err) {
                    this.state.addLog('⚠️ Clipboard write failed (ignore)', 'warning');
                }

                const editor = document.querySelector(this.selectors.captionEditor);
                if (editor) {
                    editor.focus();
                    await this.human.sleep(500);

                    // 1. Select All (Ctrl+A)
                    document.execCommand('selectAll', false, null);
                    await this.human.sleep(300);

                    // 2. Delete (Clear content)
                    document.execCommand('delete', false, null);
                    await this.human.sleep(300);

                    // 3. Dispatch Synthetic Paste Event (Ctrl+V)
                    // This tricks Draft.js into thinking user passed Ctrl+V
                    const pasteEvent = new ClipboardEvent('paste', {
                        bubbles: true,
                        cancelable: true,
                        clipboardData: new DataTransfer()
                    });
                    pasteEvent.clipboardData.setData('text/plain', caption);

                    editor.dispatchEvent(pasteEvent);

                    // 3. Dispatch Input Event (Trigger validation)
                    await this.human.sleep(200);
                    editor.dispatchEvent(new InputEvent('input', { bubbles: true }));

                    this.state.addLog('✅ Caption pasted event sent');
                } else {
                    this.state.addLog('⚠️ Caption Editor not found', 'warning');
                }
            } catch (e) {
                this.state.addLog(`⚠️ Caption error: ${e.message}`, 'warning');
            }
        }

        async _setVisibility(targetText) {
            const container = document.querySelector(this.selectors.visibilityContainer);
            if (!container) return;

            const trigger = container.querySelector('.Select__trigger');
            if (trigger) {
                await this.human.humanClick(trigger);
                await this.human.sleep(500);

                for (const option of document.querySelectorAll('.Select__item')) {
                    if (option.innerText.toLowerCase().includes(targetText.toLowerCase())) {
                        await this.human.humanClick(option);
                        break;
                    }
                }
            }
        }

        async _setPostMode(mode) {
            const modeValue = mode === 'schedule' ? 'schedule' : 'post_now';
            const radio = document.querySelector(`input[name="postSchedule"][value="${modeValue}"]`);
            if (radio) await this.human.humanClick(radio);
        }

    }

    // Register with namespace
    TTU.PageHandler = PageHandler;

})(window.TikTokUploader || (window.TikTokUploader = {}));


