/**
 * Content Script Entry Point
 * Initializes YouTubeUploader namespace
 */
(function () {
    'use strict';

    if (window.__YTU_INITIALIZED__) return;
    window.__YTU_INITIALIZED__ = true;

    const init = () => {
        setTimeout(() => {
            if (window.YouTubeUploader?.init) {
                window.YouTubeUploader.init();
            } else {
                console.error('[YTU] Namespace not found');
            }
        }, 500);
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
