/**
 * ApiClient - Backend Stub for server communication
 * @memberof MTSuno
 */
(function (MTS) {
    'use strict';

    class ApiClient {
        constructor(baseUrl) {
            this.baseUrl = baseUrl || 'http://localhost:8000';
        }

        async healthCheck() {
            try {
                const res = await fetch(`${this.baseUrl}/health`, { method: 'GET' });
                if (!res.ok) throw new Error('Not OK');
                return { success: true, data: await res.json() };
            } catch (e) {
                console.warn('[ApiClient] Health check failed:', e.message);
                return { success: false, error: e.message };
            }
        }

        async sendSongEvent(eventData) {
            try {
                const res = await fetch(`${this.baseUrl}/api/suno/webhook`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(eventData)
                });
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                return { success: true, data: await res.json() };
            } catch (e) {
                console.error('[ApiClient] Send event failed:', e);
                return { success: false, error: e.message };
            }
        }
    }

    MTS.ApiClient = ApiClient;

})(window.MTSuno || (window.MTSuno = {}));
