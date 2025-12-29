/**
 * TikTok Uploader Namespace
 * Global namespace for the TikTok Auto Uploader plugin
 * Provides encapsulation and extensibility
 */
(function (global) {
    'use strict';

    // Prevent re-initialization
    if (global.TikTokUploader) {
        console.log('[TikTokUploader] Already initialized');
        return;
    }

    /**
     * Main Namespace Object
     */
    const TikTokUploader = {
        // Version info
        VERSION: '5.1.0',
        NAME: 'TikTok Auto Uploader',

        // Module references (populated by individual modules)
        State: null,
        Api: null,
        Human: null,
        Page: null,
        Automation: null,
        UI: null,

        // Configuration
        config: {
            apiBaseUrl: 'http://127.0.0.1:8000',
            sidebarWidth: 450,
            debug: true
        },

        // Internal state
        _initialized: false,
        _modules: {},

        /**
         * Register a module
         * @param {string} name - Module name
         * @param {object|function} module - Module implementation
         */
        register(name, module) {
            if (this._modules[name]) {
                this.log(`Module "${name}" already registered, overwriting`, 'warning');
            }
            this._modules[name] = module;
            this[name] = module;
            this.log(`Module "${name}" registered`);
        },

        /**
         * Extend namespace with additional functionality
         * @param {string} name - Extension name
         * @param {object} extension - Extension object
         */
        extend(name, extension) {
            if (this[name]) {
                // Merge if exists
                Object.assign(this[name], extension);
            } else {
                this[name] = extension;
            }
            this.log(`Extended with "${name}"`);
        },

        /**
         * Initialize the application
         */
        async init() {
            if (this._initialized) {
                this.log('Already initialized', 'warning');
                return;
            }

            this.log('Initializing...');

            try {
                // Initialize modules in order
                this.State = new this.StateManager();
                this.Api = new this.ApiClient(this.config.apiBaseUrl);
                this.Human = new this.HumanLike(this.State.config.humanLike);
                this.Page = new this.PageHandler(this.Human, this.State);
                this.Automation = new this.AutomationEngine(this.State, this.Api, this.Page);

                // Create UI
                this._createUI();

                // Initial server check
                await this.Automation.checkServer();

                this._initialized = true;
                this.log('Initialized successfully!');

            } catch (error) {
                this.log(`Init error: ${error.message}`, 'error');
                console.error(error);
            }
        },

        /**
         * Create sidebar UI
         */
        _createUI() {
            if (document.getElementById('tiktok-uploader-sidebar')) return;

            const sidebar = document.createElement('div');
            sidebar.id = 'tiktok-uploader-sidebar';
            sidebar.className = 'ttu-sidebar';
            document.body.appendChild(sidebar);

            // Push main content
            document.documentElement.style.cssText =
                `margin-right: ${this.config.sidebarWidth}px !important; transition: margin-right 0.3s ease !important;`;

            // Mount Vue if available
            if (typeof Vue !== 'undefined' && this.VueApp) {
                this.UI = this.VueApp.mount('#tiktok-uploader-sidebar');
            }
        },

        /**
         * Logging utility
         */
        log(message, type = 'info') {
            if (!this.config.debug && type === 'info') return;

            const prefix = {
                info: '✅',
                warning: '⚠️',
                error: '❌'
            }[type] || 'ℹ️';

            console.log(`[TikTokUploader] ${prefix} ${message}`);

            // Also add to state logs if available
            if (this.State?.addLog) {
                this.State.addLog(message, type);
            }
        },

        /**
         * Get module by name
         */
        getModule(name) {
            return this._modules[name] || this[name];
        },

        /**
         * Check if initialized
         */
        isReady() {
            return this._initialized;
        }
    };

    // Freeze config to prevent accidental modification
    Object.freeze(TikTokUploader.config);

    // Export to global
    global.TikTokUploader = TikTokUploader;

    // Shorthand alias
    global.TTU = TikTokUploader;

})(typeof window !== 'undefined' ? window : this);
