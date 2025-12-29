/**
 * HumanLike - Anti-bot detection utilities
 * Provides human-like interaction simulation
 * 
 * @memberof YouTubeUploader.Utils
 */
(function (YTU) {
    'use strict';

    class HumanLike {
        constructor(config = {}) {
            this.config = {
                enabled: true,
                randomizeClicks: true,
                mouseMovement: true,
                typingDelay: 50,
                mouseSpeed: 15,
                ...config
            };

            this._virtualMouseX = 0;
            this._virtualMouseY = 0;
        }

        setConfig(config) {
            this.config = { ...this.config, ...config };
        }

        sleep(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
        }

        async randomDelay(min, max) {
            const delay = Math.floor(Math.random() * (max - min + 1)) + min;
            await this.sleep(delay);
            return delay;
        }

        async moveMouseLikeHuman(element) {
            if (!element || !this.config.mouseMovement) return;

            const rect = element.getBoundingClientRect();
            const targetX = rect.left + Math.random() * rect.width * 0.8 + rect.width * 0.1;
            const targetY = rect.top + Math.random() * rect.height * 0.8 + rect.height * 0.1;

            const startX = this._virtualMouseX || Math.random() * window.innerWidth;
            const startY = this._virtualMouseY || Math.random() * window.innerHeight;

            // Bezier curve control points
            const cp1x = startX + (Math.random() - 0.5) * (targetX - startX) * 2;
            const cp1y = startY + (Math.random() - 0.5) * (targetY - startY) * 2;
            const cp2x = targetX + (Math.random() - 0.5) * (targetX - startX) * 2;
            const cp2y = targetY + (Math.random() - 0.5) * (targetY - startY) * 2;

            const distance = Math.sqrt((targetX - startX) ** 2 + (targetY - startY) ** 2);
            const steps = Math.max(20, Math.floor(distance / this.config.mouseSpeed));

            for (let i = 0; i <= steps; i++) {
                const t = i / steps;
                const cx = (1 - t) ** 3 * startX + 3 * (1 - t) ** 2 * t * cp1x +
                    3 * (1 - t) * t ** 2 * cp2x + t ** 3 * targetX;
                const cy = (1 - t) ** 3 * startY + 3 * (1 - t) ** 2 * t * cp1y +
                    3 * (1 - t) * t ** 2 * cp2y + t ** 3 * targetY;

                this._dispatchMouse(element, 'mousemove', cx, cy);
                this._virtualMouseX = cx;
                this._virtualMouseY = cy;

                await this.sleep(Math.random() * 5 + 5);
            }

            this._dispatchMouse(element, 'mouseenter', targetX, targetY);
        }

        _dispatchMouse(element, type, x, y) {
            element.dispatchEvent(new MouseEvent(type, {
                view: window,
                bubbles: true,
                cancelable: true,
                clientX: x,
                clientY: y,
                screenX: x + window.screenX,
                screenY: y + window.screenY
            }));
        }

        async humanClick(element) {
            if (!element) return false;

            if (this.config.enabled) {
                await this.moveMouseLikeHuman(element);
                await this.randomDelay(100, 300);
            }

            const rect = element.getBoundingClientRect();
            const x = rect.left + (this.config.randomizeClicks
                ? Math.random() * rect.width * 0.6 + rect.width * 0.2
                : rect.width / 2);
            const y = rect.top + (this.config.randomizeClicks
                ? Math.random() * rect.height * 0.6 + rect.height * 0.2
                : rect.height / 2);

            this._dispatchMouse(element, 'mousedown', x, y);
            await this.randomDelay(50, 150);
            this._dispatchMouse(element, 'mouseup', x, y);
            this._dispatchMouse(element, 'click', x, y);
            element.click();

            return true;
        }

        async humanType(element, text) {
            if (!element) return;

            element.focus();
            document.execCommand('selectAll', false, null);
            document.execCommand('delete', false, null);

            for (const char of text) {
                document.execCommand('insertText', false, char);
                await this.sleep(this.config.typingDelay + Math.random() * this.config.typingDelay * 2);
            }
        }
    }

    // Register with namespace
    YTU.HumanLike = HumanLike;

})(window.YouTubeUploader || (window.YouTubeUploader = {}));
