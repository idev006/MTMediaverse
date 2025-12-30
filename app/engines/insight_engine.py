"""
InsightEngine - AI/ML Data Collection and Analysis

Features:
- Collect ALL events, logs, metrics ผ่านจุดเดียว
- Store patterns and anomalies
- Provide context for AI diagnosis
- Export data for ML training
- Suggest fixes based on historical patterns

แนวคิด: ทุกอย่างผ่านจุดนี้ เพื่อเป็นข้อมูลให้ AI วิเคราะห์

Pattern: Observer, Repository
"""

import json
import threading
import time
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.engines.base_engine import BaseEngine
from app.core.event_bus import get_event_bus
from app.core.log_orchestrator import get_log_orchestrator


class EventType(Enum):
    """Types of events for AI analysis."""
    JOB_CREATED = "job_created"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    ERROR = "error"
    WARNING = "warning"
    METRIC = "metric"
    USER_ACTION = "user_action"
    SYSTEM_STATE = "system_state"
    ANOMALY = "anomaly"


class Severity(Enum):
    """Event severity levels."""
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4


@dataclass
class InsightEvent:
    """
    Single event for AI analysis.
    
    Contains all context needed for pattern recognition
    and root cause analysis.
    """
    event_id: str
    event_type: EventType
    severity: Severity
    timestamp: datetime
    source: str
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)  # Related state
    tags: List[str] = field(default_factory=list)
    correlation_id: Optional[str] = None  # Link related events
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'severity': self.severity.value,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'message': self.message,
            'data': self.data,
            'context': self.context,
            'tags': self.tags,
            'correlation_id': self.correlation_id,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


@dataclass
class DiagnosticContext:
    """
    Context for AI diagnosis.
    
    Contains recent history and patterns for analysis.
    """
    recent_events: List[InsightEvent]
    recent_errors: List[InsightEvent]
    metrics_snapshot: Dict[str, float]
    patterns_detected: List[str]
    suggested_actions: List[str]


@dataclass
class Pattern:
    """Detected pattern for ML training."""
    pattern_id: str
    pattern_type: str
    description: str
    conditions: Dict[str, Any]
    occurrence_count: int = 0
    last_seen: datetime = field(default_factory=datetime.now)
    resolution: Optional[str] = None  # If pattern was resolved


