/**
 * Stub1_Api - Server Communication Stub
 * Handles all HTTP communication with backend server
 * 
 * @memberof YouTubeUploader.Stubs
 */
(function (YTU) {
    'use strict';

    class Stub1_Api {
        constructor(baseUrl = 'http://127.0.0.1:8000') {
            this.baseUrl = baseUrl;
            this.clientCode = '';
        }

        setClientCode(code) {
            this.clientCode = code;
        }

        /**
         * Generic fetch wrapper with error handling
         */
        async _fetch(endpoint, options = {}) {
            try {
                const headers = {
                    'Content-Type': 'application/json',
                    ...options.headers
                };

                if (this.clientCode) {
                    headers['X-Client-Code'] = this.clientCode;
                }

                const response = await fetch(`${this.baseUrl}${endpoint}`, {
                    ...options,
                    headers
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                return await response.json();
            } catch (error) {
                console.error(`[Stub1_Api] Error: ${endpoint}`, error);
                throw error;
            }
        }

        /**
         * Health check - verify server connection
         */
        async healthCheck() {
            try {
                const data = await this._fetch('/health');
                return {
                    success: true,
                    status: data.status,
                    videoCount: data.video_count,
                    stats: data.stats
                };
            } catch (error) {
                return { success: false, error: error.message };
            }
        }

        /**
         * Fetch pending products
         */
        async fetchProducts(includeSuccess = false) {
            try {
                const query = includeSuccess ? '?include_success=true' : '';
                const data = await this._fetch(`/api/products${query}`);
                return {
                    success: true,
                    products: data.prod_list || [],
                    total: data.total || 0
                };
            } catch (error) {
                return { success: false, error: error.message, products: [] };
            }
        }

        /**
         * Fetch video file for a product
         */
        async fetchVideo(prodCode) {
            try {
                const data = await this._fetch('/api/get-video', {
                    method: 'POST',
                    body: JSON.stringify({ prod_code: prodCode })
                });

                if (!data.success || !data.payload) {
                    throw new Error('Invalid video response');
                }

                // Convert base64 to File
                const base64 = data.payload;
                const byteCharacters = atob(base64);
                const byteNumbers = new Array(byteCharacters.length);

                for (let i = 0; i < byteCharacters.length; i++) {
                    byteNumbers[i] = byteCharacters.charCodeAt(i);
                }

                const byteArray = new Uint8Array(byteNumbers);
                const blob = new Blob([byteArray], { type: 'video/mp4' });
                const file = new File([blob], data.filename || `${prodCode}.mp4`, { type: 'video/mp4' });

                return {
                    success: true,
                    file,
                    filename: data.filename,
                    sizeMb: data.size_mb,
                    product: data.product || {}
                };
            } catch (error) {
                return { success: false, error: error.message };
            }
        }

        /**
         * Report upload result
         */
        async reportUpload(prodCode, status, errorMessage = '') {
            try {
                const data = await this._fetch('/api/report-upload', {
                    method: 'POST',
                    body: JSON.stringify({
                        prod_code: prodCode,
                        status,
                        error_message: errorMessage,
                        uploaded_at: new Date().toISOString()
                    })
                });

                return {
                    success: true,
                    shouldStop: data.should_stop || false,
                    shouldPause: data.should_pause || false,
                    reason: data.reason || ''
                };
            } catch (error) {
                return { success: false, error: error.message };
            }
        }

        /**
         * Check control signals from BE
         */
        async checkStatus() {
            try {
                const data = await this._fetch('/api/check-status');
                return {
                    shouldStop: data.should_stop || false,
                    shouldPause: data.should_pause || false,
                    reason: data.reason || ''
                };
            } catch (error) {
                return { shouldStop: false, shouldPause: false };
            }
        }

        /**
         * Clear stop signal
         */
        async clearStop() {
            try {
                await this._fetch('/api/clear-stop', { method: 'POST' });
                return { success: true };
            } catch (error) {
                return { success: false, error: error.message };
            }
        }

        /**
         * Reset product status
         */
        async resetStatus(prodCode = null) {
            try {
                const query = prodCode ? `?prod_code=${prodCode}` : '';
                await this._fetch(`/api/reset-status${query}`, { method: 'POST' });
                return { success: true };
            } catch (error) {
                return { success: false, error: error.message };
            }
        }

        /**
         * Start a new session
         */
        async startSession() {
            try {
                const data = await this._fetch('/api/sessions/start', { method: 'POST' });
                return { success: true, session: data.data };
            } catch (error) {
                return { success: false, error: error.message };
            }
        }
    }

    // Register with namespace
    YTU.Stub1_Api = Stub1_Api;

})(window.YouTubeUploader || (window.YouTubeUploader = {}));
