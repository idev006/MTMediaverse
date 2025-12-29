/**
 * Content Script Entry
 */
(function () {
    'use strict';

    console.log('[FBU] Content script loaded');

    const init = () => {
        // Check filtering: Facebook AND reels_tab
        if (!window.location.href.includes('reels_tab')) {
            console.log('[FBU] Not on reels_tab, skipping...');
            return;
        }

        if (window.FBReelsUploader && window.FBReelsUploader.AutomationEngine && window.FBReelsUploader.App) {
            const engine = new window.FBReelsUploader.AutomationEngine();
            engine.init();

            // Init UI
            const app = new window.FBReelsUploader.App(engine);

            console.log('[FBU] App Initialized');
        } else {
            console.error('[FBU] Namespace/Classes not found, retrying...');
            setTimeout(init, 500);
        }
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
