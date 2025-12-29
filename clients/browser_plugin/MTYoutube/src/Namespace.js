/**
 * YouTube Uploader Namespace
 * Global namespace registry.
 * Actual initialization logic is in App.js (YTU.init)
 * 
 * @namespace YouTubeUploader
 */
(function (global) {
    'use strict';

    if (global.YouTubeUploader) return;

    const YouTubeUploader = {
        VERSION: '1.0.0',
        NAME: 'YouTube Auto Uploader',

        // MVVM Placeholders
        Model: {},
        ViewModel: null,
        View: null,
        Stubs: {},
        Utils: {},

        // Configuration
        config: {
            apiBaseUrl: 'http://127.0.0.1:8000',
            sidebarWidth: 450,
            debug: true
        },

        _modules: {},
        _initialized: false,

        /**
         * Register a module
         */
        register(name, module) {
            this._modules[name] = module;
        },

        /**
         * Logging utility
         */
        log(message, type = 'info') {
            if (!this.config.debug && type === 'info') return;
            const prefix = { info: '✅', warning: '⚠️', error: '❌' }[type] || 'ℹ️';
            console.log(`[YTU] ${prefix} ${message}`);
            if (this.State?.addLog) this.State.addLog(message, type);
        },

        isReady() { return this._initialized; }
    };

    global.YouTubeUploader = YouTubeUploader;
    global.YTU = YouTubeUploader;

})(typeof window !== 'undefined' ? window : this);
