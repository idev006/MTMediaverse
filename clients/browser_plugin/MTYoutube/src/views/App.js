/**
 * App.js - Main Application Entry & UI
 * Implements Vue.js with Render Functions (No Templates) to avoid CSP/Parsing errors.
 * Architecture matches Tiktok3 pattern.
 * 
 * @memberof YouTubeUploader
 */
(function (YTU) {
    'use strict';

    YTU.init = async function () {
        console.log('[YTU] Initializing...');

        try {
            // 1. Initialize Architecture
            // Using existing classes defined in Namespace or global
            YTU.State = new YTU.StateManager();

            // Fix: Check if Stub1_Api is available as Stubs.Api or direct class
            // Namespace.js assigns global.YouTubeUploader.Stub1_Api
            YTU.Api = new YTU.Stub1_Api(YTU.State.config.apiBaseUrl || 'http://127.0.0.1:8000');

            YTU.Human = new YTU.HumanLike(YTU.State.config.humanLike);
            YTU.Page = new YTU.PageHandler(YTU.Human, YTU.State);
            YTU.Scene = new YTU.SceneManager(YTU.State, YTU.Api);

            // ViewModel acts as Automation Engine
            YTU.ViewModel = new YTU.AppViewModel(YTU.State, YTU.Scene, YTU.Api, YTU.Page);

            // 2. Create Sidebar Container
            if (!document.getElementById('youtube-uploader-sidebar')) {
                const sidebar = document.createElement('div');
                sidebar.id = 'youtube-uploader-sidebar';
                sidebar.className = 'ytu-sidebar';
                document.body.appendChild(sidebar);

                // Push content
                document.documentElement.style.cssText =
                    `margin-right: ${YTU.State.config.sidebarWidth || 450}px !important; transition: margin-right 0.3s ease !important;`;
            }

            // 3. Create Vue App (Render Functions)
            const { createApp, ref, reactive, computed, h, onMounted, watch } = Vue;

            const app = createApp({
                setup() {
                    // --- State ---
                    const isCollapsed = ref(false);
                    const activeTab = ref('queue'); // queue, settings, log
                    const serverOnline = ref(false);
                    const isProcessing = ref(false);
                    const isPaused = ref(false);

                    const products = ref([]);
                    const currentProduct = ref(null);
                    const logs = ref([]);

                    const progress = reactive({
                        total: 0, completed: 0, success: 0, failed: 0,
                        currentScene: '', stepLabel: 'Ready'
                    });

                    // Config Proxy
                    const config = reactive({
                        clientCode: '',
                        autoPost: false,
                        productDelayMin: 60,
                        productDelayMax: 120,
                        stepDelayMin: 1,
                        stepDelayMax: 3
                    });

                    // --- Sync with StateManager ---
                    const syncState = (state) => {
                        serverOnline.value = state.serverOnline;
                        isProcessing.value = state.isProcessing;
                        isPaused.value = state.isPaused;
                        products.value = [...state.products];
                        currentProduct.value = state.currentProduct;
                        logs.value = [...state.logs]; // Limit logs if needed

                        progress.total = state.progress.total;
                        progress.completed = state.progress.completed;
                        progress.success = state.progress.success;
                        progress.failed = state.progress.failed;
                        progress.currentScene = state.progress.currentScene;
                        progress.stepLabel = state.progress.stepLabel;
                    };

                    onMounted(() => {
                        // Load initial config
                        config.clientCode = YTU.State.config.clientCode;
                        config.autoPost = YTU.State.config.autoPost;
                        config.productDelayMin = YTU.State.config.productDelay.min / 1000;
                        config.productDelayMax = YTU.State.config.productDelay.max / 1000;
                        config.stepDelayMin = YTU.State.config.stepDelay.min / 1000;
                        config.stepDelayMax = YTU.State.config.stepDelay.max / 1000;

                        // Subscribe
                        YTU.State.subscribe(syncState);
                        syncState(YTU.State);

                        // Initial check
                        YTU.ViewModel.checkServer();
                    });

                    // --- Computed ---
                    const progressPercent = computed(() =>
                        progress.total === 0 ? 0 : Math.round((progress.completed / progress.total) * 100));

                    const statusText = computed(() => {
                        if (!serverOnline.value) return '🔴 Offline';
                        return isProcessing.value ? (isPaused.value ? '⏸️ Paused' : '🟢 Running') : '🟡 Ready';
                    });

                    const isOnline = computed(() => isProcessing.value && !isPaused.value);

                    // --- Actions ---
                    const toggleCollapse = () => {
                        isCollapsed.value = !isCollapsed.value;
                        const sidebar = document.getElementById('youtube-uploader-sidebar');
                        if (sidebar) {
                            sidebar.style.display = isCollapsed.value ? 'none' : 'block'; // Simple hide for now or use class
                            document.documentElement.style.marginRight = isCollapsed.value ? '0' : '450px';
                        }
                    };

                    const applyConfig = () => {
                        YTU.State.config.clientCode = config.clientCode;
                        YTU.State.config.autoPost = config.autoPost;
                        YTU.State.config.productDelay = { min: config.productDelayMin * 1000, max: config.productDelayMax * 1000 };
                        YTU.State.config.stepDelay = { min: config.stepDelayMin * 1000, max: config.stepDelayMax * 1000 };
                        YTU.State.saveConfig();
                        YTU.Api.setClientCode(config.clientCode);
                        YTU.State.addLog('✅ Config saved');
                    };

                    const clearLogs = () => YTU.State.clearLogs();

                    // --- Render ---
                    return () => h('div', { class: ['ytu-container', { collapsed: isCollapsed.value }] }, [

                        // Header
                        h('div', { class: 'ytu-header', onDblclick: toggleCollapse }, [
                            h('div', { class: 'ytu-title' }, [
                                h('span', { class: 'ytu-logo' }, '📺'),
                                h('span', {}, 'YouTube Uploader')
                            ]),
                            h('div', { class: ['ytu-status', { online: isOnline.value }] }, statusText.value)
                        ]),

                        // Progress
                        isProcessing.value && h('div', { class: 'ytu-progress' }, [
                            h('div', { class: 'ytu-progress-bar' }, [
                                h('div', { class: 'ytu-progress-fill', style: { width: progressPercent.value + '%' } })
                            ]),
                            h('div', { class: 'ytu-progress-text' }, `${progress.currentScene} - ${progress.stepLabel}`),
                            h('div', { class: 'ytu-stats' }, `✅ ${progress.success} | ❌ ${progress.failed} | 📦 ${progress.completed}/${progress.total}`)
                        ]),

                        // Tabs
                        h('div', { class: 'ytu-tabs' }, [
                            h('button', { class: { active: activeTab.value === 'queue' }, onClick: () => activeTab.value = 'queue' }, 'Queue'),
                            h('button', { class: { active: activeTab.value === 'settings' }, onClick: () => activeTab.value = 'settings' }, 'Settings'),
                            h('button', { class: { active: activeTab.value === 'log' }, onClick: () => activeTab.value = 'log' }, 'Log')
                        ]),

                        // Content
                        h('div', { class: 'ytu-content' }, [

                            // QUEUE TAB
                            activeTab.value === 'queue' && h('div', { class: 'ytu-tab-content' }, [
                                h('div', { class: 'ytu-actions' }, [
                                    h('button', { onClick: () => YTU.ViewModel.checkServer(), disabled: isProcessing.value }, '🔄 Check'),
                                    h('button', { onClick: () => YTU.ViewModel.fetchProducts(), disabled: isProcessing.value }, '📦 Fetch'),
                                    !isProcessing.value
                                        ? h('button', {
                                            class: 'primary',
                                            onClick: () => YTU.ViewModel.startBatch(),
                                            disabled: products.value.length === 0
                                        }, '🚀 Start')
                                        : h('button', { class: 'danger', onClick: () => YTU.ViewModel.stopBatch() }, '🛑 Stop'),
                                    isProcessing.value && h('button', { onClick: () => YTU.ViewModel.togglePause() }, isPaused.value ? '▶️ Resume' : '⏸️ Pause')
                                ]),
                                h('div', { class: 'ytu-queue' }, [
                                    currentProduct.value && h('div', { class: 'ytu-current' }, '🎯 ' + currentProduct.value.prod_code),
                                    products.value.length === 0
                                        ? h('div', { class: 'ytu-empty' }, 'No products in queue')
                                        : products.value.map((p, i) => h('div', {
                                            key: p.prod_code,
                                            class: 'ytu-queue-item'
                                        }, `${i + 1}. ${p.prod_code}`))
                                ])
                            ]),

                            // SETTINGS TAB
                            activeTab.value === 'settings' && h('div', { class: 'ytu-tab-content' }, [
                                h('div', { class: 'ytu-setting' }, [
                                    h('label', {}, 'Client Code'),
                                    h('input', {
                                        type: 'text',
                                        value: config.clientCode,
                                        onInput: (e) => config.clientCode = e.target.value,
                                        placeholder: 'Enter client code'
                                    })
                                ]),
                                h('div', { class: 'ytu-setting' }, [
                                    h('label', {}, [
                                        h('input', {
                                            type: 'checkbox',
                                            checked: config.autoPost,
                                            onChange: (e) => config.autoPost = e.target.checked
                                        }),
                                        ' Auto Post'
                                    ])
                                ]),
                                h('button', { class: 'primary', onClick: applyConfig }, '💾 Save Config'),
                                h('button', {
                                    class: 'danger', onClick: async () => {
                                        if (confirm('Reset all?')) { await YTU.ViewModel.resetAll(); await YTU.ViewModel.fetchProducts(); }
                                    }
                                }, '🔄 Reset All Status')
                            ]),

                            // LOG TAB
                            activeTab.value === 'log' && h('div', { class: 'ytu-tab-content' }, [
                                h('div', { class: 'ytu-log-box', ref: 'logBox' },
                                    logs.value.map((log, i) => h('div', {
                                        key: i,
                                        class: ['ytu-log-item', log.type]
                                    }, [
                                        h('span', { class: 'time' }, log.timestamp),
                                        h('span', { class: 'msg' }, log.message)
                                    ]))
                                ),
                                h('button', { onClick: clearLogs }, '🗑️ Clear Logs')
                            ])
                        ])
                    ]);
                }
            });

            YTU.VueApp = app.mount('#youtube-uploader-sidebar');
            console.log('[YTU] Vue App Mounted Successfully');

        } catch (error) {
            console.error('[YTU] Init Error:', error);
        }
    };

})(window.YouTubeUploader || (window.YouTubeUploader = {}));
