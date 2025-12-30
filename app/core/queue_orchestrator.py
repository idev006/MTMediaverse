"""
QueueOrchestrator - จัดการ Job Queue พร้อม Priority

Features:
- Priority-based queue (high, normal, low)
- Job lifecycle management
- Retry logic with backoff
- Dead letter queue for failed jobs

แนวคิด: MQTT + LINE Messaging Queue
"""

import time
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from queue import PriorityQueue
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from app.core.event_bus import get_event_bus
from app.core.log_orchestrator import get_log_orchestrator


class JobPriority(Enum):
    """Job priority levels."""
    HIGH = 1
    NORMAL = 5
    LOW = 10


class JobStatus(Enum):
    """Job status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD = "dead"


@dataclass(order=True)
class Job:
    """
    Job representation in queue.
    
    Comparable by priority for PriorityQueue.
    """
    priority: int
    created_at: float = field(compare=False)
    job_id: str = field(compare=False, default_factory=lambda: str(uuid4())[:8])
    job_type: str = field(compare=False, default="default")
    payload: Dict[str, Any] = field(compare=False, default_factory=dict)
    status: JobStatus = field(compare=False, default=JobStatus.PENDING)
    attempt_count: int = field(compare=False, default=0)
    max_attempts: int = field(compare=False, default=3)
    error_message: str = field(compare=False, default="")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'job_id': self.job_id,
            'job_type': self.job_type,
            'priority': self.priority,
            'status': self.status.value,
            'attempt_count': self.attempt_count,
            'payload': self.payload,
            'error': self.error_message,
        }


class QueueOrchestrator:
    """
    Central job queue manager.
    
    Patterns:
    - Singleton
    - Strategy (different queue policies)
    - Observer (job status changes)
    """
    
    _instance = None
    _lock = threading.Lock()
    
    # Event topics
    TOPIC_JOB_ENQUEUED = "queue/job/enqueued"
    TOPIC_JOB_STARTED = "queue/job/started"
    TOPIC_JOB_COMPLETED = "queue/job/completed"
    TOPIC_JOB_FAILED = "queue/job/failed"
    TOPIC_JOB_DEAD = "queue/job/dead"
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._event_bus = get_event_bus()
        self._log = get_log_orchestrator()
        
        # Main queue (priority-based)
        self._queue: PriorityQueue[Job] = PriorityQueue()
        
        # Job tracking
        self._jobs: Dict[str, Job] = {}
        
        # Dead letter queue
        self._dead_letter: List[Job] = []
        
        # Job handlers by type
        self._handlers: Dict[str, Callable] = {}
        
        # Stats
        self._stats = {
            'enqueued': 0,
            'completed': 0,
            'failed': 0,
            'dead': 0,
        }
        
        self._initialized = True
        self._log.info("QueueOrchestrator initialized")
    
    # ========================================================================
    # Queue Operations
    # ========================================================================
    
    def enqueue(
        self,
        job_type: str,
        payload: Dict[str, Any],
        priority: JobPriority = JobPriority.NORMAL,
        max_attempts: int = 3
    ) -> Job:
        """
        Add job to queue.
        
        Args:
            job_type: Type of job (used to find handler)
            payload: Job data
            priority: Job priority
            max_attempts: Max retry attempts
            
        Returns:
            Created Job
        """
        job = Job(
            priority=priority.value,
            created_at=time.time(),
            job_type=job_type,
            payload=payload,
            max_attempts=max_attempts,
        )
        
        self._queue.put(job)
        self._jobs[job.job_id] = job
        self._stats['enqueued'] += 1
        
        self._event_bus.publish(self.TOPIC_JOB_ENQUEUED, job.to_dict(), source='QueueOrchestrator')
        self._log.debug(f"Job enqueued: {job.job_id} ({job_type})")
        
        return job
    
    def dequeue(self, timeout: float = 1.0) -> Optional[Job]:
        """
        Get next job from queue.
        
        Args:
            timeout: Wait timeout in seconds
            
        Returns:
            Next Job or None if queue empty
        """
        try:
            job = self._queue.get(timeout=timeout)
            job.status = JobStatus.PROCESSING
            job.attempt_count += 1
            
            self._event_bus.publish(self.TOPIC_JOB_STARTED, job.to_dict(), source='QueueOrchestrator')
            
            return job
        except:
            return None
    
    def complete(self, job_id: str, result: Any = None):
        """Mark job as completed."""
        if job_id not in self._jobs:
            return
        
        job = self._jobs[job_id]
        job.status = JobStatus.COMPLETED
        self._stats['completed'] += 1
        
        self._event_bus.publish(self.TOPIC_JOB_COMPLETED, {
            **job.to_dict(),
            'result': result
        }, source='QueueOrchestrator')
        
        self._log.info(f"Job completed: {job_id}")
    
    def fail(self, job_id: str, error: str):
        """
        Mark job as failed.
        
        If attempts remain, re-enqueue with backoff.
        Otherwise, move to dead letter queue.
        """
        if job_id not in self._jobs:
            return
        
        job = self._jobs[job_id]
        job.error_message = error
        
        if job.attempt_count < job.max_attempts:
            # Re-enqueue with exponential backoff
            job.status = JobStatus.PENDING
            backoff = 2 ** job.attempt_count
            
            self._log.warning(f"Job {job_id} failed (attempt {job.attempt_count}), retry in {backoff}s: {error}")
            
            # Schedule retry (simplified - immediate re-queue)
            self._queue.put(job)
            
        else:
            # Move to dead letter queue
            job.status = JobStatus.DEAD
            self._dead_letter.append(job)
            self._stats['dead'] += 1
            
            self._event_bus.publish(self.TOPIC_JOB_DEAD, job.to_dict(), source='QueueOrchestrator')
            self._log.error(f"Job {job_id} moved to dead letter queue: {error}")
        
        self._stats['failed'] += 1
    
    # ========================================================================
    # Handler Registration
    # ========================================================================
    
    def register_handler(self, job_type: str, handler: Callable[[Job], Any]):
        """
        Register handler for job type.
        
        Args:
            job_type: Job type string
            handler: Function that processes the job
        """
        self._handlers[job_type] = handler
        self._log.debug(f"Handler registered for: {job_type}")
    
    def get_handler(self, job_type: str) -> Optional[Callable]:
        """Get handler for job type."""
        return self._handlers.get(job_type)
    
    # ========================================================================
    # Status & Stats
    # ========================================================================
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        return self._jobs.get(job_id)
    
    def get_queue_size(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        return {
            **self._stats,
            'queue_size': self._queue.qsize(),
            'dead_letter_size': len(self._dead_letter),
            'registered_handlers': list(self._handlers.keys()),
        }
    
    def get_dead_letter_jobs(self) -> List[Dict]:
        """Get all dead letter jobs."""
        return [job.to_dict() for job in self._dead_letter]
    
    def clear_dead_letter(self):
        """Clear dead letter queue."""
        count = len(self._dead_letter)
        self._dead_letter.clear()
        self._log.info(f"Cleared {count} dead letter jobs")
    
    # ========================================================================
    # Singleton Reset (for testing)
    # ========================================================================
    
    @classmethod
    def reset_instance(cls):
        """Reset singleton instance (for testing)."""
        cls._instance = None


# Singleton getter
_queue_orchestrator: Optional[QueueOrchestrator] = None


def get_queue_orchestrator() -> QueueOrchestrator:
    """Get global QueueOrchestrator instance."""
    global _queue_orchestrator
    if _queue_orchestrator is None:
        _queue_orchestrator = QueueOrchestrator()
    return _queue_orchestrator
