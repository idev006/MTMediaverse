/**
 * StateManager - Centralized State Model (Observable)
 * Single source of truth for all plugin state
 * Uses Vue's reactivity for automatic UI updates
 * 
 * @memberof YouTubeUploader.Model
 */
(function (YTU) {
    'use strict';

    class StateManager {
        constructor() {
            // Products queue
            this.products = [];
            this.currentProduct = null;
            this.currentVideoFile = null;

            // Processing state
            this.isProcessing = false;
            this.shouldStop = false;
            this.isPaused = false;

            // Progress tracking
            this.progress = {
                total: 0,
                completed: 0,
                success: 0,
                failed: 0,
                currentStep: 0,
                stepLabel: 'Ready',
                currentScene: '',
                estimatedTimeLeft: null,
                startTime: null
            };

            // Config
            this.config = {
                productDelay: { min: 60000, max: 120000 },
                stepDelay: { min: 1000, max: 3000 },
                typing: 50,
                mouse: 15,
                pollInterval: 500,
                maxWaitTime: 30000,
                heartbeatInterval: 5000,
                humanLike: {
                    enabled: true,
                    randomizeClicks: true,
                    mouseMovement: true
                },
                autoPost: false,
                clientCode: ''
            };

            // Logs
            this.logs = [];

            // Server connection
            this.serverOnline = false;

            // Observers for reactivity
            this._listeners = [];

            // Load saved config
            this.loadConfig();
        }

        /**
         * Load config from localStorage
         */
        loadConfig() {
            try {
                const saved = localStorage.getItem('ytu_config');
                if (saved) {
                    const parsed = JSON.parse(saved);
                    this.config = {
                        ...this.config,
                        ...parsed,
                        productDelay: { ...this.config.productDelay, ...parsed.productDelay },
                        stepDelay: { ...this.config.stepDelay, ...parsed.stepDelay },
                        humanLike: { ...this.config.humanLike, ...parsed.humanLike }
                    };
                    console.log('[StateManager] Config loaded');
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
                localStorage.setItem('ytu_config', JSON.stringify(this.config));
                console.log('[StateManager] Config saved');
            } catch (e) {
                console.error('Failed to save config:', e);
            }
        }

        /**
         * Subscribe to state changes (Observer pattern)
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
                currentScene: '',
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
                const elapsed = Date.now() - this.progress.startTime;
                const avgTimePerItem = elapsed / completed;
                const remaining = this.progress.total - completed;
                this.progress.estimatedTimeLeft = Math.round((avgTimePerItem * remaining) / 1000);
            }

            this._notify();
        }

        updateScene(sceneName, stepIndex, stepLabel) {
            this.progress.currentScene = sceneName;
            this.progress.currentStep = stepIndex;
            this.progress.stepLabel = stepLabel;
            this._notify();
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

            // Console log
            const prefix = type === 'error' ? '❌' : type === 'warning' ? '⚠️' : '✅';
            console.log(`[YouTube Uploader] ${prefix} ${message}`);
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
    YTU.StateManager = StateManager;

})(window.YouTubeUploader || (window.YouTubeUploader = {}));
