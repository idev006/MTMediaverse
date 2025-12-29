"""
MessageOrchestrator - Central Hub for MediaVerse
Routes messages between FE.Stub (Bots) and internal components.
Acts as the brain of the system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
import threading

from .event_bus import EventBus, get_event_bus
from .message_envelope import (
    MessageEnvelope, Event, EventType,
    ResponseEnvelope, ResponseMessage, MessageType
)
from .log_orchestrator import get_log_orchestrator
from .error_orchestrator import get_error_orchestrator, ErrorCategory, ErrorSeverity


@dataclass
class ClientStatus:
    """Status information for a connected client."""
    client_code: str
    platform: str
    last_seen: datetime
    is_online: bool = True
    current_job_id: Optional[int] = None
    jobs_completed: int = 0
    jobs_failed: int = 0


class MessageOrchestrator:
    """
    Central Message Hub (Singleton)
    
    Responsibilities:
    - Route incoming webhook messages to appropriate handlers
    - Coordinate with ViewModels (MediaVM, OrderVM)
    - Maintain client connection states
    - Publish events to EventBus for GUI updates
    """
    
    _instance: Optional['MessageOrchestrator'] = None
    _lock = threading.Lock()
    
    # EventBus topics
    TOPIC_CLIENT_CONNECTED = "client/connected"
    TOPIC_CLIENT_DISCONNECTED = "client/disconnected"
    TOPIC_JOB_REQUESTED = "job/requested"
    TOPIC_JOB_ASSIGNED = "job/assigned"
    TOPIC_JOB_COMPLETED = "job/completed"
    TOPIC_JOB_FAILED = "job/failed"
    TOPIC_HEARTBEAT = "client/heartbeat"
    
    def __new__(cls) -> 'MessageOrchestrator':
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
        self._error = get_error_orchestrator()
        
        # Client tracking
        self._clients: Dict[str, ClientStatus] = {}
        self._clients_lock = threading.Lock()
        
        # Event handlers
        self._event_handlers: Dict[EventType, Callable[[str, Event], ResponseEnvelope]] = {
            EventType.REQUEST_JOB: self._handle_request_job,
            EventType.REPORT_JOB: self._handle_report_job,
            EventType.HEARTBEAT: self._handle_heartbeat,
            EventType.LOG: self._handle_log,
        }
        
        # ViewModel references (to be set externally)
        self._media_vm = None
        self._order_vm = None
        
        self._initialized = True
        self._log.info("MessageOrchestrator initialized")
    
    def set_media_vm(self, media_vm) -> None:
        """Set the MediaVM reference."""
        self._media_vm = media_vm
        self._log.debug("MediaVM connected to MessageOrchestrator")
    
    def set_order_vm(self, order_vm) -> None:
        """Set the OrderVM reference."""
        self._order_vm = order_vm
        self._log.debug("OrderVM connected to MessageOrchestrator")
    
    def process_envelope(self, envelope: MessageEnvelope) -> List[ResponseEnvelope]:
        """
        Process an incoming message envelope from a bot.
        
        Args:
            envelope: The incoming message envelope
            
        Returns:
            List of response envelopes for each event
        """
        responses: List[ResponseEnvelope] = []
        client_code = envelope.client_code
        
        self._log.debug(f"Processing envelope from {client_code} with {len(envelope.events)} events")
        
        # Update client last seen
        self._update_client_status(client_code)
        
        for event in envelope.events:
            try:
                handler = self._event_handlers.get(event.type)
                if handler:
                    response = handler(client_code, event)
                    responses.append(response)
                else:
                    self._log.warning(f"No handler for event type: {event.type}")
                    responses.append(ResponseEnvelope.create_error(
                        event.reply_token,
                        "UNKNOWN_EVENT",
                        f"Unknown event type: {event.type}"
                    ))
            except Exception as e:
                self._error.handle_error(
                    e,
                    category=ErrorCategory.UNKNOWN,
                    severity=ErrorSeverity.MEDIUM,
                    context={'client_code': client_code, 'event_type': event.type.value}
                )
                responses.append(ResponseEnvelope.create_error(
                    event.reply_token,
                    "PROCESSING_ERROR",
                    str(e)
                ))
        
        return responses
    
    def _update_client_status(self, client_code: str, platform: str = "unknown") -> None:
        """Update or create client status."""
        with self._clients_lock:
            if client_code not in self._clients:
                self._clients[client_code] = ClientStatus(
                    client_code=client_code,
                    platform=platform,
                    last_seen=datetime.now()
                )
                self._event_bus.publish(self.TOPIC_CLIENT_CONNECTED, {
                    'client_code': client_code,
                    'platform': platform
                }, source='MessageOrchestrator')
                self._log.info(f"New client connected: {client_code}")
            else:
                self._clients[client_code].last_seen = datetime.now()
                self._clients[client_code].is_online = True
    
    def _handle_request_job(self, client_code: str, event: Event) -> ResponseEnvelope:
        """Handle job request from a bot."""
        self._log.info(f"Job request from {client_code}")
        
        # Publish to EventBus
        self._event_bus.publish(self.TOPIC_JOB_REQUESTED, {
            'client_code': client_code,
            'payload': event.payload
        }, source='MessageOrchestrator')
        
        # Try to get next job from OrderVM
        if self._order_vm:
            job = self._order_vm.get_next_job(client_code)
            if job:
                # Update client status
                with self._clients_lock:
                    if client_code in self._clients:
                        self._clients[client_code].current_job_id = job['job_id']
                
                # Publish job assigned event
                self._event_bus.publish(self.TOPIC_JOB_ASSIGNED, {
                    'client_code': client_code,
                    'job_id': job['job_id'],
                    'media_id': job.get('media_id')
                }, source='MessageOrchestrator')
                
                self._log.info(f"Job {job['job_id']} assigned to {client_code}")
                
                return ResponseEnvelope.create_job_assignment(
                    reply_token=event.reply_token,
                    job_id=job['job_id'],
                    media_url=job['media_url'],
                    title=job['payload'].get('title', ''),
                    description=job['payload'].get('description', ''),
                    tags=job['payload'].get('tags', []),
                    privacy=job['payload'].get('privacy', 'public')
                )
        
        # No job available
        self._log.debug(f"No jobs available for {client_code}")
        return ResponseEnvelope.create_text(event.reply_token, "Standby - no jobs available")
    
    def _handle_report_job(self, client_code: str, event: Event) -> ResponseEnvelope:
        """Handle job completion report from a bot."""
        job_id = event.payload.get('job_id')
        status = event.payload.get('status', 'done')
        log_message = event.payload.get('log', '')
        
        self._log.info(f"Job report from {client_code}: Job {job_id} = {status}")
        
        # Update client status
        with self._clients_lock:
            if client_code in self._clients:
                self._clients[client_code].current_job_id = None
                if status == 'done':
                    self._clients[client_code].jobs_completed += 1
                else:
                    self._clients[client_code].jobs_failed += 1
        
        # Publish to EventBus
        topic = self.TOPIC_JOB_COMPLETED if status == 'done' else self.TOPIC_JOB_FAILED
        self._event_bus.publish(topic, {
            'client_code': client_code,
            'job_id': job_id,
            'status': status,
            'log': log_message
        }, source='MessageOrchestrator')
        
        # Update OrderVM
        if self._order_vm:
            self._order_vm.report_job(job_id, status, log_message)
        
        return ResponseEnvelope.create_ack(event.reply_token)
    
    def _handle_heartbeat(self, client_code: str, event: Event) -> ResponseEnvelope:
        """Handle heartbeat ping from a bot."""
        self._log.debug(f"Heartbeat from {client_code}")
        
        self._event_bus.publish(self.TOPIC_HEARTBEAT, {
            'client_code': client_code,
            'timestamp': datetime.now().isoformat()
        }, source='MessageOrchestrator')
        
        return ResponseEnvelope.create_ack(event.reply_token)
    
    def _handle_log(self, client_code: str, event: Event) -> ResponseEnvelope:
        """Handle log message from a bot."""
        level = event.payload.get('level', 'info')
        message = event.payload.get('message', '')
        
        self._log.info(f"[{client_code}] {level.upper()}: {message}")
        
        return ResponseEnvelope.create_ack(event.reply_token)
    
    def get_client_statuses(self) -> Dict[str, ClientStatus]:
        """Get all client statuses."""
        with self._clients_lock:
            return dict(self._clients)
    
    def get_online_clients(self) -> List[str]:
        """Get list of online client codes."""
        with self._clients_lock:
            return [code for code, status in self._clients.items() if status.is_online]
    
    def mark_client_offline(self, client_code: str) -> None:
        """Mark a client as offline."""
        with self._clients_lock:
            if client_code in self._clients:
                self._clients[client_code].is_online = False
                self._event_bus.publish(self.TOPIC_CLIENT_DISCONNECTED, {
                    'client_code': client_code
                }, source='MessageOrchestrator')
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance."""
        with cls._lock:
            cls._instance = None


def get_message_orchestrator() -> MessageOrchestrator:
    """Get the global MessageOrchestrator instance."""
    return MessageOrchestrator()
