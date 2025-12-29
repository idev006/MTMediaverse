"""
Message Envelope - LINE Messaging API Inspired Protocol
Defines the message structures for communication between FE.Stub (Bots) and BE.Stub (Backend)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import json
import uuid


class EventType(str, Enum):
    """Types of events that can be sent by bots."""
    REQUEST_JOB = "request_job"
    REPORT_JOB = "report_job"
    HEARTBEAT = "heartbeat"
    LOG = "log"


class MessageType(str, Enum):
    """Types of messages that can be sent by the system."""
    JOB_ASSIGNMENT = "job_assignment"
    TEXT = "text"
    ERROR = "error"
    ACK = "ack"


class JobStatus(str, Enum):
    """Status of a job."""
    NEW = "new"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


@dataclass
class Event:
    """
    An event sent by a bot to the system.
    Inspired by LINE Messaging API webhook events.
    """
    type: EventType
    reply_token: str
    timestamp: int  # Unix timestamp in milliseconds
    payload: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create an Event from a dictionary."""
        return cls(
            type=EventType(data.get('type', 'heartbeat')),
            reply_token=data.get('replyToken', ''),
            timestamp=data.get('timestamp', int(datetime.now().timestamp() * 1000)),
            payload=data.get('payload', {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'type': self.type.value,
            'replyToken': self.reply_token,
            'timestamp': self.timestamp,
            'payload': self.payload
        }


@dataclass
class MessageEnvelope:
    """
    Incoming message envelope from a bot.
    Contains client identification and a list of events.
    """
    client_code: str
    events: List[Event] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MessageEnvelope':
        """Create a MessageEnvelope from a dictionary."""
        events = [Event.from_dict(e) for e in data.get('events', [])]
        return cls(
            client_code=data.get('client_code', ''),
            events=events
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'MessageEnvelope':
        """Create a MessageEnvelope from a JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'client_code': self.client_code,
            'events': [e.to_dict() for e in self.events]
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)


@dataclass
class ResponseMessage:
    """A single message in the response."""
    type: MessageType
    payload: Dict[str, Any] = field(default_factory=dict)
    job_id: Optional[int] = None
    media_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            'type': self.type.value,
            'payload': self.payload
        }
        if self.job_id is not None:
            result['job_id'] = self.job_id
        if self.media_url is not None:
            result['media_url'] = self.media_url
        return result


@dataclass
class ResponseEnvelope:
    """
    Outgoing response envelope to a bot.
    Contains the reply token and a list of messages.
    """
    reply_token: str
    messages: List[ResponseMessage] = field(default_factory=list)
    
    @classmethod
    def create_job_assignment(
        cls,
        reply_token: str,
        job_id: int,
        media_url: str,
        title: str,
        description: str,
        tags: List[str],
        privacy: str = "public",
        **extra_payload
    ) -> 'ResponseEnvelope':
        """Create a job assignment response."""
        payload = {
            'title': title,
            'description': description,
            'tags': tags,
            'privacy': privacy,
            **extra_payload
        }
        message = ResponseMessage(
            type=MessageType.JOB_ASSIGNMENT,
            job_id=job_id,
            media_url=media_url,
            payload=payload
        )
        return cls(reply_token=reply_token, messages=[message])
    
    @classmethod
    def create_text(cls, reply_token: str, text: str) -> 'ResponseEnvelope':
        """Create a simple text response."""
        message = ResponseMessage(
            type=MessageType.TEXT,
            payload={'text': text}
        )
        return cls(reply_token=reply_token, messages=[message])
    
    @classmethod
    def create_error(cls, reply_token: str, error_code: str, error_message: str) -> 'ResponseEnvelope':
        """Create an error response."""
        message = ResponseMessage(
            type=MessageType.ERROR,
            payload={'code': error_code, 'message': error_message}
        )
        return cls(reply_token=reply_token, messages=[message])
    
    @classmethod
    def create_ack(cls, reply_token: str) -> 'ResponseEnvelope':
        """Create an acknowledgment response."""
        message = ResponseMessage(
            type=MessageType.ACK,
            payload={'status': 'received'}
        )
        return cls(reply_token=reply_token, messages=[message])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'replyToken': self.reply_token,
            'messages': [m.to_dict() for m in self.messages]
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)


def generate_reply_token() -> str:
    """Generate a unique reply token."""
    return f"rt_{uuid.uuid4().hex[:16]}"
