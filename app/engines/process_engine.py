"""
ProcessEngine - Job Processing Engine

Features:
- Worker thread pool
- Process jobs from QueueOrchestrator
- Execute registered handlers
- Handle errors and retries

Pattern: Template Method, Strategy
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Any, Callable, Dict, List, Optional

from app.engines.base_engine import BaseEngine
from app.core.queue_orchestrator import (
    get_queue_orchestrator, QueueOrchestrator, Job, JobStatus
)
from app.core.event_bus import get_event_bus


class ProcessEngine(BaseEngine):
    """
    Job processing engine.
    
    Pulls jobs from QueueOrchestrator and executes them
    using registered handlers.
    """
    
    # Event topics
    TOPIC_ENGINE_STARTED = "process/engine/started"
    TOPIC_ENGINE_STOPPED = "process/engine/stopped"
    TOPIC_JOB_PROCESSING = "process/job/processing"
    TOPIC_JOB_SUCCESS = "process/job/success"
    TOPIC_JOB_ERROR = "process/job/error"
    
    def __init__(self, worker_count: int = 4):
        super().__init__("ProcessEngine")
        
        self._worker_count = worker_count
        self._queue_orc = get_queue_orchestrator()
        
        # Thread pool
        self._executor: Optional[ThreadPoolExecutor] = None
        
        # Processing control
        self._should_run = False
        self._processing_thread: Optional[threading.Thread] = None
        
        # Stats
        self._stats = {
            'processed': 0,
            'success': 0,
            'errors': 0,
        }
        
        # Active jobs
        self._active_jobs: Dict[str, Future] = {}
    
    # ========================================================================
    # Template Method Implementation
    # ========================================================================
    
    def _do_start(self):
        """Start worker pool and processing loop."""
        self._should_run = True
        
        # Create thread pool
        self._executor = ThreadPoolExecutor(
            max_workers=self._worker_count,
            thread_name_prefix="ProcessWorker"
        )
        
        # Start processing loop
        self._processing_thread = threading.Thread(
            target=self._processing_loop,
            daemon=True,
            name="ProcessEngine-Loop"
        )
        self._processing_thread.start()
    
    def _do_stop(self):
        """Stop workers and processing loop."""
        self._should_run = False
        
        # Wait for processing thread
        if self._processing_thread and self._processing_thread.is_alive():
            self._processing_thread.join(timeout=5.0)
        
        # Shutdown executor
        if self._executor:
            self._executor.shutdown(wait=True, cancel_futures=True)
            self._executor = None
    
    def _after_start(self):
        """Publish engine started event."""
        self.publish_event(self.TOPIC_ENGINE_STARTED, {
            'worker_count': self._worker_count
        })
    
    def _after_stop(self):
        """Publish engine stopped event."""
        self.publish_event(self.TOPIC_ENGINE_STOPPED, self._stats)
    
    # ========================================================================
    # Processing Loop
    # ========================================================================
    
    def _processing_loop(self):
        """Main loop - pull jobs and execute."""
        self.log_info(f"Processing loop started with {self._worker_count} workers")
        
        while self._should_run:
            try:
                # Get next job from queue
                job = self._queue_orc.dequeue(timeout=1.0)
                
                if job is None:
                    continue
                
                # Submit to thread pool
                future = self._executor.submit(self._execute_job, job)
                self._active_jobs[job.job_id] = future
                
                # Cleanup completed futures
                self._cleanup_completed()
                
            except Exception as e:
                self.log_error(f"Processing loop error: {e}")
                time.sleep(1.0)
        
        self.log_info("Processing loop stopped")
    
    def _execute_job(self, job: Job):
        """Execute a single job."""
        self._stats['processed'] += 1
        
        self.publish_event(self.TOPIC_JOB_PROCESSING, {
            'job_id': job.job_id,
            'job_type': job.job_type,
            'attempt': job.attempt_count,
        })
        
        try:
            # Get handler
            handler = self._queue_orc.get_handler(job.job_type)
            
            if handler is None:
                raise ValueError(f"No handler for job type: {job.job_type}")
            
            # Execute handler
            result = handler(job)
            
            # Mark completed
            self._queue_orc.complete(job.job_id, result)
            self._stats['success'] += 1
            
            self.publish_event(self.TOPIC_JOB_SUCCESS, {
                'job_id': job.job_id,
                'result': str(result)[:100] if result else None,
            })
            
        except Exception as e:
            # Mark failed
            self._queue_orc.fail(job.job_id, str(e))
            self._stats['errors'] += 1
            
            self.publish_event(self.TOPIC_JOB_ERROR, {
                'job_id': job.job_id,
                'error': str(e),
            })
            
            self.log_error(f"Job {job.job_id} failed: {e}")
    
    def _cleanup_completed(self):
        """Remove completed futures from tracking."""
        completed = [
            job_id for job_id, future in self._active_jobs.items()
            if future.done()
        ]
        for job_id in completed:
            del self._active_jobs[job_id]
    
    # ========================================================================
    # Stats & Status
    # ========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return {
            **self._stats,
            'active_jobs': len(self._active_jobs),
            'worker_count': self._worker_count,
            'is_running': self._running,
        }
    
    def get_active_job_ids(self) -> List[str]:
        """Get list of currently processing job IDs."""
        return list(self._active_jobs.keys())


# Singleton instance
_process_engine: Optional[ProcessEngine] = None


def get_process_engine(worker_count: int = 4) -> ProcessEngine:
    """Get global ProcessEngine instance."""
    global _process_engine
    if _process_engine is None:
        _process_engine = ProcessEngine(worker_count)
    return _process_engine
