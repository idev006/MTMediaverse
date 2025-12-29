"""
FastAPI Application for MediaVerse Backend
Provides the webhook endpoint for bot communication.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import os

from app.core.database import init_database, get_db
from app.core.event_bus import get_event_bus
from app.core.message_orchestrator import get_message_orchestrator
from app.core.message_envelope import MessageEnvelope, ResponseEnvelope
from app.core.log_orchestrator import get_log_orchestrator
from app.core.error_orchestrator import get_error_orchestrator, ErrorCategory, ErrorSeverity


# ============================================================================
# Pydantic Models for API
# ============================================================================

class EventModel(BaseModel):
    """Incoming event from a bot."""
    type: str
    replyToken: str
    timestamp: int
    payload: Dict[str, Any] = {}


class WebhookRequest(BaseModel):
    """Incoming webhook request from a bot."""
    client_code: str
    events: List[EventModel]


class MessageModel(BaseModel):
    """Outgoing message to a bot."""
    type: str
    payload: Dict[str, Any] = {}
    job_id: Optional[int] = None
    media_url: Optional[str] = None


class WebhookResponse(BaseModel):
    """Outgoing webhook response to a bot."""
    replyToken: str
    messages: List[MessageModel]


# ============================================================================
# Application Lifecycle
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    # Startup
    log = get_log_orchestrator()
    log.info("MediaVerse Backend starting...")
    
    # Initialize database
    init_database()
    log.info("Database initialized")
    
    # Start EventBus async worker
    event_bus = get_event_bus()
    event_bus.start_async_worker()
    log.info("EventBus async worker started")
    
    log.info("MediaVerse Backend ready!")
    
    yield
    
    # Shutdown
    log.info("MediaVerse Backend shutting down...")
    event_bus.stop_async_worker()
    log.info("MediaVerse Backend stopped")


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="MediaVerse API",
    description="Central Media Hub for multi-platform video distribution",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "MediaVerse",
        "version": "1.0.0"
    }


@app.post("/api/webhook", response_model=List[WebhookResponse])
async def webhook(request: WebhookRequest):
    """
    Main webhook endpoint for bot communication.
    
    Receives events from bots and returns appropriate responses.
    Follows LINE Messaging API style message envelope pattern.
    """
    log = get_log_orchestrator()
    error_orch = get_error_orchestrator()
    orchestrator = get_message_orchestrator()
    
    try:
        # Convert Pydantic model to MessageEnvelope
        envelope_data = {
            'client_code': request.client_code,
            'events': [
                {
                    'type': event.type,
                    'replyToken': event.replyToken,
                    'timestamp': event.timestamp,
                    'payload': event.payload
                }
                for event in request.events
            ]
        }
        envelope = MessageEnvelope.from_dict(envelope_data)
        
        # Process through MessageOrchestrator
        responses = orchestrator.process_envelope(envelope)
        
        # Convert ResponseEnvelopes to Pydantic models
        result = []
        for resp in responses:
            resp_dict = resp.to_dict()
            result.append(WebhookResponse(
                replyToken=resp_dict['replyToken'],
                messages=[
                    MessageModel(**msg) for msg in resp_dict['messages']
                ]
            ))
        
        return result
        
    except Exception as e:
        error_orch.handle_error(
            e,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            context={'client_code': request.client_code}
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/video/{file_hash}")
async def get_video(file_hash: str):
    """
    Serve a video file by its hash.
    
    Args:
        file_hash: SHA256 hash of the video file
    """
    log = get_log_orchestrator()
    db = get_db()
    
    from app.core.database import MediaAsset
    
    session = db.get_session()
    try:
        asset = session.query(MediaAsset).filter(MediaAsset.file_hash == file_hash).first()
        
        if not asset:
            raise HTTPException(status_code=404, detail="Video not found")
        
        if not os.path.exists(asset.file_path):
            raise HTTPException(status_code=404, detail="Video file not found on disk")
        
        log.debug(f"Serving video: {asset.filename}")
        return FileResponse(
            asset.file_path,
            media_type=asset.mime_type or "video/mp4",
            filename=asset.filename
        )
    finally:
        session.close()


@app.get("/api/clients")
async def get_clients():
    """Get list of connected clients and their status."""
    orchestrator = get_message_orchestrator()
    clients = orchestrator.get_client_statuses()
    
    return {
        'clients': [
            {
                'client_code': status.client_code,
                'platform': status.platform,
                'is_online': status.is_online,
                'last_seen': status.last_seen.isoformat() if status.last_seen else None,
                'current_job_id': status.current_job_id,
                'jobs_completed': status.jobs_completed,
                'jobs_failed': status.jobs_failed
            }
            for status in clients.values()
        ]
    }


@app.get("/api/stats")
async def get_stats():
    """Get system statistics."""
    db = get_db()
    error_orch = get_error_orchestrator()
    orchestrator = get_message_orchestrator()
    
    from app.core.database import MediaAsset, Order, ClientAccount
    
    session = db.get_session()
    try:
        return {
            'media_count': session.query(MediaAsset).count(),
            'order_count': session.query(Order).count(),
            'client_count': session.query(ClientAccount).count(),
            'online_clients': len(orchestrator.get_online_clients()),
            'error_stats': error_orch.get_error_stats()
        }
    finally:
        session.close()


# ============================================================================
# Bot API Endpoints (UC-B01 to UC-B05)
# ============================================================================

class CreateOrderRequest(BaseModel):
    """Request to create a new order."""
    client_code: str
    quantity: int = 10
    prod_code: Optional[str] = None  # Optional - filter by product


class CreateOrderResponse(BaseModel):
    """Response with created order details."""
    order_id: int
    platform: str
    item_count: int
    items: List[Dict[str, Any]]


class ConfirmJobResponse(BaseModel):
    """Response for job confirmation."""
    job_id: int
    can_post: bool
    reason: Optional[str] = None


class ReportJobRequest(BaseModel):
    """Request to report job completion."""
    job_id: int
    status: str  # 'done' or 'failed'
    external_id: Optional[str] = None  # Platform's video/post ID
    external_url: Optional[str] = None  # URL to the posted content
    log_message: Optional[str] = None


class HeartbeatRequest(BaseModel):
    """Heartbeat request."""
    client_code: str


@app.post("/api/bot/create-order", response_model=CreateOrderResponse)
async def create_order(request: CreateOrderRequest):
    """
    UC-B01: Bot สร้าง Order
    
    Bot ขอสร้าง Order พร้อมระบุจำนวน clips ที่ต้องการ
    BE จะ:
    - ดึง platform จาก client account
    - Random select clips (ไม่ซ้ำ)
    - Shuffle props (anti-detection)
    - ส่งกลับรายการ items พร้อม payload
    """
    log = get_log_orchestrator()
    db = get_db()
    
    from app.core.database import ClientAccount
    from app.viewmodels.order_builder import get_order_builder
    
    session = db.get_session()
    try:
        # Get client to find platform
        client = session.query(ClientAccount).filter(
            ClientAccount.client_code == request.client_code
        ).first()
        
        if not client:
            raise HTTPException(status_code=404, detail=f"Client not found: {request.client_code}")
        
        # Create order using OrderBuilder
        builder = get_order_builder()
        order = builder.create_order(
            client_code=request.client_code,
            platform=client.platform,
            quantity=request.quantity,
            prod_code=request.prod_code
        )
        
        if not order:
            raise HTTPException(status_code=404, detail="No available clips for this platform")
        
        log.info(f"Order {order.order_id} created for {request.client_code}: {len(order.items)} items")
        
        return CreateOrderResponse(
            order_id=order.order_id,
            platform=order.platform,
            item_count=len(order.items),
            items=[item.to_dict() for item in order.items]
        )
        
    finally:
        session.close()


@app.get("/api/bot/video/{file_hash}")
async def get_video_base64(file_hash: str):
    """
    UC-B02: Bot ขอ Video เป็น Base64
    
    Bot ขอ video file เป็น base64 สำหรับ inject เข้า browser
    """
    import base64
    
    log = get_log_orchestrator()
    db = get_db()
    
    from app.core.database import MediaAsset
    
    session = db.get_session()
    try:
        asset = session.query(MediaAsset).filter(MediaAsset.file_hash == file_hash).first()
        
        if not asset:
            raise HTTPException(status_code=404, detail="Video not found")
        
        if not os.path.exists(asset.file_path):
            raise HTTPException(status_code=404, detail="Video file not found on disk")
        
        # Read file and convert to base64
        with open(asset.file_path, 'rb') as f:
            video_bytes = f.read()
        
        video_base64 = base64.b64encode(video_bytes).decode('utf-8')
        
        log.debug(f"Serving video base64: {asset.filename} ({len(video_bytes)} bytes)")
        
        return {
            "file_hash": file_hash,
            "filename": asset.filename,
            "mime_type": asset.mime_type or "video/mp4",
            "size_bytes": len(video_bytes),
            "base64": video_base64
        }
        
    finally:
        session.close()


@app.get("/api/bot/confirm/{job_id}", response_model=ConfirmJobResponse)
async def confirm_job(job_id: int):
    """
    UC-B03: Bot ถามว่าโพสต์ได้มั้ย (Double-check)
    
    ก่อนโพสต์ Bot จะถามอีกครั้งว่า:
    - Job ยังอยู่ในสถานะ processing?
    - ยังไม่เคยโพสต์ลง platform นี้?
    """
    log = get_log_orchestrator()
    db = get_db()
    
    from app.core.database import OrderItem, Order, PostingHistory
    
    session = db.get_session()
    try:
        # Get job
        item = session.query(OrderItem).filter(OrderItem.id == job_id).first()
        
        if not item:
            return ConfirmJobResponse(job_id=job_id, can_post=False, reason="Job not found")
        
        # Check status
        if item.status != 'processing' and item.status != 'new':
            return ConfirmJobResponse(
                job_id=job_id, 
                can_post=False, 
                reason=f"Job status is '{item.status}', not processable"
            )
        
        # Get order to check platform
        order = session.query(Order).filter(Order.id == item.order_id).first()
        
        # Double-check posting history (IRON RULE enforcement)
        already_posted = session.query(PostingHistory).filter(
            PostingHistory.client_id == order.client_id,
            PostingHistory.media_id == item.media_id,
            PostingHistory.platform == order.target_platform
        ).first()
        
        if already_posted:
            # Mark as skipped
            item.status = 'skipped'
            session.commit()
            return ConfirmJobResponse(
                job_id=job_id,
                can_post=False,
                reason="Already posted to this platform (IRON RULE violation)"
            )
        
        # Mark as processing if was new
        if item.status == 'new':
            item.status = 'processing'
            session.commit()
        
        log.debug(f"Job {job_id} confirmed: can_post=True")
        return ConfirmJobResponse(job_id=job_id, can_post=True)
        
    finally:
        session.close()


@app.post("/api/bot/report")
async def report_job(request: ReportJobRequest):
    """
    UC-B04: Bot รายงานผล
    
    หลังโพสต์เสร็จ/ล้มเหลว Bot จะรายงานผล
    ถ้าสำเร็จ จะบันทึกลง posting_history
    """
    log = get_log_orchestrator()
    
    from app.viewmodels.order_vm import get_order_vm
    
    order_vm = get_order_vm()
    success = order_vm.report_job(
        job_id=request.job_id,
        status=request.status,
        log_message=request.log_message or "",
        external_id=request.external_id,
        external_url=request.external_url
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Job not found or report failed")
    
    log.info(f"Job {request.job_id} reported: {request.status}")
    
    return {"status": "ok", "job_id": request.job_id, "reported_status": request.status}


@app.post("/api/bot/heartbeat")
async def heartbeat(request: HeartbeatRequest):
    """
    UC-B05: Bot Heartbeat
    
    Bot ส่ง ping เพื่อบอกว่ายัง online
    """
    orchestrator = get_message_orchestrator()
    orchestrator._update_client_status(request.client_code)
    
    return {"status": "ok", "client_code": request.client_code}


# ============================================================================
# Run with: uvicorn app.api.main:app --reload --port 8000
# ============================================================================
