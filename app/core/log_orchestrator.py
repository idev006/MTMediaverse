"""
LogOrchestrator - Centralized Logging System for MediaVerse
Publishes logs to EventBus for GUI integration.
"""

import logging
import os
from datetime import datetime
from typing import Optional
from pathlib import Path

from .event_bus import EventBus, get_event_bus


class LogOrchestrator:
    """
    Centralized logging orchestrator.
    - Logs to file and console
    - Publishes to EventBus for GUI Monitor integration
    """
    
    _instance: Optional['LogOrchestrator'] = None
    
    # Log topics for EventBus
    TOPIC_DEBUG = "log/debug"
    TOPIC_INFO = "log/info"
    TOPIC_WARNING = "log/warning"
    TOPIC_ERROR = "log/error"
    TOPIC_CRITICAL = "log/critical"
    
    def __new__(cls) -> 'LogOrchestrator':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._event_bus = get_event_bus()
        self._setup_logging()
        self._initialized = True
    
    def _setup_logging(self) -> None:
        """Setup Python logging with file and console handlers."""
        # Create logs directory
        app_dir = Path(__file__).parent.parent
        log_dir = app_dir / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # Create logger
        self._logger = logging.getLogger('MediaVerse')
        self._logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        self._logger.handlers.clear()
        
        # File handler
        log_file = log_dir / f"mediaverse_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        
        self._logger.addHandler(file_handler)
        self._logger.addHandler(console_handler)
    
    def _publish_log(self, level: str, message: str, topic: str, **extra) -> None:
        """Publish log to EventBus for GUI."""
        self._event_bus.publish(topic, {
            'level': level,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            **extra
        }, source='LogOrchestrator')
    
    def debug(self, message: str, **extra) -> None:
        """Log debug message."""
        self._logger.debug(message)
        self._publish_log('DEBUG', message, self.TOPIC_DEBUG, **extra)
    
    def info(self, message: str, **extra) -> None:
        """Log info message."""
        self._logger.info(message)
        self._publish_log('INFO', message, self.TOPIC_INFO, **extra)
    
    def warning(self, message: str, **extra) -> None:
        """Log warning message."""
        self._logger.warning(message)
        self._publish_log('WARNING', message, self.TOPIC_WARNING, **extra)
    
    def error(self, message: str, exception: Optional[Exception] = None, **extra) -> None:
        """Log error message."""
        if exception:
            self._logger.error(f"{message}: {exception}", exc_info=True)
            extra['exception'] = str(exception)
        else:
            self._logger.error(message)
        self._publish_log('ERROR', message, self.TOPIC_ERROR, **extra)
    
    def critical(self, message: str, exception: Optional[Exception] = None, **extra) -> None:
        """Log critical message."""
        if exception:
            self._logger.critical(f"{message}: {exception}", exc_info=True)
            extra['exception'] = str(exception)
        else:
            self._logger.critical(message)
        self._publish_log('CRITICAL', message, self.TOPIC_CRITICAL, **extra)
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance."""
        cls._instance = None


def get_log_orchestrator() -> LogOrchestrator:
    """Get the global LogOrchestrator instance."""
    return LogOrchestrator()
