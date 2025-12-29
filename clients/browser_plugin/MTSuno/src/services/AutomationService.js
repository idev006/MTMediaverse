/**
 * AutomationService - Handles direct DOM manipulation on Suno.ai
 */
export class AutomationService {

    constructor() {
        this.selectors = {
            lyricsTextarea: 'textarea[placeholder*="Write some lyrics"], textarea[placeholder*="Enter your lyrics"]',
            styleTextarea: 'textarea[placeholder*="kwaito"], textarea[placeholder*="Enter style of music"]',
            titleInput: 'input[placeholder="Song Title (Optional)"]',
            createButton: 'button[data-testid="create-button"], button:contains("Create")',
            clipRow: 'div[data-testid="clip-row"], .clip-row',
        }
    }

    async sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
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

    async fillForm(title, style, lyrics) {
        // Logic ported from content.legacy.js
        console.log(`[Auto] Filling: ${title} / ${style}`)

        // 1. Title
        const titleInput = document.querySelector(this.selectors.titleInput);
        if (titleInput) {
            this.setNativeValue(titleInput, title);
        } else {
            console.warn("Title input not found. Ensure Custom Mode is on.");
        }

        // 2. Style & Lyrics
        const textareas = document.querySelectorAll('textarea');
        let styleArea, lyricsArea;

        textareas.forEach(ta => {
            const ph = ta.placeholder.toLowerCase();
            if (ph.includes('style') || ph.includes('tone')) styleArea = ta;
            if (ph.includes('lyrics') || ph.includes('prompt')) lyricsArea = ta; // "Enter your lyrics" or "Song Description" depending on mode
        });

        if (styleArea) this.setNativeValue(styleArea, style || "Pop"); // Default style?

        if (lyricsArea) {
            if (lyrics) {
                this.setNativeValue(lyricsArea, lyrics);
            } else {
                // Instrumental
                this.setNativeValue(lyricsArea, "");
                // TODO: specific toggle handling
            }
        }

        await this.sleep(500);
    }

    async clickCreate() {
        // Find Create Button
        // Selector might need refinement as "Create" text might change
        const buttons = Array.from(document.querySelectorAll('button'));
        const createBtn = buttons.find(b => b.textContent.includes('Create') && !b.disabled);

        if (createBtn) {
            createBtn.click();
            console.log("[Auto] Clicked Create");
        } else {
            throw new Error("Create button not found or disabled");
        }
    }

    async waitForGeneration(timeout = 60000) {
        // Simple wait for now, user manually checks visually or backend handles it?
        // Legacy code checked for "Generating..." class
        // For MVP refactor, just wait fixed time or until items appear

        // Let's rely on the user or a simple delay for now to avoid complexity in this step
        // Ideally we poll the DOM list
        await this.sleep(5000);
        console.log("[Auto] Wait for generation initial delay done");
    }
}
