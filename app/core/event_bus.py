"""
EventBus - MQTT-Style Pub/Sub Pattern for MediaVerse
Inspired by MQTT, provides topic-based message routing within the application.
"""

import re
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from queue import Queue
import logging

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """A message published to a topic."""
    topic: str
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None  # Who published this message


class EventBus:
    """
    MQTT-Style In-Process Event Bus (Singleton)
    
    Supports topic-based publish/subscribe with wildcards:
    - '#' matches any number of levels (e.g., 'log/#' matches 'log/info', 'log/error/critical')
    - '*' matches exactly one level (e.g., 'order/*' matches 'order/created' but not 'order/item/added')
    
    Example Topics:
    - media/imported
    - order/created
    - job/assigned
    - error/database
    - log/info
    """
    
    _instance: Optional['EventBus'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'EventBus':
        """Singleton pattern - ensure only one EventBus exists."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the EventBus (only once due to singleton)."""
        if self._initialized:
            return
            
        self._subscribers: Dict[str, List[Callable[[Message], None]]] = defaultdict(list)
        self._message_queue: Queue[Message] = Queue()
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        self._sub_lock = threading.Lock()
        self._history: List[Message] = []
        self._history_limit = 1000
        self._initialized = True
        
        logger.info("EventBus initialized")
    
    def subscribe(self, topic: str, callback: Callable[[Message], None]) -> None:
        """
        Subscribe to a topic pattern.
        
        Args:
            topic: Topic pattern (supports '#' and '*' wildcards)
            callback: Function to call when a matching message is published
        """
        with self._sub_lock:
            if callback not in self._subscribers[topic]:
                self._subscribers[topic].append(callback)
                logger.debug(f"Subscribed to '{topic}': {callback.__name__}")
    
    def unsubscribe(self, topic: str, callback: Callable[[Message], None]) -> None:
        """
        Unsubscribe from a topic pattern.
        
        Args:
            topic: Topic pattern to unsubscribe from
            callback: The callback to remove
        """
        with self._sub_lock:
            if topic in self._subscribers and callback in self._subscribers[topic]:
                self._subscribers[topic].remove(callback)
                logger.debug(f"Unsubscribed from '{topic}': {callback.__name__}")
    
    def publish(self, topic: str, payload: Dict[str, Any], source: Optional[str] = None) -> None:
        """
        Publish a message to a topic.
        
        Args:
            topic: The topic to publish to (no wildcards allowed)
            payload: The message payload
            source: Optional identifier of the publisher
        """
        if '#' in topic or '*' in topic:
            raise ValueError("Wildcards are not allowed in publish topic")
        
        message = Message(topic=topic, payload=payload, source=source)
        self._deliver_message(message)
    
    def publish_async(self, topic: str, payload: Dict[str, Any], source: Optional[str] = None) -> None:
        """
        Queue a message for asynchronous delivery.
        
        Args:
            topic: The topic to publish to
            payload: The message payload
            source: Optional identifier of the publisher
        """
        if '#' in topic or '*' in topic:
            raise ValueError("Wildcards are not allowed in publish topic")
        
        message = Message(topic=topic, payload=payload, source=source)
        self._message_queue.put(message)
    
    def _deliver_message(self, message: Message) -> None:
        """Deliver a message to all matching subscribers."""
        # Store in history
        self._history.append(message)
        if len(self._history) > self._history_limit:
            self._history = self._history[-self._history_limit:]
        
        # Find matching subscribers
        with self._sub_lock:
            for pattern, callbacks in self._subscribers.items():
                if self._topic_matches(pattern, message.topic):
                    for callback in callbacks:
                        try:
                            callback(message)
                        except Exception as e:
                            logger.error(f"Error in subscriber callback for '{pattern}': {e}")
    
    def _topic_matches(self, pattern: str, topic: str) -> bool:
        """
        Check if a topic matches a subscription pattern.
        
        Args:
            pattern: Subscription pattern (may contain wildcards)
            topic: Actual topic to match
            
        Returns:
            True if the topic matches the pattern
        """
        # Convert MQTT-style pattern to regex
        # '#' matches any number of levels
        # '*' matches exactly one level
        pattern_parts = pattern.split('/')
        topic_parts = topic.split('/')
        
        return self._match_parts(pattern_parts, topic_parts)
    
    def _match_parts(self, pattern_parts: List[str], topic_parts: List[str]) -> bool:
        """Recursively match pattern parts against topic parts."""
        if not pattern_parts:
            return not topic_parts
        
        if pattern_parts[0] == '#':
            # '#' matches everything remaining
            return True
        
        if not topic_parts:
            return False
        
        if pattern_parts[0] == '*':
            # '*' matches exactly one level
            return self._match_parts(pattern_parts[1:], topic_parts[1:])
        
        if pattern_parts[0] == topic_parts[0]:
            return self._match_parts(pattern_parts[1:], topic_parts[1:])
        
        return False
    
    def start_async_worker(self) -> None:
        """Start the background worker for async message delivery."""
        if self._running:
            return
        
        self._running = True
        self._worker_thread = threading.Thread(target=self._async_worker, daemon=True)
        self._worker_thread.start()
        logger.info("EventBus async worker started")
    
    def stop_async_worker(self) -> None:
        """Stop the background worker."""
        self._running = False
        if self._worker_thread:
            self._message_queue.put(None)  # Sentinel to wake up worker
            self._worker_thread.join(timeout=2.0)
            self._worker_thread = None
        logger.info("EventBus async worker stopped")
    
    def _async_worker(self) -> None:
        """Background worker for processing async messages."""
        while self._running:
            message = self._message_queue.get()
            if message is None:  # Sentinel for shutdown
                break
            self._deliver_message(message)
    
    def get_history(self, topic_filter: Optional[str] = None, limit: int = 100) -> List[Message]:
        """
        Get recent message history.
        
        Args:
            topic_filter: Optional topic pattern to filter by
            limit: Maximum number of messages to return
            
        Returns:
            List of recent messages
        """
        if topic_filter:
            filtered = [m for m in self._history if self._topic_matches(topic_filter, m.topic)]
            return filtered[-limit:]
        return self._history[-limit:]
    
    def clear_history(self) -> None:
        """Clear message history."""
        self._history.clear()
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (useful for testing)."""
        with cls._lock:
            if cls._instance:
                cls._instance.stop_async_worker()
            cls._instance = None


# Convenience function to get the singleton instance
def get_event_bus() -> EventBus:
    """Get the global EventBus instance."""
    return EventBus()
