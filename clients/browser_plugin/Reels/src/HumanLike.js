/**
 * HumanLike - Mimic human behavior
 */
(function (FBU) {
    'use strict';

    class HumanLike {
        async sleep(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
        }

        async randomDelay(min, max) {
            const delay = Math.floor(Math.random() * (max - min + 1) + min);
            await this.sleep(delay);
        }

        async humanClick(element) {
            if (!element) return;
            element.scrollIntoView({ behavior: 'smooth', block: 'center' });
            await this.sleep(Math.random() * 200 + 100);

            const eventOpts = { bubbles: true, cancelable: true, view: window };
            element.dispatchEvent(new MouseEvent('mousedown', eventOpts));
            await this.sleep(Math.random() * 100 + 50);
            element.dispatchEvent(new MouseEvent('mouseup', eventOpts));
            element.dispatchEvent(new MouseEvent('click', eventOpts));
        }
    }

    FBU.HumanLike = HumanLike;
})(window.FBReelsUploader || (window.FBReelsUploader = {}));
