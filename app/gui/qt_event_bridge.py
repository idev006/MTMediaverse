"""
Qt-EventBus Bridge - เชื่อม EventBus กับ Qt Signals
ทำให้ GUI รับ events real-time ได้
"""

from PySide6.QtCore import QObject, Signal, QThread
from typing import Any, Dict, Callable
import threading

from app.core.event_bus import get_event_bus, Message


class QtEventBridge(QObject):
    """
    Bridge ระหว่าง EventBus และ Qt Signals
    
    EventBus (background thread) → Qt Signal → GUI (main thread)
    """
    
    # Qt Signals for different event types
    order_created = Signal(dict)
    order_updated = Signal(dict)
    item_completed = Signal(dict)
    item_failed = Signal(dict)
    client_online = Signal(dict)
    client_offline = Signal(dict)
    log_message = Signal(dict)
    error_occurred = Signal(dict)
    generic_event = Signal(str, dict)  # topic, payload
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._event_bus = get_event_bus()
        self._subscriptions = []
        self._setup_subscriptions()
    
    def _setup_subscriptions(self):
        """Subscribe to all relevant EventBus topics."""
        
        # Order events
        self._subscribe("order/created", self._on_order_created)
        self._subscribe("order/updated", self._on_order_updated)
        self._subscribe("order/item_completed", self._on_item_completed)
        self._subscribe("order/item_failed", self._on_item_failed)
        
        # Client events
        self._subscribe("client/online", self._on_client_online)
        self._subscribe("client/offline", self._on_client_offline)
        
        # Log events
        self._subscribe("log/#", self._on_log_message)
        
        # Error events
        self._subscribe("error/#", self._on_error_occurred)
        
        # Generic catch-all
        self._subscribe("#", self._on_generic_event)
    
    def _subscribe(self, topic: str, handler: Callable):
        """Subscribe to an EventBus topic."""
        self._event_bus.subscribe(topic, handler)
        self._subscriptions.append((topic, handler))
    
    def _on_order_created(self, msg: Message):
        self.order_created.emit(msg.payload)
    
    def _on_order_updated(self, msg: Message):
        self.order_updated.emit(msg.payload)
    
    def _on_item_completed(self, msg: Message):
        self.item_completed.emit(msg.payload)
    
    def _on_item_failed(self, msg: Message):
        self.item_failed.emit(msg.payload)
    
    def _on_client_online(self, msg: Message):
        self.client_online.emit(msg.payload)
    
    def _on_client_offline(self, msg: Message):
        self.client_offline.emit(msg.payload)
    
    def _on_log_message(self, msg: Message):
        self.log_message.emit(msg.payload)
    
    def _on_error_occurred(self, msg: Message):
        self.error_occurred.emit(msg.payload)
    
    def _on_generic_event(self, msg: Message):
        self.generic_event.emit(msg.topic, msg.payload)
    
    def cleanup(self):
        """Unsubscribe from all topics."""
        for topic, handler in self._subscriptions:
            self._event_bus.unsubscribe(topic, handler)
        self._subscriptions.clear()


# Global bridge instance
_bridge_instance = None


def get_qt_event_bridge() -> QtEventBridge:
    """Get or create the global QtEventBridge instance."""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = QtEventBridge()
    return _bridge_instance
