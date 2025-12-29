// Background Service Worker - Handle API calls
const API_BASE_URL = 'http://127.0.0.1:8000';

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    // Health Check
    if (request.action === 'healthCheck') {
        fetch(`${API_BASE_URL}/health`)
            .then(response => response.json())
            .then(data => sendResponse({ success: true, data }))
            .catch(error => sendResponse({ success: false, error: error.message }));
        return true;
    }

    // Get Product List
    if (request.action === 'getProducts') {
        const includeSuccess = request.includeSuccess ? '?include_success=true' : '';
        fetch(`${API_BASE_URL}/api/products${includeSuccess}`)
            .then(response => response.json())
            .then(data => sendResponse({ success: true, data }))
            .catch(error => sendResponse({ success: false, error: error.message }));
        return true;
    }

    // Get Video
    if (request.action === 'getVideo') {
        fetch(`${API_BASE_URL}/api/get-video`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prod_code: request.prodCode })
        })
            .then(response => {
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                return response.json();
            })
            .then(data => sendResponse({ success: true, data }))
            .catch(error => sendResponse({ success: false, error: error.message }));
        return true;
    }

    // Report Upload Result
    if (request.action === 'reportUpload') {
        fetch(`${API_BASE_URL}/api/report-upload`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prod_code: request.prodCode,
                status: request.status,
                error_message: request.errorMessage || '',
                uploaded_at: new Date().toISOString()
            })
        })
            .then(response => response.json())
            .then(data => sendResponse({ success: true, data }))
            .catch(error => sendResponse({ success: false, error: error.message }));
        return true;
    }

    // Reset Status
    if (request.action === 'resetStatus') {
        const url = request.prodCode
            ? `${API_BASE_URL}/api/reset-status?prod_code=${request.prodCode}`
            : `${API_BASE_URL}/api/reset-status`;
        fetch(url, { method: 'POST' })
            .then(response => response.json())
            .then(data => sendResponse({ success: true, data }))
            .catch(error => sendResponse({ success: false, error: error.message }));
        return true;
    }

    // Check Status
    if (request.action === 'checkStatus') {
        fetch(`${API_BASE_URL}/api/check-status`)
            .then(response => response.json())
            .then(data => sendResponse({ success: true, data }))
            .catch(error => sendResponse({ success: false, error: error.message }));
        return true;
    }
});
