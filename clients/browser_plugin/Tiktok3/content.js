/**
 * Content Script Entry Point
 * Initializes TikTokUploader namespace
 */
(function () {
    'use strict';

    if (window.__TTU_INITIALIZED__) return;
    window.__TTU_INITIALIZED__ = true;

    const init = () => {
        setTimeout(() => {
            if (window.TikTokUploader?.init) {
                window.TikTokUploader.init();
            } else {
                console.error('[TTU] Namespace not found');
            }
        }, 500);
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