class InsightEngine(BaseEngine):
    """
    Central point for AI/ML data collection and analysis.
    
    ALL system events flow through here to:
    1. Build training data for ML
    2. Detect patterns and anomalies
    3. Provide diagnostic context
    4. Suggest fixes based on history
    """
    
    # Event topics this engine listens to
    LISTEN_TOPICS = [
        "queue/job/*",
        "process/*", 
        "monitor/*",
        "order/*",
        "product/*",
        "error/*",
    ]
    
    # Export topics
    TOPIC_INSIGHT = "insight/event"
    TOPIC_ANOMALY = "insight/anomaly"
    TOPIC_SUGGESTION = "insight/suggestion"
    
    def __init__(self, max_history: int = 10000):
        super().__init__("InsightEngine")
        
        self._event_bus = get_event_bus()
        
        # Event storage (rolling window)
        self._events: deque = deque(maxlen=max_history)
        self._errors: deque = deque(maxlen=1000)
        
        # Pattern storage
        self._patterns: Dict[str, Pattern] = {}
        
        # Event counter for ID generation
        self._event_counter = 0
        self._lock = threading.Lock()
        
        # Anomaly detection thresholds
        self._thresholds = {
            'error_rate': 0.1,  # 10% error rate
            'job_duration_ms': 30000,  # 30 seconds
            'queue_size': 100,
        }
        
        # AI/ML callback (for external AI integration)
        self._ai_callback: Optional[Callable[[DiagnosticContext], List[str]]] = None
        
        # Data export path
        self._export_path = Path("logs/insight_data")
    
    # ========================================================================
    # Template Method Implementation
    # ========================================================================
    
    def _do_start(self):
        """Subscribe to all relevant events."""
        self._subscribe_to_events()
        self._export_path.mkdir(parents=True, exist_ok=True)
    
    def _do_stop(self):
        """Export remaining data."""
        self._export_to_file()
    
    # ========================================================================
    # Event Collection
    # ========================================================================
    
    def _subscribe_to_events(self):
        """Subscribe to all system events."""
        # Subscribe to EventBus
        self._event_bus.subscribe("*", self._on_event)
        self.log_info("Subscribed to all EventBus events")
    
    def _on_event(self, topic: str, data: Dict[str, Any], source: str):
        """Handle incoming event from any source."""
        event = self._create_insight_event(topic, data, source)
        self._store_event(event)
        
        # Check for anomalies
        self._check_anomalies(event)
        
        # Update patterns
        self._update_patterns(event)
    
    def _create_insight_event(
        self, 
        topic: str, 
        data: Dict[str, Any], 
        source: str
    ) -> InsightEvent:
        """Create InsightEvent from raw event."""
        with self._lock:
            self._event_counter += 1
            event_id = f"INS-{self._event_counter:08d}"
        
        # Determine event type
        event_type = self._classify_event_type(topic)
        severity = self._classify_severity(topic, data)
        
        return InsightEvent(
            event_id=event_id,
            event_type=event_type,
            severity=severity,
            timestamp=datetime.now(),
            source=source,
            message=self._extract_message(topic, data),
            data=data,
            context=self._capture_context(),
            tags=self._extract_tags(topic, data),
            correlation_id=data.get('job_id') or data.get('order_id'),
        )
    
    def _classify_event_type(self, topic: str) -> EventType:
        """Classify event type from topic."""
        if 'error' in topic or 'failed' in topic:
            return EventType.ERROR
        elif 'completed' in topic or 'success' in topic:
            return EventType.JOB_COMPLETED
        elif 'created' in topic or 'enqueued' in topic:
            return EventType.JOB_CREATED
        elif 'metric' in topic:
            return EventType.METRIC
        elif 'warning' in topic:
            return EventType.WARNING
        else:
            return EventType.SYSTEM_STATE
    
    def _classify_severity(self, topic: str, data: Dict) -> Severity:
        """Classify severity from topic and data."""
        if 'critical' in topic or 'dead' in topic:
            return Severity.CRITICAL
        elif 'error' in topic or 'failed' in topic:
            return Severity.ERROR
        elif 'warning' in topic:
            return Severity.WARNING
        else:
            return Severity.INFO
    
    def _extract_message(self, topic: str, data: Dict) -> str:
        """Extract human-readable message."""
        if 'message' in data:
            return data['message']
        elif 'error' in data:
            return f"Error: {data['error']}"
        else:
            return f"Event: {topic}"
    
    def _extract_tags(self, topic: str, data: Dict) -> List[str]:
        """Extract searchable tags."""
        tags = topic.split('/')
        if 'job_type' in data:
            tags.append(data['job_type'])
        if 'platform' in data:
            tags.append(data['platform'])
        return tags
    
    def _capture_context(self) -> Dict[str, Any]:
        """Capture current system context."""
        try:
            from app.core.queue_orchestrator import get_queue_orchestrator
            queue = get_queue_orchestrator()
            return {
                'queue_size': queue.get_queue_size(),
                'queue_stats': queue.get_stats(),
            }
        except:
            return {}
    
    def _store_event(self, event: InsightEvent):
        """Store event for analysis."""
        self._events.append(event)
        
        if event.severity.value >= Severity.ERROR.value:
            self._errors.append(event)
        
        # Publish for real-time listeners
        self.publish_event(self.TOPIC_INSIGHT, event.to_dict())
    
    # ========================================================================
    # Anomaly Detection
    # ========================================================================
    
    def _check_anomalies(self, event: InsightEvent):
        """Check for anomalies based on thresholds."""
        anomalies = []
        
        # Check error rate
        if len(self._events) > 100:
            recent = list(self._events)[-100:]
            error_count = sum(1 for e in recent if e.severity.value >= Severity.ERROR.value)
            error_rate = error_count / 100
            
            if error_rate > self._thresholds['error_rate']:
                anomalies.append({
                    'type': 'high_error_rate',
                    'value': error_rate,
                    'threshold': self._thresholds['error_rate'],
                })
        
        # Check queue size
        if event.context.get('queue_size', 0) > self._thresholds['queue_size']:
            anomalies.append({
                'type': 'queue_overflow',
                'value': event.context['queue_size'],
                'threshold': self._thresholds['queue_size'],
            })
        
        # Publish anomalies
        for anomaly in anomalies:
            self.publish_event(self.TOPIC_ANOMALY, {
                'anomaly': anomaly,
                'event': event.to_dict(),
            })
            self._trigger_ai_analysis(anomaly, event)
    
    # ========================================================================
    # Pattern Detection & Learning
    # ========================================================================
    
    def _update_patterns(self, event: InsightEvent):
        """Update pattern detection based on event."""
        # Create pattern key from event characteristics
        pattern_key = f"{event.event_type.value}:{event.source}"
        
        if event.severity.value >= Severity.ERROR.value:
            pattern_key = f"error:{event.source}:{event.tags[0] if event.tags else 'unknown'}"
        
        if pattern_key in self._patterns:
            pattern = self._patterns[pattern_key]
            pattern.occurrence_count += 1
            pattern.last_seen = datetime.now()
        else:
            self._patterns[pattern_key] = Pattern(
                pattern_id=pattern_key,
                pattern_type=event.event_type.value,
                description=event.message,
                conditions={'source': event.source, 'tags': event.tags},
                occurrence_count=1,
            )
    
    # ========================================================================
    # AI Integration
    # ========================================================================
    
    def set_ai_callback(self, callback: Callable[[DiagnosticContext], List[str]]):
        """
        Set AI callback for intelligent analysis.
        
        The callback receives DiagnosticContext and returns
        list of suggested actions.
        """
        self._ai_callback = callback
        self.log_info("AI callback registered")
    
    def _trigger_ai_analysis(self, anomaly: Dict, event: InsightEvent):
        """Trigger AI analysis for anomaly."""
        if self._ai_callback is None:
            return
        
        context = self.get_diagnostic_context()
        suggestions = self._ai_callback(context)
        
        if suggestions:
            self.publish_event(self.TOPIC_SUGGESTION, {
                'anomaly': anomaly,
                'suggestions': suggestions,
            })
    
    def get_diagnostic_context(self) -> DiagnosticContext:
        """Get full context for AI diagnosis."""
        recent_events = list(self._events)[-100:]
        recent_errors = list(self._errors)[-20:]
        
        # Get metrics
        metrics = {}
        for event in recent_events:
            if event.event_type == EventType.METRIC:
                for key, val in event.data.items():
                    if isinstance(val, (int, float)):
                        metrics[key] = val
        
        # Detect patterns
        patterns = [p.pattern_id for p in self._patterns.values() 
                   if p.occurrence_count > 5]
        
        return DiagnosticContext(
            recent_events=recent_events,
            recent_errors=recent_errors,
            metrics_snapshot=metrics,
            patterns_detected=patterns,
            suggested_actions=self._generate_basic_suggestions(recent_errors),
        )
    
    def _generate_basic_suggestions(self, errors: List[InsightEvent]) -> List[str]:
        """Generate basic suggestions from error patterns."""
        suggestions = []
        
        # Group errors by source
        error_sources = {}
        for err in errors:
            source = err.source
            if source not in error_sources:
                error_sources[source] = 0
            error_sources[source] += 1
        
        # Suggest based on patterns
        for source, count in error_sources.items():
            if count >= 3:
                suggestions.append(
                    f"Multiple errors from {source} ({count}x) - consider investigating"
                )
        
        return suggestions
    
    # ========================================================================
    # Query & Export
    # ========================================================================
    
    def get_events(
        self, 
        event_type: Optional[EventType] = None,
        severity: Optional[Severity] = None,
        source: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Query events with filters."""
        events = list(self._events)
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if severity:
            events = [e for e in events if e.severity.value >= severity.value]
        if source:
            events = [e for e in events if source in e.source]
        
        return [e.to_dict() for e in events[-limit:]]
    
    def get_patterns(self) -> List[Dict]:
        """Get detected patterns."""
        return [asdict(p) for p in self._patterns.values()]
    
    def export_for_training(self, filepath: str = None) -> str:
        """Export events as JSON for ML training."""
        filepath = filepath or str(
            self._export_path / f"training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        data = {
            'events': [e.to_dict() for e in self._events],
            'patterns': self.get_patterns(),
            'exported_at': datetime.now().isoformat(),
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        self.log_info(f"Exported {len(self._events)} events to {filepath}")
        return filepath
    
    def _export_to_file(self):
        """Export data on shutdown."""
        if len(self._events) > 0:
            self.export_for_training()


# Singleton instance
_insight_engine: Optional[InsightEngine] = None


def get_insight_engine(max_history: int = 10000) -> InsightEngine:
    """Get global InsightEngine instance."""
    global _insight_engine
    if _insight_engine is None:
        _insight_engine = InsightEngine(max_history)
    return _insight_engine
