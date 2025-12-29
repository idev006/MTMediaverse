/**
 * BackendStub - Middleware for server communication
 */
export class BackendStub {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }

    async healthCheck() {
        try {
            const res = await fetch(`${this.baseUrl}/health`);
            return await res.json();
        } catch (e) {
            console.error('[Stub] Health check failed', e);
            return { status: 'error' };
        }
    }

    async sendEvent(eventData) {
        try {
            const res = await fetch(`${this.baseUrl}/api/suno/webhook`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(eventData)
            });
            return await res.json();
        } catch (e) {
            console.error('[Stub] Send event failed', e);
            return { error: e.message };
        }
    }
}
