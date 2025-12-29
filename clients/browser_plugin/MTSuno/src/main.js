import { createApp } from 'vue'
import App from './App.vue'
import './index.css'
import { BackendStub } from './services/BackendStub.js'

(function (MTSuno) {
    'use strict';

    MTSuno.init = function () {
        console.log('[MTSuno] Initializing...');

        // 1. Initialize Services (Stub)
        MTSuno.Stub = new BackendStub('http://localhost:8000');

        // 2. Create UI Container (Fixed Overlay)
        const containerId = 'mt-suno-root';
        if (!document.getElementById(containerId)) {
            const container = document.createElement('div');
            container.id = containerId;
            // Shadow DOM could be used here to isolate Tailwind, but simple root is requested for now.
            // If using Shadow DOM, we need to inject styles inside it. 
            // For now, we'll append to body and rely on scoped CSS or specific ID/class strategies.
            // Vite build will output style.css which content script must fetch/inject.
            document.body.appendChild(container);

            // Mount Vue App
            const app = createApp(App);
            // Provide global instances if needed
            app.config.globalProperties.$stub = MTSuno.Stub;
            app.mount(container);

            console.log('[MTSuno] Vue App Mounted');
        }
    };

    // Auto-init for content script (or can be triggered manualy)
    // Wait for DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', MTSuno.init);
    } else {
        MTSuno.init();
    }

})(window.MTSuno || (window.MTSuno = {}));
