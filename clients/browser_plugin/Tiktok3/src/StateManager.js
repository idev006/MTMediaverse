/**
 * StateManager - Centralized state management (Singleton pattern)
 * Single source of truth for all plugin state
 * 
 * @memberof TikTokUploader
 */
(function (TTU) {
    'use strict';

    class StateManager {
        constructor() {

            // Products
            this.products = [];
            this.currentProduct = null;
            this.currentVideoFile = null;

            // Processing state
            this.isProcessing = false;
            this.shouldStop = false;
            this.isPaused = false;

            // Manual Trigger State
            this.waitingForManualPost = false;
            this.manualPostTrigger = false;

            // Progress tracking
            this.progress = {
                total: 0,
                completed: 0,
                success: 0,
                failed: 0,
                currentStep: 0,
                stepLabel: 'Ready',
                estimatedTimeLeft: null, // In seconds
                startTime: null
            };

            // Config
            this.config = {
                productDelay: { min: 660000, max: 720000 },
                stepDelay: { min: 2000, max: 5000 },
                typing: 50,
                mouse: 15,
                pollInterval: 500,
                maxWaitTime: 30000,
                heartbeatInterval: 5000, // [NEW] Explicit heartbeat interval
                humanLike: {
                    enabled: true,
                    randomizeClicks: true,
                    mouseMovement: true
                },
                autoPost: false, // Default to false for manual verification
                clientCode: ''   // [NEW] Multi-Client Auth Code
            };

            // Logs
            this.logs = [];

            // Server connection
            this.serverOnline = false;

            // Callbacks for reactivity
            this._listeners = [];

            // Load saved config
            this.loadConfig();
        }

        /**
         * Load config from localStorage
         */
        loadConfig() {
            try {
                const saved = localStorage.getItem('ttu_config');
                if (saved) {
                    const parsed = JSON.parse(saved);
                    // Merge deeply to preserve defaults for new keys
                    this.config = {
                        ...this.config,
                        ...parsed,
                        productDelay: { ...this.config.productDelay, ...parsed.productDelay },
                        stepDelay: { ...this.config.stepDelay, ...parsed.stepDelay },
                        humanLike: { ...this.config.humanLike, ...parsed.humanLike }
                    };
                    console.log('[StateManager] Config loaded:', this.config);
                }
            } catch (e) {
                console.error('Failed to load config:', e);
            }
        }

        /**
         * Save config to localStorage
         */
        saveConfig() {
            try {
                localStorage.setItem('ttu_config', JSON.stringify(this.config));
                console.log('[StateManager] Config saved');
            } catch (e) {
                console.error('Failed to save config:', e);
            }
        }

        /**
         * Subscribe to state changes
         */
        subscribe(listener) {
            this._listeners.push(listener);
            return () => {
                this._listeners = this._listeners.filter(l => l !== listener);
            };
        }

        /**
         * Notify all listeners of state change
         */
        _notify() {
            this._listeners.forEach(listener => listener(this));
        }

        // ============================================
        // PRODUCTS
        // ============================================

        setProducts(products) {
            this.products = products;
            this._notify();
        }

        shiftProduct() {
            const product = this.products.shift();
            this._notify();
            return product;
        }

        setCurrentProduct(product) {
            this.currentProduct = product;
            this._notify();
        }

        setCurrentVideoFile(file) {
            this.currentVideoFile = file;
        }

        // ============================================
        // PROCESSING STATE
        // ============================================

        startProcessing() {
            this.isProcessing = true;
            this.shouldStop = false;
            this.isPaused = false;
            this._notify();
        }

        stopProcessing() {
            this.shouldStop = true;
            this._notify();
        }

        pauseProcessing() {
            this.isPaused = true;
            this._notify();
        }

        resumeProcessing() {
            this.isPaused = false;
            this._notify();
        }

        finishProcessing() {
            this.isProcessing = false;
            this.currentProduct = null;
            this._notify();
        }

        // ============================================
        // MANUAL TRIGGER
        // ============================================

        setWaitingForManualPost(waiting) {
            this.waitingForManualPost = waiting;
            this._notify();
        }

        triggerManualPost() {
            this.manualPostTrigger = true;
            this._notify();
        }

        // ============================================
        // PROGRESS
        // ============================================

        initProgress(total) {
            this.progress = {
                total,
                completed: 0,
                success: 0,
                failed: 0,
                currentStep: 0,
                stepLabel: 'Starting...',
                estimatedTimeLeft: null,
                startTime: Date.now()
            };
            this._notify();
        }

        updateProgress(completed, success, failed) {
            this.progress.completed = completed;
            this.progress.success = success;
            this.progress.failed = failed;

            // Calculate ETA
            if (this.progress.startTime && completed > 0 && this.progress.total > completed) {
                const elapsed = Date.now() - this.progress.startTime; // ms
                const avgTimePerItem = elapsed / completed; // ms per item
                const remaining = this.progress.total - completed;
                this.progress.estimatedTimeLeft = Math.round((avgTimePerItem * remaining) / 1000); // seconds
            } else {
                this.progress.estimatedTimeLeft = null;
            }

            this._notify();
        }

        updateStep(step, label) {
            this.progress.currentStep = step;
            this.progress.stepLabel = label;
            this._notify();
        }

        getProgressPercent() {
            if (this.progress.total === 0) return 0;
            return Math.round((this.progress.completed / this.progress.total) * 100);
        }

        // ============================================
        // LOGS
        // ============================================

        addLog(message, type = 'info') {
            const timestamp = new Date().toLocaleTimeString('en-US', { hour12: false });
            this.logs.push({ timestamp, message, type });

            // Keep only last 100 logs
            if (this.logs.length > 100) {
                this.logs = this.logs.slice(-100);
            }

            this._notify();

            // Also console.log for debugging
            const prefix = type === 'error' ? '❌' : type === 'warning' ? '⚠️' : '✅';
            console.log(`[TikTok Uploader] ${prefix} ${message}`);
        }

        clearLogs() {
            this.logs = [];
            this._notify();
        }

        // ============================================
        // CONFIG
        // ============================================

        setConfig(key, value) {
            if (key.includes('.')) {
                const [parent, child] = key.split('.');
                this.config[parent][child] = value;
            } else {
                this.config[key] = value;
            }
            this._notify();
        }

        // ============================================
        // SERVER
        // ============================================

        setServerStatus(online) {
            this.serverOnline = online;
            this._notify();
        }
    }

    // Register with namespace
    TTU.StateManager = StateManager;

})(window.TikTokUploader || (window.TikTokUploader = {}));
