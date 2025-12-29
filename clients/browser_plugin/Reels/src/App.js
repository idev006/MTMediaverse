/**
 * App - Main UI Panel for Reels
 */
(function (FBU) {
    'use strict';

    class App {
        constructor(engine) {
            this.engine = engine;
            this.initUI();
        }

        initUI() {
            // Remove existing if any
            const existing = document.getElementById('fbu-panel');
            if (existing) existing.remove();

            // Container
            const panel = document.createElement('div');
            panel.id = 'fbu-panel';
            panel.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                width: 300px;
                background: rgba(0, 0, 0, 0.85);
                color: white;
                border-radius: 8px;
                padding: 15px;
                z-index: 999999;
                font-family: sans-serif;
                box-shadow: 0 4px 15px rgba(0,0,0,0.5);
                border: 1px solid rgba(255,255,255,0.1);
            `;

            // Title
            const title = document.createElement('h3');
            title.innerText = 'FB Reels Uploader';
            title.style.cssText = 'margin: 0 0 15px 0; font-size: 16px; color: #1877f2;';
            panel.appendChild(title);

            // Input Group
            const inputGroup = document.createElement('div');
            inputGroup.style.marginBottom = '15px';

            const label = document.createElement('label');
            label.innerText = 'Product Code:';
            label.style.display = 'block';
            label.style.marginBottom = '5px';
            label.style.fontSize = '12px';
            label.style.color = '#ccc';
            inputGroup.appendChild(label);

            const input = document.createElement('input');
            input.type = 'text';
            input.id = 'fbu-prod-code';
            input.placeholder = 'e.g., PROD-123';
            input.value = 'TEST-001'; // Default
            input.style.cssText = `
                width: 100%;
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #444;
                background: #222;
                color: white;
                box-sizing: border-box;
            `;
            inputGroup.appendChild(input);
            panel.appendChild(inputGroup);

            // Log Area
            const logArea = document.createElement('div');
            logArea.id = 'fbu-log';
            logArea.style.cssText = `
                height: 100px;
                background: #111;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 5px;
                font-family: monospace;
                font-size: 10px;
                overflow-y: auto;
                margin-bottom: 15px;
                color: #0f0;
            `;
            panel.appendChild(logArea);

            // Actions
            const btn = document.createElement('button');
            btn.innerText = 'Fetch & Inject';
            btn.style.cssText = `
                width: 100%;
                padding: 10px;
                background: #1877f2;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-weight: bold;
            `;
            btn.onmouseover = () => btn.style.background = '#166fe5';
            btn.onmouseout = () => btn.style.background = '#1877f2';

            btn.onclick = async () => {
                const prodCode = input.value.trim();
                if (!prodCode) {
                    this.log('Result: Please enter a product code', 'error');
                    return;
                }

                btn.disabled = true;
                btn.innerText = 'Processing...';

                try {
                    await this.engine.runStep2(prodCode);
                } catch (e) {
                    this.log(`Error: ${e.message}`, 'error');
                } finally {
                    btn.disabled = false;
                    btn.innerText = 'Fetch & Inject';
                }
            };
            panel.appendChild(btn);

            // Footer / Close
            const closeBtn = document.createElement('div');
            closeBtn.innerText = '×';
            closeBtn.style.cssText = `
                position: absolute;
                top: 5px;
                right: 10px;
                cursor: pointer;
                font-size: 20px;
                color: #aaa;
            `;
            closeBtn.onclick = () => panel.remove();
            panel.appendChild(closeBtn);

            document.body.appendChild(panel);
            this.log('Panel ready.');

            // Override console.log to show in panel
            const origLog = this.engine.log || console.log;
            this.engine.log = (msg, type) => {
                this.log(msg, type);
                if (origLog) origLog(msg);
            };
        }

        log(msg, type = 'info') {
            const area = document.getElementById('fbu-log');
            if (!area) return;
            const line = document.createElement('div');
            line.innerText = `> ${msg}`;
            if (type === 'error') line.style.color = '#ff5252';
            area.appendChild(line);
            area.scrollTop = area.scrollHeight;
        }
    }

    FBU.App = App;
})(window.FBReelsUploader || (window.FBReelsUploader = {}));
