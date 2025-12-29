"""
ErrorOrchestrator - Centralized Error Handling for MediaVerse
Categorizes errors, provides recovery strategies, and notifies GUI.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import traceback

from .event_bus import get_event_bus
from .log_orchestrator import get_log_orchestrator


class ErrorSeverity(str, Enum):
    """Severity levels for errors."""
    LOW = "low"           # Non-critical, can be ignored
    MEDIUM = "medium"     # Should be addressed, but doesn't block operation
    HIGH = "high"         # Blocks current operation
    CRITICAL = "critical" # System-wide impact, requires immediate attention


class ErrorCategory(str, Enum):
    """Categories of errors for organization."""
    DATABASE = "database"
    NETWORK = "network"
    FILE_IO = "file_io"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    PLATFORM_API = "platform_api"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"


@dataclass
class ErrorRecord:
    """Record of an error occurrence."""
    id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    exception_type: str
    exception_message: str
    traceback: str
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolution_note: Optional[str] = None


class ErrorOrchestrator:
    """
    Centralized error handling and management.
    - Categorizes errors by type and severity
    - Provides recovery suggestions
    - Maintains error history
    - Publishes to EventBus for GUI notification
    """
    
    _instance: Optional['ErrorOrchestrator'] = None
    
    # EventBus topics
    TOPIC_ERROR = "error/occurred"
    TOPIC_ERROR_RESOLVED = "error/resolved"
    TOPIC_CRITICAL = "error/critical"
    
    def __new__(cls) -> 'ErrorOrchestrator':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._event_bus = get_event_bus()
        self._log = get_log_orchestrator()
        self._error_history: List[ErrorRecord] = []
        self._error_count = 0
        self._recovery_handlers: Dict[ErrorCategory, Callable] = {}
        self._initialized = True
    
    def handle_error(
        self,
        exception: Exception,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        notify_gui: bool = True
    ) -> ErrorRecord:
        """
        Handle an error with categorization and logging.
        
        Args:
            exception: The exception that occurred
            category: Category of the error
            severity: Severity level
            context: Additional context information
            notify_gui: Whether to publish to EventBus
            
        Returns:
            ErrorRecord for the handled error
        """
        self._error_count += 1
        error_id = f"ERR-{self._error_count:06d}"
        
        record = ErrorRecord(
            id=error_id,
            category=category,
            severity=severity,
            message=str(exception),
            exception_type=type(exception).__name__,
            exception_message=str(exception),
            traceback=traceback.format_exc(),
            context=context or {}
        )
        
        self._error_history.append(record)
        
        # Keep history limited
        if len(self._error_history) > 1000:
            self._error_history = self._error_history[-1000:]
        
        # Log the error
        if severity == ErrorSeverity.CRITICAL:
            self._log.critical(f"[{error_id}] {category.value}: {exception}", exception=exception)
        elif severity == ErrorSeverity.HIGH:
            self._log.error(f"[{error_id}] {category.value}: {exception}", exception=exception)
        else:
            self._log.warning(f"[{error_id}] {category.value}: {exception}")
        
        # Publish to EventBus
        if notify_gui:
            topic = self.TOPIC_CRITICAL if severity == ErrorSeverity.CRITICAL else self.TOPIC_ERROR
            self._event_bus.publish(topic, {
                'error_id': error_id,
                'category': category.value,
                'severity': severity.value,
                'message': str(exception),
                'timestamp': record.timestamp.isoformat(),
                'recovery_suggestion': self.get_recovery_suggestion(category)
            }, source='ErrorOrchestrator')
        
        return record
    
    def get_recovery_suggestion(self, category: ErrorCategory) -> str:
        """Get a recovery suggestion for an error category."""
        suggestions = {
            ErrorCategory.DATABASE: "Check database connection and file permissions.",
            ErrorCategory.NETWORK: "Check network connection and retry.",
            ErrorCategory.FILE_IO: "Verify file path exists and has correct permissions.",
            ErrorCategory.VALIDATION: "Check input data format and required fields.",
            ErrorCategory.AUTHENTICATION: "Verify credentials and refresh tokens.",
            ErrorCategory.PLATFORM_API: "Check API rate limits and credentials.",
            ErrorCategory.CONFIGURATION: "Review configuration file for missing/invalid values.",
            ErrorCategory.UNKNOWN: "Check logs for more details."
        }
        return suggestions.get(category, "Check logs for more details.")
    
    def register_recovery_handler(
        self, 
        category: ErrorCategory, 
        handler: Callable[[ErrorRecord], bool]
    ) -> None:
        """Register a recovery handler for an error category."""
        self._recovery_handlers[category] = handler
    
    def attempt_recovery(self, error_record: ErrorRecord) -> bool:
        """
        Attempt to recover from an error using registered handlers.
        
        Returns:
            True if recovery was successful
        """
        handler = self._recovery_handlers.get(error_record.category)
        if handler:
            try:
                success = handler(error_record)
                if success:
                    error_record.resolved = True
                    error_record.resolution_note = "Recovered automatically"
                    self._event_bus.publish(self.TOPIC_ERROR_RESOLVED, {
                        'error_id': error_record.id,
                        'category': error_record.category.value,
                        'resolution': 'auto_recovered'
                    }, source='ErrorOrchestrator')
                return success
            except Exception as e:
                self._log.error(f"Recovery handler failed: {e}", exception=e)
        return False
    
    def get_error_history(
        self, 
        category: Optional[ErrorCategory] = None,
        severity: Optional[ErrorSeverity] = None,
        unresolved_only: bool = False,
        limit: int = 100
    ) -> List[ErrorRecord]:
        """Get filtered error history."""
        result = self._error_history
        
        if category:
            result = [e for e in result if e.category == category]
        if severity:
            result = [e for e in result if e.severity == severity]
        if unresolved_only:
            result = [e for e in result if not e.resolved]
        
        return result[-limit:]
    
    def get_error_stats(self) -> Dict[str, int]:
        """Get error statistics by category."""
        stats: Dict[str, int] = {}
        for record in self._error_history:
            key = record.category.value
            stats[key] = stats.get(key, 0) + 1
        return stats
    
    def clear_history(self) -> None:
        """Clear error history."""
        self._error_history.clear()
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance."""
        cls._instance = None


def get_error_orchestrator() -> ErrorOrchestrator:
    """Get the global ErrorOrchestrator instance."""
    return ErrorOrchestrator()
