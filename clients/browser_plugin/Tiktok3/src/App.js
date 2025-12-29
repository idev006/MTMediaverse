/**
 * App - Main application with Vue.js + Tabs UI
 * Tabs: Queue, Order, Settings, Log
 * 
 * @memberof TikTokUploader
 */
(function (TTU) {
    'use strict';

    TTU.init = async function () {
        console.log('[TTU] Initializing...');

        try {
            // 1. Initialize classes
            TTU.State = new TTU.StateManager();
            TTU.Api = new TTU.ApiClient('http://127.0.0.1:8000');
            TTU.Human = new TTU.HumanLike(TTU.State.config.humanLike);
            TTU.Page = new TTU.PageHandler(TTU.Human, TTU.State);
            TTU.Automation = new TTU.AutomationEngine(TTU.State, TTU.Api, TTU.Page);

            // 2. Create sidebar container if not exists
            if (!document.getElementById('tiktok-uploader-sidebar')) {
                const sidebar = document.createElement('div');
                sidebar.id = 'tiktok-uploader-sidebar';
                document.body.appendChild(sidebar);
                // Push body content to make room for sidebar
                document.documentElement.style.cssText = 'margin-right: 400px !important; transition: margin-right 0.3s ease !important;';
            }

            // 3. Create Vue app
            const { createApp, ref, reactive, computed, h } = Vue;

            const app = createApp({
                setup() {
                    // --- Styles ---
                    // Force inject font
                    const fontId = 'ttu-chakra-font';
                    if (!document.getElementById(fontId)) {
                        const link = document.createElement('link');
                        link.id = fontId;
                        link.href = 'https://fonts.googleapis.com/css2?family=Chakra+Petch:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300;1,400;1,500;1,600;1,700&display=swap';
                        link.rel = 'stylesheet';
                        document.head.appendChild(link);
                    }

                    // --- State ---
                    const isCollapsed = ref(false);
                    const activeTab = ref('queue'); // queue, order, settings, log
                    const serverOnline = ref(false);
                    const isProcessing = ref(false);
                    const isPaused = ref(false);
                    const waitingForManualPost = ref(false);

                    // Data
                    const products = ref([]);
                    const currentProduct = ref(null);
                    const logs = ref([]);

                    // Order Tab State
                    const catalog = ref([]);
                    const orderSearch = ref('');
                    const orderQtys = reactive({}); // { 'P001': 2 }

                    // Progress
                    const progress = reactive({
                        total: 0, completed: 0, success: 0, failed: 0,
                        currentStep: 0, stepLabel: 'Ready'
                    });

                    // Config (Reactive copy of TTU.State.config for UI)
                    const config = reactive({
                        productDelayMin: TTU.State.config.productDelay.min,
                        productDelayMax: TTU.State.config.productDelay.max,
                        stepDelayMin: TTU.State.config.stepDelay.min,
                        stepDelayMax: TTU.State.config.stepDelay.max,
                        videoProcessDelayMin: TTU.State.config.videoProcessDelay?.min || 2000,
                        videoProcessDelayMax: TTU.State.config.videoProcessDelay?.max || 5000,
                        maxRetries: TTU.State.config.maxRetries || 2,
                        humanLike: TTU.State.config.humanLike.enabled,
                        autoPost: TTU.State.config.autoPost,
                        clientCode: TTU.State.config.clientCode || '',
                        heartbeatInterval: TTU.State.config.heartbeatInterval || 5000,
                        opacity: 100,
                        skipRealPost: TTU.State.config.skipRealPost || false
                    });

                    // Init Client Code
                    if (config.clientCode) {
                        TTU.Api.setClientCode(config.clientCode);
                    }

                    // --- Computed ---
                    const percent = computed(() =>
                        progress.total > 0 ? Math.round((progress.completed / progress.total) * 100) : 0
                    );

                    const filteredCatalog = computed(() => {
                        if (!orderSearch.value) return catalog.value;
                        const s = orderSearch.value.toLowerCase();
                        return catalog.value.filter(p =>
                            p.code.toLowerCase().includes(s) ||
                            p.name.toLowerCase().includes(s)
                        );
                    });

                    // --- Subsriptions ---
                    TTU.State.subscribe((state) => {
                        serverOnline.value = state.serverOnline;
                        isProcessing.value = state.isProcessing;
                        isPaused.value = state.isPaused;
                        waitingForManualPost.value = state.waitingForManualPost;
                        products.value = [...state.products];
                        currentProduct.value = state.currentProduct;
                        logs.value = [...state.logs].slice(-50);

                        progress.total = state.progress.total;
                        progress.completed = state.progress.completed;
                        progress.success = state.progress.success;
                        progress.failed = state.progress.failed;
                        progress.currentStep = state.progress.currentStep;
                        progress.stepLabel = state.progress.stepLabel;
                    });

                    // --- Methods ---
                    const applyConfig = () => {
                        TTU.State.config.productDelay.min = config.productDelayMin;
                        TTU.State.config.productDelay.max = config.productDelayMax;
                        TTU.State.config.stepDelay.min = config.stepDelayMin;
                        TTU.State.config.stepDelay.max = config.stepDelayMax;

                        // Initialize videoProcessDelay if doesn't exist
                        TTU.State.config.videoProcessDelay = TTU.State.config.videoProcessDelay || {};
                        TTU.State.config.videoProcessDelay.min = config.videoProcessDelayMin;
                        TTU.State.config.videoProcessDelay.max = config.videoProcessDelayMax;

                        TTU.State.config.maxRetries = config.maxRetries;

                        TTU.State.config.humanLike.enabled = config.humanLike;
                        TTU.State.config.autoPost = config.autoPost;
                        TTU.State.config.skipRealPost = config.skipRealPost;
                        TTU.State.config.clientCode = config.clientCode;
                        TTU.State.config.heartbeatInterval = config.heartbeatInterval;

                        TTU.Api.setClientCode(config.clientCode);
                        TTU.Human.setConfig({ enabled: config.humanLike });

                        TTU.State.saveConfig();
                        TTU.State.addLog('⚙️ Settings updated & Saved');
                    };

                    const fetchCatalog = async () => {
                        TTU.State.addLog('⏳ Fetching product catalog...');
                        const res = await TTU.Api.getCatalog();
                        if (res.success) {
                            catalog.value = res.catalog;
                            // Reset quantities
                            Object.keys(orderQtys).forEach(k => delete orderQtys[k]);
                            res.catalog.forEach(p => orderQtys[p.code] = 0);
                            TTU.State.addLog('✅ Loaded ' + res.catalog.length + ' items to catalog');
                        } else {
                            TTU.State.addLog('❌ Fetch failed: ' + res.error, 'error');
                        }
                    };

                    const submitOrderNew = async () => {
                        if (!config.clientCode) {
                            TTU.State.addLog('⚠️ Please set Client Code in Settings first!', 'error');
                            activeTab.value = 'settings';
                            return;
                        }

                        // Filter items with Qty > 0
                        const items = [];
                        for (const [code, qty] of Object.entries(orderQtys)) {
                            if (qty > 0) items.push({ code, qty });
                        }

                        if (items.length === 0) {
                            TTU.State.addLog('⚠️ No items selected. Please enter quantity > 0.', 'error');
                            return;
                        }

                        TTU.State.addLog('⏳ Sending order for ' + items.length + ' items...');
                        const res = await TTU.Api.createOrder(items);

                        if (res.success) {
                            TTU.State.addLog('✅ Order #' + res.batch_id + ' created with ' + res.job_count + ' jobs!', 'success');
                            activeTab.value = 'queue';
                            setTimeout(() => TTU.Automation.fetchProducts(), 1000);
                        } else {
                            TTU.State.addLog('❌ Order failed: ' + res.error, 'error');
                        }
                    };

                    const toggleCollapse = () => {
                        isCollapsed.value = !isCollapsed.value;
                        const sidebar = document.getElementById('tiktok-uploader-sidebar');
                        if (sidebar) {
                            sidebar.classList.toggle('ttu-collapsed', isCollapsed.value);
                            sidebar.style.opacity = isCollapsed.value ? '1' : (config.opacity / 100).toString();
                            sidebar.style.pointerEvents = (config.opacity < 20) ? 'none' : 'auto';
                        }
                        document.documentElement.style.marginRight = isCollapsed.value ? '0' : '500px';
                    };

                    const updateOpacity = (e) => {
                        config.opacity = +e.target.value;
                        const sidebar = document.getElementById('tiktok-uploader-sidebar');
                        if (sidebar && !isCollapsed.value) {
                            sidebar.style.opacity = (config.opacity / 100).toString();
                        }
                    };

                    const togglePause = () => {
                        if (isPaused.value) {
                            TTU.State.resumeProcessing();
                            TTU.State.addLog('▶️ Resumed');
                        } else {
                            TTU.State.pauseProcessing();
                            TTU.State.addLog('⏸️ Paused');
                        }
                    };

                    const getStepIcon = (prod) => {
                        if (currentProduct.value?.prod_code === prod.prod_code) {
                            return ['⏳', '📥', '📤', '🎬', '📝'][progress.currentStep] || '⏳';
                        }
                        return '○';
                    };

                    const resumeSession = () => {
                        const backup = TTU.Automation.loadSessionBackup();
                        if (!backup) {
                            TTU.State.addLog('⚠️ No session backup found', 'warning');
                            return;
                        }

                        // Restore products
                        TTU.State.setProducts(backup.products);

                        // Restore progress counters
                        TTU.State.initProgress(backup.total);
                        TTU.State.updateProgress(backup.processed, backup.success, backup.failed);

                        TTU.State.addLog(`✅ Session restored: ${backup.products.length} items pending`, 'success');
                        activeTab.value = 'queue';
                    };

                    // --- RENDER FUNCTION ---
                    return () => {
                        return h('div', { class: 'ttu-root' }, [
                            // 1. Header
                            h('div', { class: 'ttu-header' }, [
                                h('span', { class: 'ttu-header-icon' }, '🎬'),
                                h('span', { class: 'ttu-header-title' }, 'TikTok Uploader'),
                                h('span', {
                                    class: ['ttu-status-dot', serverOnline.value ? 'online' : 'offline'],
                                    title: serverOnline.value ? 'Server Online' : 'Server Offline'
                                }),
                                h('button', {
                                    class: 'ttu-btn-toggle',
                                    onClick: toggleCollapse,
                                    title: isCollapsed.value ? 'Expand panel' : 'Collapse panel'
                                }, isCollapsed.value ? '+' : '−')
                            ]),

                            // 2. Main Body (Hidden if collapsed)
                            !isCollapsed.value && h('div', { class: 'ttu-main' }, [

                                // Status Bar
                                h('div', { class: 'ttu-status-bar' }, [
                                    h('span', { class: 'ttu-badge ttu-badge-success', title: 'Successful uploads' }, '✓ ' + progress.success),
                                    h('span', { class: 'ttu-badge ttu-badge-error', title: 'Failed uploads' }, '✗ ' + progress.failed),
                                    progress.total > 0 && h('span', { class: 'ttu-badge' }, progress.completed + '/' + progress.total),

                                    // Current Step (detailed)
                                    isProcessing.value && !isPaused.value && h('span', { class: 'ttu-processing-label' },
                                        `🔄 [${progress.currentStep}/7] ${progress.stepLabel}`),

                                    // Paused status
                                    isPaused.value && h('span', { class: 'ttu-processing-label', style: 'color: #ff9800;' }, '⏸️ Paused'),

                                    // ETA
                                    progress.estimatedTimeLeft && isProcessing.value && !isPaused.value && h('span', {
                                        class: 'ttu-badge',
                                        style: 'background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;',
                                        title: 'Estimated Time Remaining'
                                    }, (() => {
                                        const seconds = progress.estimatedTimeLeft;
                                        if (seconds < 60) return `⏱️ ${seconds}s`;
                                        const mins = Math.floor(seconds / 60);
                                        const secs = seconds % 60;
                                        if (mins < 60) return `⏱️ ${mins}m ${secs}s`;
                                        const hours = Math.floor(mins / 60);
                                        const remainMins = mins % 60;
                                        return `⏱️ ${hours}h ${remainMins}m`;
                                    })())
                                ]),

                                // Control Bar
                                h('div', { class: 'ttu-control-bar', style: 'padding: 10px; background: rgba(0,0,0,0.2); border-bottom: 1px solid var(--glass-border);' }, [
                                    h('div', { class: 'ttu-flex ttu-gap-2' }, [
                                        !isProcessing.value
                                            ? h('button', {
                                                class: 'ttu-btn ttu-btn-success ttu-flex-1',
                                                disabled: products.value.length === 0,
                                                onClick: () => TTU.Automation.startBatch(),
                                                title: 'Start batch upload',
                                                style: 'font-size: 14px; padding: 10px; box-shadow: 0 0 10px rgba(0,255,157,0.3);'
                                            }, '🚀 START UPLOAD')
                                            : h('button', {
                                                class: ['ttu-btn', 'ttu-flex-1', isPaused.value ? 'ttu-btn-success' : 'ttu-btn-warning'],
                                                onClick: togglePause,
                                                title: isPaused.value ? 'Resume processing' : 'Pause after current item'
                                            }, isPaused.value ? '▶️ RESUME' : '⏸️ PAUSE'),

                                        h('button', {
                                            class: 'ttu-btn ttu-btn-error',
                                            disabled: !isProcessing.value,
                                            onClick: () => TTU.Automation.stopBatch(),
                                            title: 'Stop processing',
                                            style: 'min-width: 80px;'
                                        }, '🛑 STOP')
                                    ])
                                ]),

                                // Progress Bar
                                progress.total > 0 && h('div', { class: 'ttu-progress-bar' }, [
                                    h('div', {
                                        class: 'ttu-progress-fill',
                                        style: { width: percent.value + '%' }
                                    })
                                ]),

                                // Manual Trigger
                                waitingForManualPost.value && h('div', {
                                    class: 'ttu-manual-trigger',
                                    style: 'padding: 10px; background: #fff3cd; text-align: center; border-bottom: 1px solid #ffeeba;'
                                }, [
                                    h('button', {
                                        class: 'ttu-btn ttu-btn-primary ttu-btn-block',
                                        style: 'font-weight: bold; background: #e02d2d; border-color: #c01c1c; animation: pulse 1.5s infinite;',
                                        onClick: () => TTU.State.triggerManualPost()
                                    }, '🚀 Auto Click Post (Click to Confirm)')
                                ]),

                                // Tabs
                                h('div', { class: 'ttu-tabs' }, [
                                    h('button', {
                                        class: ['ttu-tab', activeTab.value === 'queue' && 'active'],
                                        onClick: () => activeTab.value = 'queue'
                                    }, '📦 Queue (' + products.value.length + ')'),
                                    h('button', {
                                        class: ['ttu-tab', activeTab.value === 'order' && 'active'],
                                        onClick: () => activeTab.value = 'order'
                                    }, '🛒 Order'),
                                    h('button', {
                                        class: ['ttu-tab', activeTab.value === 'settings' && 'active'],
                                        onClick: () => activeTab.value = 'settings'
                                    }, '⚙️ Settings'),
                                    h('button', {
                                        class: ['ttu-tab', activeTab.value === 'log' && 'active'],
                                        onClick: () => activeTab.value = 'log'
                                    }, '📋 Log')
                                ]),

                                // Tab Content Container
                                h('div', { class: 'ttu-tab-content' }, [

                                    // ========== QUEUE TAB ==========
                                    activeTab.value === 'queue' && h('div', { class: 'ttu-queue-tab' }, [
                                        h('div', { class: 'ttu-scroll-panel' }, [
                                            products.value.length === 0
                                                ? h('div', { class: 'ttu-empty' }, 'No products. Click Refresh to load.')
                                                : h('div', { class: 'ttu-table-container' }, [
                                                    h('table', { class: 'ttu-table' }, [
                                                        h('thead', {}, [
                                                            h('tr', {}, [
                                                                h('th', { style: 'width: 30px' }, '#'),
                                                                h('th', { style: 'width: 80px' }, 'Code'),
                                                                h('th', { style: 'width: 120px' }, 'Name'),
                                                                h('th', { style: 'width: 100px' }, 'Schedule'),
                                                                h('th', { style: 'width: 40px' }, 'St')
                                                            ])
                                                        ]),
                                                        h('tbody', {},
                                                            products.value.map((prod, idx) => {
                                                                let schedText = '-';
                                                                if (prod.when_to_post === 'schedule') {
                                                                    schedText = prod.sched_date + '\n' + prod.sched_time;
                                                                }
                                                                return h('tr', {
                                                                    key: prod.prod_code,
                                                                    class: currentProduct.value?.prod_code === prod.prod_code ? 'active' : ''
                                                                }, [
                                                                    h('td', {}, idx + 1),
                                                                    h('td', { class: 'ttu-code', title: prod.prod_code }, prod.prod_code),
                                                                    h('td', { class: 'ttu-name', title: prod.prod_name }, prod.prod_name || '-'),
                                                                    h('td', { class: 'ttu-sched' }, schedText),
                                                                    h('td', { class: 'ttu-step' }, getStepIcon(prod))
                                                                ]);
                                                            })
                                                        )
                                                    ])
                                                ]),

                                            // Current Detail
                                            currentProduct.value && h('div', { class: 'ttu-current-detail' }, [
                                                h('div', { class: 'ttu-flex ttu-gap-2 ttu-mb-2' }, [
                                                    h('span', { class: 'ttu-label-strong' }, currentProduct.value.prod_code),
                                                    h('span', { class: 'ttu-badge ttu-badge-success' }, 'Active')
                                                ]),
                                                h('div', { class: 'ttu-detail-row' }, [
                                                    h('div', { class: 'ttu-label-xs' }, 'NAME'),
                                                    h('div', { class: 'ttu-text-content' }, currentProduct.value.prod_name || '-')
                                                ])
                                                // (Simplified current detail for brevity, can add more later if needed)
                                            ])
                                        ]),

                                        // Queue Footer
                                        h('div', { class: 'ttu-tab-footer' }, [
                                            h('button', {
                                                class: 'ttu-btn ttu-btn-outline',
                                                onClick: resumeSession,
                                                title: 'Resume previous session from backup',
                                                style: 'min-width: 60px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none;'
                                            }, '📂'),
                                            h('button', {
                                                class: 'ttu-btn ttu-btn-outline',
                                                onClick: () => {
                                                    products.value.sort(() => Math.random() - 0.5);
                                                    TTU.State.addLog('🔀 Queue shuffled!');
                                                },
                                                title: 'Shuffle queue'
                                            }, '🔀'),
                                            h('button', {
                                                class: 'ttu-btn ttu-btn-outline ttu-flex-1',
                                                onClick: () => TTU.Automation.checkServer(),
                                                title: 'Check server connection'
                                            }, '🔌 Check Connect'),
                                            h('button', {
                                                class: 'ttu-btn ttu-btn-outline',
                                                onClick: async () => {
                                                    await TTU.Automation.resetAll();
                                                    await TTU.Automation.fetchProducts();
                                                },
                                                title: 'Reset all status & fetch again'
                                            }, '🔄')
                                        ])
                                    ]),

                                    // ========== ORDER TAB ==========
                                    activeTab.value === 'order' && h('div', { class: 'ttu-order-tab' }, [
                                        h('div', { class: 'ttu-scroll-panel' }, [
                                            // Search
                                            h('div', { class: 'ttu-flex ttu-gap-2 ttu-mb-2' }, [
                                                h('input', {
                                                    type: 'text', class: 'ttu-input ttu-flex-1',
                                                    placeholder: '🔍 Search product code/name...',
                                                    value: orderSearch.value,
                                                    onInput: (e) => orderSearch.value = e.target.value
                                                }),
                                                h('button', {
                                                    class: 'ttu-btn ttu-btn-outline',
                                                    onClick: fetchCatalog,
                                                    title: 'Refresh Catalog'
                                                }, '↻ Reload')
                                            ]),
                                            // Catalog list
                                            filteredCatalog.value.length === 0
                                                ? h('div', { class: 'ttu-empty' }, catalog.value.length === 0 ? 'Click reload to load catalog.' : 'No matching products.')
                                                : h('div', { class: 'ttu-table-container' }, [
                                                    h('table', { class: 'ttu-table' }, [
                                                        h('thead', {}, [
                                                            h('tr', {}, [
                                                                h('th', {}, 'Product'),
                                                                h('th', { style: 'width: 60px' }, 'Stock'),
                                                                h('th', { style: 'width: 80px' }, 'Qty')
                                                            ])
                                                        ]),
                                                        h('tbody', {},
                                                            filteredCatalog.value.map(prod => {
                                                                return h('tr', { key: prod.code }, [
                                                                    h('td', {}, [
                                                                        h('div', { class: 'ttu-code' }, prod.code),
                                                                        h('div', { class: 'ttu-name' }, prod.name || '-')
                                                                    ]),
                                                                    h('td', { style: 'text-align: center' },
                                                                        h('span', { class: ['ttu-badge', prod.stock > 0 ? 'ttu-badge-success' : 'ttu-badge-error'] }, prod.stock)
                                                                    ),
                                                                    h('td', {},
                                                                        h('input', {
                                                                            type: 'number', class: 'ttu-input', style: 'width: 100%; text-align: center;',
                                                                            min: 0, max: prod.stock,
                                                                            value: orderQtys[prod.code] || 0,
                                                                            onInput: (e) => {
                                                                                let val = +e.target.value;
                                                                                if (val < 0) val = 0;
                                                                                orderQtys[prod.code] = val;
                                                                            }
                                                                        })
                                                                    )
                                                                ]);
                                                            })
                                                        )
                                                    ])
                                                ])
                                        ]),
                                        // Order Footer
                                        h('div', { class: 'ttu-tab-footer' }, [
                                            h('button', {
                                                class: 'ttu-btn ttu-btn-outline',
                                                onClick: () => {
                                                    Object.keys(orderQtys).forEach(key => orderQtys[key] = 0);
                                                    TTU.State.addLog('🧹 Order form cleared by user');
                                                },
                                                title: 'Clear all quantities'
                                            }, '🗑️'),
                                            h('button', {
                                                class: 'ttu-btn ttu-btn-primary ttu-flex-1',
                                                onClick: submitOrderNew
                                            }, '🛒 Submit Order')
                                        ])
                                    ]),

                                    // ========== SETTINGS TAB ==========
                                    activeTab.value === 'settings' && h('div', { class: 'ttu-order-tab' }, [
                                        h('div', { class: 'ttu-scroll-panel' }, [

                                            // Group 1: Identity
                                            h('div', { class: 'ttu-flex ttu-gap-2' }, [
                                                h('div', { class: 'ttu-setting-group ttu-flex-1' }, [
                                                    h('div', { class: 'ttu-setting-title' }, '🔑 Client Identity'),
                                                    h('input', {
                                                        type: 'text', class: 'ttu-input', style: 'width: 100%; font-family: monospace;',
                                                        value: config.clientCode,
                                                        onInput: (e) => config.clientCode = e.target.value,
                                                        placeholder: 'Code'
                                                    })
                                                ]),
                                                h('div', { class: 'ttu-setting-group ttu-flex-1' }, [
                                                    h('div', { class: 'ttu-setting-title' }, '💓 Heartbeat (ms)'),
                                                    h('input', {
                                                        type: 'number', class: 'ttu-input', style: 'width: 100%',
                                                        value: config.heartbeatInterval,
                                                        onInput: (e) => config.heartbeatInterval = +e.target.value,
                                                        placeholder: '5000'
                                                    })
                                                ])
                                            ]),

                                            // Group 2: Opacity
                                            h('div', { class: 'ttu-setting-group' }, [
                                                h('div', { class: 'ttu-setting-title' }, '👻 Panel Opacity'),
                                                h('div', { class: 'ttu-flex ttu-gap-2', style: 'align-items: center;' }, [
                                                    h('input', {
                                                        type: 'range', class: 'ttu-range', min: '20', max: '100',
                                                        value: config.opacity,
                                                        onInput: updateOpacity,
                                                        style: 'flex: 1'
                                                    }),
                                                    h('span', { style: 'width: 40px; text-align: right;' }, config.opacity + '%')
                                                ])
                                            ]),

                                            // Group 3: Delays
                                            h('div', { class: 'ttu-setting-group' }, [
                                                h('div', { class: 'ttu-setting-title' }, '⏱️ Delays (Min - Max)'),
                                                h('div', { class: 'ttu-flex ttu-gap-2', style: 'margin-bottom: 8px; align-items: center;' }, [
                                                    h('span', { style: 'width: 60px; font-size: 11px; color: #888;' }, 'Product:'),
                                                    h('input', {
                                                        type: 'number', class: 'ttu-input ttu-flex-1',
                                                        value: config.productDelayMin,
                                                        onInput: (e) => config.productDelayMin = +e.target.value,
                                                        placeholder: 'Min'
                                                    }),
                                                    h('input', {
                                                        type: 'number', class: 'ttu-input ttu-flex-1',
                                                        value: config.productDelayMax,
                                                        onInput: (e) => config.productDelayMax = +e.target.value,
                                                        placeholder: 'Max'
                                                    })
                                                ]),
                                                h('div', { class: 'ttu-flex ttu-gap-2', style: 'align-items: center;' }, [
                                                    h('span', { style: 'width: 60px; font-size: 11px; color: #888;' }, 'Step:'),
                                                    h('input', {
                                                        type: 'number', class: 'ttu-input ttu-flex-1',
                                                        value: config.stepDelayMin,
                                                        onInput: (e) => config.stepDelayMin = +e.target.value,
                                                        placeholder: 'Min'
                                                    }),
                                                    h('input', {
                                                        type: 'number', class: 'ttu-input ttu-flex-1',
                                                        value: config.stepDelayMax,
                                                        onInput: (e) => config.stepDelayMax = +e.target.value,
                                                        placeholder: 'Max'
                                                    })
                                                ]),
                                                h('div', { class: 'ttu-flex ttu-gap-2', style: 'align-items: center; margin-top: 8px;' }, [
                                                    h('span', { style: 'width: 60px; font-size: 11px; color: #888;' }, 'Video:'),
                                                    h('input', {
                                                        type: 'number', class: 'ttu-input ttu-flex-1',
                                                        value: config.videoProcessDelayMin,
                                                        onInput: (e) => config.videoProcessDelayMin = +e.target.value,
                                                        placeholder: 'Min (ms)'
                                                    }),
                                                    h('input', {
                                                        type: 'number', class: 'ttu-input ttu-flex-1',
                                                        value: config.videoProcessDelayMax,
                                                        onInput: (e) => config.videoProcessDelayMax = +e.target.value,
                                                        placeholder: 'Max (ms)'
                                                    })
                                                ])
                                            ]),

                                            // Group 3B: Retry
                                            h('div', { class: 'ttu-setting-group' }, [
                                                h('div', { class: 'ttu-setting-title' }, '🔄 Error Handling'),
                                                h('div', { class: 'ttu-flex ttu-gap-2', style: 'align-items: center;' }, [
                                                    h('span', { style: 'width: 120px; font-size: 11px; color: #888;' }, 'Max Retries:'),
                                                    h('input', {
                                                        type: 'number', class: 'ttu-input', style: 'width: 80px;',
                                                        value: config.maxRetries,
                                                        onInput: (e) => config.maxRetries = Math.max(0, Math.min(5, +e.target.value)),
                                                        min: '0', max: '5',
                                                        placeholder: '2'
                                                    }),
                                                    h('span', { style: 'font-size: 10px; color: #666; flex: 1;' }, '(0-5 attempts)')
                                                ])
                                            ]),

                                            // Group 4: Toggles
                                            h('div', { class: 'ttu-setting-group' }, [
                                                // Auto Post
                                                h('div', { class: 'ttu-flex', style: 'justify-content: space-between; align-items: center; margin-bottom: 8px;' }, [
                                                    h('span', { class: 'ttu-setting-label' }, '🚀 Auto Post (Submit)'),
                                                    h('label', { class: 'ttu-switch' }, [
                                                        h('input', {
                                                            type: 'checkbox',
                                                            checked: config.autoPost,
                                                            onChange: (e) => config.autoPost = e.target.checked
                                                        }),
                                                        h('span', { class: 'ttu-slider round' })
                                                    ])
                                                ]),
                                                // Skip Real Post
                                                h('div', { class: 'ttu-flex', style: 'justify-content: space-between; align-items: center; margin-bottom: 8px;' }, [
                                                    h('span', { class: 'ttu-setting-label', title: 'Simulate only' }, '🧪 Simulation (Skip Post)'),
                                                    h('label', { class: 'ttu-switch' }, [
                                                        h('input', {
                                                            type: 'checkbox',
                                                            checked: config.skipRealPost,
                                                            onChange: (e) => config.skipRealPost = e.target.checked
                                                        }),
                                                        h('span', { class: 'ttu-slider round', style: 'background-color: #ff9800;' })
                                                    ])
                                                ]),
                                                // Human
                                                h('div', { class: 'ttu-flex', style: 'justify-content: space-between; align-items: center;' }, [
                                                    h('span', { class: 'ttu-setting-label' }, '🤖 Human Behavior'),
                                                    h('label', { class: 'ttu-switch' }, [
                                                        h('input', {
                                                            type: 'checkbox',
                                                            checked: config.humanLike,
                                                            onChange: (e) => config.humanLike = e.target.checked
                                                        }),
                                                        h('span', { class: 'ttu-slider round' })
                                                    ])
                                                ])
                                            ])
                                        ]),

                                        // Settings Footer (Save)
                                        h('div', { class: 'ttu-tab-footer' }, [
                                            h('button', {
                                                class: 'ttu-btn ttu-btn-primary ttu-btn-block',
                                                onClick: applyConfig
                                            }, '💾 Save Settings')
                                        ])
                                    ]),

                                    // ========== LOG TAB ==========
                                    activeTab.value === 'log' && h('div', {
                                        class: 'ttu-log-tab',
                                        style: 'display: flex; flex-direction: column; height: 100%; overflow: hidden;'
                                    }, [
                                        h('div', {
                                            class: 'ttu-log',
                                            style: 'flex: 1; overflow-y: auto; overflow-x: hidden; padding: 10px; font-family: monospace; font-size: 11px; line-height: 1.5;',
                                            ref: (el) => { if (el) el.scrollTop = el.scrollHeight; }
                                        }, logs.value.map((log, i) => h('div', {
                                            key: i,
                                            class: ['ttu-log-entry', log.type],
                                            style: 'margin-bottom: 4px; word-wrap: break-word;'
                                        }, '[' + log.timestamp + '] ' + log.message)))
                                    ])

                                ]) // End Tab Content
                            ]) // End Main Body
                        ]); // End Root
                    };
                }
            });

            app.mount('#tiktok-uploader-sidebar');

            // Start automation checks
            await TTU.Automation.checkServer();
            TTU.Automation.startHeartbeatLoop();
            console.log('[TTU] Ready!');

        } catch (error) {
            console.error('[TTU] Init error:', error);
        }
    };

})(window.TikTokUploader || (window.TikTokUploader = {}));
