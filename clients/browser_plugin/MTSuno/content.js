/**
 * MTSuno - Entry Point (content.js)
 * Loads all modules and initializes the application
 */
(function (MTS) {
    'use strict';

    // Wait for DOM to be ready
    const init = () => {
        console.log('[MTSuno] Content script loaded');

        // Initialize the app
        if (MTS.initApp) {
            MTS.initApp();
        } else {
            console.error('[MTSuno] App module not loaded');
        }
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})(window.MTSuno || (window.MTSuno = {}));
