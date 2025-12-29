/**
 * StateManager - Central State Management
 * @memberof MTSuno
 */
(function (MTS) {
    'use strict';

    class StateManager {
        constructor() {
            this.state = {
                serverOnline: false,
                isProcessing: false,
                isPaused: false,
                songs: [],
                currentSongIndex: -1,
                logs: [],
                progress: {
                    total: 0,
                    completed: 0,
                    success: 0,
                    failed: 0,
                    stepLabel: 'Ready'
                }
            };
            this.subscribers = [];
        }

        subscribe(callback) {
            this.subscribers.push(callback);
            callback(this.state); // Initial call
        }

        notify() {
            this.subscribers.forEach(cb => cb(this.state));
        }

        // --- State Mutators ---
        setSongs(songs) {
            this.state.songs = songs;
            this.state.progress.total = songs.length;
            this.state.progress.completed = 0;
            this.state.progress.success = 0;
            this.state.progress.failed = 0;
            this.notify();
        }

        updateSongStatus(index, status, msg = '') {
            if (this.state.songs[index]) {
                this.state.songs[index].status = status;
                this.state.songs[index].msg = msg;
                this.notify();
            }
        }

        setCurrentSong(index) {
            this.state.currentSongIndex = index;
            this.notify();
        }

        incrementSuccess() {
            this.state.progress.success++;
            this.state.progress.completed++;
            this.notify();
        }

        incrementFailed() {
            this.state.progress.failed++;
            this.state.progress.completed++;
            this.notify();
        }

        setProcessing(val) {
            this.state.isProcessing = val;
            this.notify();
        }

        setPaused(val) {
            this.state.isPaused = val;
            this.notify();
        }

        setServerOnline(val) {
            this.state.serverOnline = val;
            this.notify();
        }

        setStepLabel(label) {
            this.state.progress.stepLabel = label;
            this.notify();
        }

        addLog(msg, type = 'info') {
            const timestamp = new Date().toLocaleTimeString();
            this.state.logs.push({ timestamp, message: msg, type });
            // Keep last 50 logs
            if (this.state.logs.length > 50) {
                this.state.logs.shift();
            }
            console.log(`[MTS][${type}]`, msg);
            this.notify();
        }
    }

    MTS.StateManager = StateManager;

})(window.MTSuno || (window.MTSuno = {}));
