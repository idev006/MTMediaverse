"""
MonitorEngine - System Monitoring Engine

Features:
- Collect metrics from all components
- Health check endpoints
- Alert on anomalies
- Dashboard data provider

Pattern: Observer, Singleton
"""

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from app.engines.base_engine import BaseEngine
from app.core.event_bus import get_event_bus
from app.core.queue_orchestrator import get_queue_orchestrator
from app.core.log_orchestrator import get_log_orchestrator


@dataclass
class MetricPoint:
    """Single metric data point."""
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class HealthStatus:
    """Component health status."""
    component: str
    healthy: bool
    message: str = ""
    last_check: datetime = field(default_factory=datetime.now)


class MonitorEngine(BaseEngine):
    """
    System monitoring engine.
    
    Collects metrics, performs health checks,
    and provides data for dashboards.
    """
    
    # Event topics
    TOPIC_METRICS_UPDATED = "monitor/metrics/updated"
    TOPIC_HEALTH_CHANGED = "monitor/health/changed"
    TOPIC_ALERT = "monitor/alert"
    
    def __init__(self, check_interval: float = 5.0):
        super().__init__("MonitorEngine")
        
        self._check_interval = check_interval
        self._queue_orc = get_queue_orchestrator()
        
        # Monitoring thread
        self._monitor_thread: Optional[threading.Thread] = None
        self._should_run = False
        
        # Metrics storage (rolling window)
        self._metrics: Dict[str, List[MetricPoint]] = {}
        self._max_history = 100  # Keep last 100 points
        
        # Health checks registry
        self._health_checks: Dict[str, Callable[[], HealthStatus]] = {}
        self._health_status: Dict[str, HealthStatus] = {}
        
        # Alert handlers
        self._alert_handlers: List[Callable[[str, Dict], None]] = []
        
        # Register default health checks
        self._register_default_checks()
    
    # ========================================================================
    # Template Method Implementation
    # ========================================================================
    
    def _do_start(self):
        """Start monitoring loop."""
        self._should_run = True
        
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="MonitorEngine-Loop"
        )
        self._monitor_thread.start()
    
    def _do_stop(self):
        """Stop monitoring loop."""
        self._should_run = False
        
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5.0)
    
    # ========================================================================
    # Monitoring Loop
    # ========================================================================
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        self.log_info(f"Monitoring started (interval: {self._check_interval}s)")
        
        while self._should_run:
            try:
                # Collect metrics
                self._collect_metrics()
                
                # Run health checks
                self._run_health_checks()
                
                # Publish update event
                self.publish_event(self.TOPIC_METRICS_UPDATED, {
                    'timestamp': datetime.now().isoformat(),
                    'summary': self.get_metrics_summary(),
                })
                
            except Exception as e:
                self.log_error(f"Monitor loop error: {e}")
            
            time.sleep(self._check_interval)
        
        self.log_info("Monitoring stopped")
    
    def _collect_metrics(self):
        """Collect metrics from all sources."""
        now = datetime.now()
        
        # Queue metrics
        queue_stats = self._queue_orc.get_stats()
        self._record_metric("queue.size", queue_stats['queue_size'])
        self._record_metric("queue.enqueued", queue_stats['enqueued'])
        self._record_metric("queue.completed", queue_stats['completed'])
        self._record_metric("queue.failed", queue_stats['failed'])
        self._record_metric("queue.dead", queue_stats['dead'])
        
        # Import ProcessEngine stats if available
        try:
            from app.engines.process_engine import get_process_engine
            pe = get_process_engine()
            pe_stats = pe.get_stats()
            self._record_metric("process.active", pe_stats['active_jobs'])
            self._record_metric("process.success", pe_stats['success'])
            self._record_metric("process.errors", pe_stats['errors'])
        except:
            pass
    
    def _record_metric(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a metric point."""
        point = MetricPoint(name=name, value=value, tags=tags or {})
        
        if name not in self._metrics:
            self._metrics[name] = []
        
        self._metrics[name].append(point)
        
        # Trim to max history
        if len(self._metrics[name]) > self._max_history:
            self._metrics[name] = self._metrics[name][-self._max_history:]
    
    # ========================================================================
    # Health Checks
    # ========================================================================
    
    def _register_default_checks(self):
        """Register default health checks."""
        
        def check_queue() -> HealthStatus:
            stats = self._queue_orc.get_stats()
            dead = stats['dead']
            healthy = dead < 10  # Alert if too many dead jobs
            return HealthStatus(
                component="QueueOrchestrator",
                healthy=healthy,
                message=f"Dead jobs: {dead}" if not healthy else "OK"
            )
        
        self.register_health_check("queue", check_queue)
    
    def register_health_check(self, name: str, check_fn: Callable[[], HealthStatus]):
        """Register a health check function."""
        self._health_checks[name] = check_fn
        self.log_info(f"Health check registered: {name}")
    
    def _run_health_checks(self):
        """Run all registered health checks."""
        for name, check_fn in self._health_checks.items():
            try:
                status = check_fn()
                
                # Check for status change
                old_status = self._health_status.get(name)
                if old_status and old_status.healthy != status.healthy:
                    self.publish_event(self.TOPIC_HEALTH_CHANGED, {
                        'component': status.component,
                        'healthy': status.healthy,
                        'message': status.message,
                    })
                    
                    # Trigger alert if unhealthy
                    if not status.healthy:
                        self._trigger_alert("health_degraded", {
                            'component': status.component,
                            'message': status.message,
                        })
                
                self._health_status[name] = status
                
            except Exception as e:
                self._health_status[name] = HealthStatus(
                    component=name,
                    healthy=False,
                    message=f"Check failed: {e}"
                )
    
    # ========================================================================
    # Alerts
    # ========================================================================
    
    def add_alert_handler(self, handler: Callable[[str, Dict], None]):
        """Add alert handler callback."""
        self._alert_handlers.append(handler)
    
    def _trigger_alert(self, alert_type: str, data: Dict[str, Any]):
        """Trigger an alert."""
        self.log_error(f"ALERT [{alert_type}]: {data}")
        
        self.publish_event(self.TOPIC_ALERT, {
            'type': alert_type,
            'data': data,
            'timestamp': datetime.now().isoformat(),
        })
        
        # Call handlers
        for handler in self._alert_handlers:
            try:
                handler(alert_type, data)
            except Exception as e:
                self.log_error(f"Alert handler error: {e}")
    
    # ========================================================================
    # Query Methods
    # ========================================================================
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of current metrics."""
        summary = {}
        for name, points in self._metrics.items():
            if points:
                latest = points[-1]
                summary[name] = {
                    'current': latest.value,
                    'timestamp': latest.timestamp.isoformat(),
                }
        return summary
    
    def get_metric_history(self, name: str, limit: int = 50) -> List[Dict]:
        """Get historical values for a metric."""
        if name not in self._metrics:
            return []
        
        points = self._metrics[name][-limit:]
        return [
            {'value': p.value, 'timestamp': p.timestamp.isoformat()}
            for p in points
        ]
    
    def get_health_status(self) -> Dict[str, Dict]:
        """Get current health status of all components."""
        return {
            name: {
                'component': status.component,
                'healthy': status.healthy,
                'message': status.message,
                'last_check': status.last_check.isoformat(),
            }
            for name, status in self._health_status.items()
        }
    
    def is_system_healthy(self) -> bool:
        """Check if entire system is healthy."""
        if not self._health_status:
            return True
        return all(s.healthy for s in self._health_status.values())


# Singleton instance
_monitor_engine: Optional[MonitorEngine] = None


def get_monitor_engine(check_interval: float = 5.0) -> MonitorEngine:
    """Get global MonitorEngine instance."""
    global _monitor_engine
    if _monitor_engine is None:
        _monitor_engine = MonitorEngine(check_interval)
    return _monitor_engine
