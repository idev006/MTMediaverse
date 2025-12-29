/**
 * Styles - Inject CSS for the panel
 * @memberof MTSuno
 */
(function (MTS) {
    'use strict';

    const CSS = `
        #mt-suno-root {
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 13px;
            color: #e0e0e0;
        }
        .mts-panel {
            position: fixed;
            top: 60px;
            right: 20px;
            width: 400px;
            max-height: 80vh;
            background: linear-gradient(145deg, #1e1e2e, #2a2a3e);
            border: 1px solid #3a3a5a;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
            z-index: 10000;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .mts-header {
            padding: 12px 16px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .mts-header-title {
            font-weight: 600;
            font-size: 15px;
            color: #fff;
        }
        .mts-header-status {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #888;
        }
        .mts-header-status.online { background: #4ade80; box-shadow: 0 0 8px #4ade80; }
        .mts-header-status.offline { background: #f87171; }
        .mts-body {
            padding: 12px;
            overflow-y: auto;
            flex: 1;
        }
        .mts-section {
            margin-bottom: 12px;
        }
        .mts-label {
            font-size: 11px;
            color: #888;
            margin-bottom: 4px;
            text-transform: uppercase;
        }
        .mts-file-input {
            width: 100%;
            padding: 8px;
            background: #2a2a3e;
            border: 1px solid #444;
            border-radius: 6px;
            color: #fff;
            font-size: 12px;
        }
        .mts-input-small {
            width: 55px;
            padding: 4px 6px;
            background: #2a2a3e;
            border: 1px solid #444;
            border-radius: 4px;
            color: #fff;
            font-size: 11px;
            text-align: center;
        }
        .mts-input-small:focus {
            border-color: #667eea;
            outline: none;
        }
        .mts-btn {
            padding: 10px 16px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            font-size: 13px;
            transition: all 0.2s;
            width: 100%;
        }
        .mts-btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
        }
        .mts-btn-primary:hover { opacity: 0.9; transform: translateY(-1px); }
        .mts-btn-primary:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        .mts-btn-secondary {
            background: #3a3a5a;
            color: #ccc;
        }
        .mts-stats {
            display: flex;
            gap: 8px;
            margin-bottom: 10px;
        }
        .mts-stat {
            flex: 1;
            padding: 8px;
            background: #2a2a3e;
            border-radius: 6px;
            text-align: center;
        }
        .mts-stat-value {
            font-size: 18px;
            font-weight: bold;
        }
        .mts-stat-label {
            font-size: 10px;
            color: #888;
        }
        .mts-stat.success .mts-stat-value { color: #4ade80; }
        .mts-stat.error .mts-stat-value { color: #f87171; }
        .mts-table-wrap {
            max-height: 200px;
            overflow-y: auto;
            border: 1px solid #333;
            border-radius: 6px;
        }
        .mts-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
        }
        .mts-table th {
            background: #2a2a3e;
            padding: 8px;
            text-align: left;
            position: sticky;
            top: 0;
            z-index: 1;
        }
        .mts-table td {
            padding: 8px;
            border-bottom: 1px solid #333;
        }
        .mts-table tr.active {
            background: rgba(102, 126, 234, 0.2);
        }
        .mts-badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 10px;
            font-weight: 600;
        }
        .mts-badge.pending { background: #444; color: #aaa; }
        .mts-badge.processing { background: #3b82f6; color: #fff; }
        .mts-badge.generating { background: #f59e0b; color: #fff; }
        .mts-badge.completed { background: #22c55e; color: #fff; }
        .mts-badge.error { background: #ef4444; color: #fff; }
        .mts-log-wrap {
            background: #1a1a2e;
            border-radius: 6px;
            padding: 8px;
            max-height: 100px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 11px;
            margin-top: 8px;
        }
        .mts-log-entry {
            border-bottom: 1px solid #2a2a3e;
            padding: 2px 0;
        }
        .mts-log-entry.error { color: #f87171; }
        .mts-log-entry.success { color: #4ade80; }
        .mts-log-entry.warning { color: #fbbf24; }
        .mts-collapse-btn {
            background: transparent;
            border: none;
            color: #fff;
            cursor: pointer;
            font-size: 18px;
            padding: 4px 8px;
        }
        /* Modal Overlay */
        .mts-modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0, 0, 0, 0.7);
            z-index: 10001;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .mts-modal {
            background: linear-gradient(145deg, #1e1e2e, #2a2a3e);
            border: 1px solid #3a3a5a;
            border-radius: 12px;
            width: 500px;
            max-height: 80vh;
            display: flex;
            flex-direction: column;
            box-shadow: 0 12px 48px rgba(0,0,0,0.5);
        }
        .mts-modal-header {
            padding: 16px;
            border-bottom: 1px solid #3a3a5a;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .mts-modal-header h3 {
            margin: 0;
            font-size: 16px;
            color: #fff;
        }
        .mts-modal-close {
            background: transparent;
            border: none;
            color: #888;
            font-size: 24px;
            cursor: pointer;
        }
        .mts-modal-close:hover { color: #fff; }
        .mts-modal-body {
            padding: 16px;
            overflow-y: auto;
            flex: 1;
        }
        .mts-modal-footer {
            padding: 12px 16px;
            border-top: 1px solid #3a3a5a;
            display: flex;
            gap: 8px;
            justify-content: flex-end;
        }
        .mts-modal-footer .mts-btn {
            width: auto;
            padding: 8px 16px;
        }
        .mts-dl-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
            margin-bottom: 12px;
        }
        .mts-dl-table th {
            background: #2a2a3e;
            padding: 10px 8px;
            text-align: left;
            color: #aaa;
            font-weight: 600;
        }
        .mts-dl-table td {
            padding: 10px 8px;
            border-bottom: 1px solid #333;
        }
        .mts-dl-table tr:hover { background: rgba(102, 126, 234, 0.1); }
        .mts-dl-table .song-thumb {
            width: 40px;
            height: 40px;
            border-radius: 4px;
            object-fit: cover;
        }
        .mts-dl-table .song-title {
            font-weight: 500;
            color: #fff;
        }
        .mts-dl-table .song-tags {
            font-size: 10px;
            color: #888;
            max-width: 200px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .mts-summary-text {
            text-align: center;
            padding: 12px;
            color: #4ade80;
            font-size: 14px;
        }
        .mts-btn-download {
            background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
            color: #fff;
        }
        .mts-btn-download:hover { opacity: 0.9; }
    `;

    MTS.injectStyles = function () {
        if (document.getElementById('mts-styles')) return;
        const style = document.createElement('style');
        style.id = 'mts-styles';
        style.textContent = CSS;
        document.head.appendChild(style);
    };

})(window.MTSuno || (window.MTSuno = {}));
