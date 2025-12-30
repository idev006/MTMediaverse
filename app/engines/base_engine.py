"""
BaseEngine - Abstract base class for engines

Design Pattern: Template Method
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

from app.core.event_bus import get_event_bus
from app.core.log_orchestrator import get_log_orchestrator


class BaseEngine(ABC):
    """
    Abstract base class for all engines.
    
    Pattern: Template Method
    - define skeleton of algorithm
    - subclasses override specific steps
    """
    
    def __init__(self, name: str):
        self._name = name
        self._event_bus = get_event_bus()
        self._log = get_log_orchestrator()
        self._running = False
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def is_running(self) -> bool:
        return self._running
    
    # ========================================================================
    # Template Method Pattern
    # ========================================================================
    
    def start(self):
        """Start the engine (Template Method)."""
        if self._running:
            self._log.warning(f"{self._name} already running")
            return
        
        self._log.info(f"Starting {self._name}...")
        
        # Hook: before start
        self._before_start()
        
        # Core start logic
        self._do_start()
        
        self._running = True
        
        # Hook: after start
        self._after_start()
        
        self._log.info(f"{self._name} started")
    
    def stop(self):
        """Stop the engine (Template Method)."""
        if not self._running:
            return
        
        self._log.info(f"Stopping {self._name}...")
        
        # Hook: before stop
        self._before_stop()
        
        # Core stop logic
        self._do_stop()
        
        self._running = False
        
        # Hook: after stop
        self._after_stop()
        
        self._log.info(f"{self._name} stopped")
    
    # ========================================================================
    # Abstract Methods (must implement)
    # ========================================================================
    
    @abstractmethod
    def _do_start(self):
        """Core start logic - must implement."""
        pass
    
    @abstractmethod
    def _do_stop(self):
        """Core stop logic - must implement."""
        pass
    
    # ========================================================================
    # Hooks (optional override)
    # ========================================================================
    
    def _before_start(self):
        """Hook: called before start."""
        pass
    
    def _after_start(self):
        """Hook: called after start."""
        pass
    
    def _before_stop(self):
        """Hook: called before stop."""
        pass
    
    def _after_stop(self):
        """Hook: called after stop."""
        pass
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def publish_event(self, topic: str, data: Any):
        """Publish event via EventBus."""
        self._event_bus.publish(topic, data, source=self._name)
    
    def log_info(self, message: str):
        """Log info message."""
        self._log.info(f"[{self._name}] {message}")
    
    def log_error(self, message: str):
        """Log error message."""
        self._log.error(f"[{self._name}] {message}")
