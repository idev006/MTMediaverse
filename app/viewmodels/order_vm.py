"""
OrderVM - Order ViewModel for MediaVerse
Handles order creation, job assignment, and duplicate prevention.

IRON RULES (กฎเหล็ก):
1. ห้ามโพสต์คลิปซ้ำลงแพลตฟอร์มเดียวกัน (No duplicate posts)
2. ห้ามมีรายการคลิปซ้ำในบิลเดียวกัน (No duplicate items in same order)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.database import (
    get_db, DatabaseManager,
    Order, OrderItem, MediaAsset, ClientAccount, PostingHistory, Product
)
from app.core.event_bus import get_event_bus
from app.core.log_orchestrator import get_log_orchestrator
from app.core.error_orchestrator import get_error_orchestrator, ErrorCategory, ErrorSeverity


@dataclass
class DuplicateCheckResult:
    """Result of duplicate check."""
    has_duplicates: bool
    duplicate_media_ids: List[int]
    already_posted_ids: List[int]
    message: str


class OrderVM:
    """
    Order ViewModel - Manages orders and enforces duplicate prevention rules.
    
    IRON RULES:
    1. Client cannot post same media to same platform twice (posting_history guard)
    2. Order cannot contain duplicate media for same platform (order validation)
    """
    
    _instance: Optional['OrderVM'] = None
    
    # EventBus topics
    TOPIC_ORDER_CREATED = "order/created"
    TOPIC_ORDER_COMPLETED = "order/completed"
    TOPIC_JOB_ASSIGNED = "order/job_assigned"
    TOPIC_JOB_COMPLETED = "order/job_completed"
    TOPIC_JOB_FAILED = "order/job_failed"
    TOPIC_DUPLICATE_BLOCKED = "order/duplicate_blocked"
    
    def __new__(cls) -> 'OrderVM':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._db = get_db()
        self._event_bus = get_event_bus()
        self._log = get_log_orchestrator()
        self._error = get_error_orchestrator()
        self._initialized = True
        
        self._log.info("OrderVM initialized with duplicate prevention rules")
    
    # ========================================================================
    # IRON RULE #1: Check Posting History (No duplicate posts)
    # ========================================================================
    
    def check_already_posted(
        self, 
        client_id: int, 
        media_ids: List[int], 
        platform: str
    ) -> List[int]:
        """
        Check which media IDs have already been posted by this client to this platform.
        
        IRON RULE #1: ห้ามโพสต์คลิปซ้ำลงแพลตฟอร์มเดียวกัน
        
        Args:
            client_id: The client account ID
            media_ids: List of media IDs to check
            platform: Target platform
            
        Returns:
            List of media IDs that have already been posted
        """
        session = self._db.get_session()
        try:
            already_posted = session.query(PostingHistory.media_id).filter(
                and_(
                    PostingHistory.client_id == client_id,
                    PostingHistory.media_id.in_(media_ids),
                    PostingHistory.platform == platform
                )
            ).all()
            
            return [row[0] for row in already_posted]
        finally:
            session.close()
    
    # ========================================================================
    # IRON RULE #2: Check Order for Duplicates (No duplicate items in order)
    # ========================================================================
    
    def check_order_duplicates(self, media_ids: List[int]) -> Tuple[bool, List[int]]:
        """
        Check if there are duplicate media IDs in the order request.
        
        IRON RULE #2: ห้ามมีรายการคลิปซ้ำในบิลเดียวกัน
        
        Args:
            media_ids: List of media IDs in the order
            
        Returns:
            Tuple of (has_duplicates, list of duplicate IDs)
        """
        seen: Set[int] = set()
        duplicates: List[int] = []
        
        for media_id in media_ids:
            if media_id in seen:
                duplicates.append(media_id)
            else:
                seen.add(media_id)
        
        return len(duplicates) > 0, duplicates
    
    # ========================================================================
    # Combined Duplicate Check
    # ========================================================================
    
    def validate_order_media(
        self, 
        client_id: int, 
        media_ids: List[int], 
        platform: str
    ) -> DuplicateCheckResult:
        """
        Validate media IDs for an order against both iron rules.
        
        Args:
            client_id: The client account ID
            media_ids: List of media IDs for the order
            platform: Target platform
            
        Returns:
            DuplicateCheckResult with validation details
        """
        # IRON RULE #2: Check for duplicates in the order itself
        has_order_duplicates, order_duplicates = self.check_order_duplicates(media_ids)
        
        # IRON RULE #1: Check posting history
        already_posted = self.check_already_posted(client_id, media_ids, platform)
        
        has_issues = has_order_duplicates or len(already_posted) > 0
        
        messages = []
        if has_order_duplicates:
            messages.append(f"Order contains duplicate media IDs: {order_duplicates}")
        if already_posted:
            messages.append(f"Media already posted to {platform}: {already_posted}")
        
        return DuplicateCheckResult(
            has_duplicates=has_issues,
            duplicate_media_ids=order_duplicates,
            already_posted_ids=already_posted,
            message=" | ".join(messages) if messages else "OK"
        )
    
    # ========================================================================
    # Order Creation
    # ========================================================================
    
    def create_order(
        self, 
        client_code: str, 
        media_ids: List[int],
        platform: str,
        posting_configs: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[Optional[Order], str]:
        """
        Create a new order with duplicate validation.
        
        Args:
            client_code: Client account code (e.g., "CLIENT-001")
            media_ids: List of media asset IDs to include
            platform: Target platform ('youtube', 'tiktok', 'facebook')
            posting_configs: Optional list of posting configurations for each item
            
        Returns:
            Tuple of (Order or None, error message or success message)
        """
        session = self._db.get_session()
        try:
            # Get client account
            client = session.query(ClientAccount).filter(
                ClientAccount.client_code == client_code
            ).first()
            
            if not client:
                return None, f"Client not found: {client_code}"
            
            # Validate against iron rules
            validation = self.validate_order_media(client.id, media_ids, platform)
            
            if validation.has_duplicates:
                self._log.warning(f"Order creation blocked: {validation.message}")
                self._event_bus.publish(self.TOPIC_DUPLICATE_BLOCKED, {
                    'client_code': client_code,
                    'platform': platform,
                    'reason': validation.message,
                    'duplicate_ids': validation.duplicate_media_ids,
                    'already_posted_ids': validation.already_posted_ids
                }, source='OrderVM')
                return None, f"IRON RULE VIOLATION: {validation.message}"
            
            # Create order
            order = Order(
                client_id=client.id,
                target_platform=platform,
                status='pending'
            )
            session.add(order)
            session.flush()  # Get order ID
            
            # Create order items
            for i, media_id in enumerate(media_ids):
                config = posting_configs[i] if posting_configs and i < len(posting_configs) else {}
                
                item = OrderItem(
                    order_id=order.id,
                    media_id=media_id,
                    status='new',
                    posting_config=config
                )
                session.add(item)
            
            session.commit()
            
            self._log.info(f"Order {order.id} created for {client_code} with {len(media_ids)} items")
            self._event_bus.publish(self.TOPIC_ORDER_CREATED, {
                'order_id': order.id,
                'client_code': client_code,
                'platform': platform,
                'item_count': len(media_ids)
            }, source='OrderVM')
            
            return order, f"Order {order.id} created successfully with {len(media_ids)} items"
            
        except Exception as e:
            session.rollback()
            self._error.handle_error(e, ErrorCategory.DATABASE, ErrorSeverity.HIGH)
            return None, str(e)
        finally:
            session.close()
    
    # ========================================================================
    # Job Assignment (for bots requesting work)
    # ========================================================================
    
    def get_next_job(self, client_code: str) -> Optional[Dict[str, Any]]:
        """
        Get the next available job for a bot.
        
        Args:
            client_code: Bot's client code
            
        Returns:
            Job details dict or None if no job available
        """
        session = self._db.get_session()
        try:
            # Get client
            client = session.query(ClientAccount).filter(
                ClientAccount.client_code == client_code
            ).first()
            
            if not client:
                self._log.warning(f"Unknown client requesting job: {client_code}")
                return None
            
            # Get next pending order item for this client's platform
            item = session.query(OrderItem).join(Order).join(MediaAsset).filter(
                and_(
                    Order.client_id == client.id,
                    Order.target_platform == client.platform,
                    OrderItem.status == 'new'
                )
            ).order_by(Order.priority.desc(), Order.created_at.asc()).first()
            
            if not item:
                return None
            
            # Mark as processing
            item.status = 'processing'
            item.assigned_at = datetime.utcnow()
            item.attempt_count += 1
            session.commit()
            
            # Get media details
            media = session.query(MediaAsset).filter(MediaAsset.id == item.media_id).first()
            product = session.query(Product).filter(Product.id == media.product_id).first() if media else None
            
            job = {
                'job_id': item.id,
                'order_id': item.order_id,
                'media_id': item.media_id,
                'media_url': f"/api/video/{media.file_hash}" if media else None,
                'payload': item.get_posting_config()
            }
            
            # Add product info if available
            if product:
                job['payload'].setdefault('title', product.name)
                job['payload'].setdefault('description', product.description)
                job['payload'].setdefault('tags', product.get_tags_list())
                job['payload'].setdefault('affiliate_link', product.affiliate_link)
            
            self._log.info(f"Job {item.id} assigned to {client_code}")
            
            return job
            
        except Exception as e:
            session.rollback()
            self._error.handle_error(e, ErrorCategory.DATABASE, ErrorSeverity.MEDIUM)
            return None
        finally:
            session.close()
    
    def report_job(
        self, 
        job_id: int, 
        status: str, 
        log_message: str = "",
        external_id: Optional[str] = None,
        external_url: Optional[str] = None
    ) -> bool:
        """
        Report job completion or failure.
        
        When job is done, adds to posting_history to prevent future duplicates.
        
        Args:
            job_id: The order item ID
            status: 'done' or 'failed'
            log_message: Optional log message
            external_id: Platform-specific post ID (if successful)
            external_url: URL to the posted content (if successful)
            
        Returns:
            True if report processed successfully
        """
        session = self._db.get_session()
        try:
            item = session.query(OrderItem).filter(OrderItem.id == job_id).first()
            
            if not item:
                self._log.warning(f"Job not found: {job_id}")
                return False
            
            order = session.query(Order).filter(Order.id == item.order_id).first()
            
            if status == 'done':
                item.status = 'done'
                item.completed_at = datetime.utcnow()
                
                # Add to posting history (IRON RULE #1 enforcement)
                history = PostingHistory(
                    client_id=order.client_id,
                    media_id=item.media_id,
                    platform=order.target_platform,
                    external_id=external_id,
                    external_url=external_url
                )
                session.add(history)
                
                self._log.info(f"Job {job_id} completed - added to posting history")
                self._event_bus.publish(self.TOPIC_JOB_COMPLETED, {
                    'job_id': job_id,
                    'order_id': item.order_id,
                    'media_id': item.media_id,
                    'external_url': external_url
                }, source='OrderVM')
                
            else:  # failed
                item.status = 'failed'
                item.error_log = log_message
                
                self._log.warning(f"Job {job_id} failed: {log_message}")
                self._event_bus.publish(self.TOPIC_JOB_FAILED, {
                    'job_id': job_id,
                    'order_id': item.order_id,
                    'error': log_message
                }, source='OrderVM')
            
            # Check if order is complete
            remaining = session.query(OrderItem).filter(
                and_(
                    OrderItem.order_id == item.order_id,
                    OrderItem.status.in_(['new', 'processing'])
                )
            ).count()
            
            if remaining == 0:
                order.status = 'completed'
                order.completed_at = datetime.utcnow()
                self._event_bus.publish(self.TOPIC_ORDER_COMPLETED, {
                    'order_id': order.id
                }, source='OrderVM')
            
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            self._error.handle_error(e, ErrorCategory.DATABASE, ErrorSeverity.MEDIUM)
            return False
        finally:
            session.close()
    
    # ========================================================================
    # Available Media Query (Excludes already posted)
    # ========================================================================
    
    def get_available_media_for_client(
        self, 
        client_id: int, 
        platform: str,
        limit: int = 100
    ) -> List[MediaAsset]:
        """
        Get media assets that have NOT been posted by this client to this platform.
        
        This enforces IRON RULE #1 by excluding already-posted media from available pool.
        
        Args:
            client_id: The client account ID
            platform: Target platform
            limit: Maximum number of results
            
        Returns:
            List of available MediaAsset objects
        """
        session = self._db.get_session()
        try:
            # Subquery: media IDs already posted
            posted_subquery = session.query(PostingHistory.media_id).filter(
                and_(
                    PostingHistory.client_id == client_id,
                    PostingHistory.platform == platform
                )
            ).subquery()
            
            # Get media NOT in posted list
            available = session.query(MediaAsset).filter(
                ~MediaAsset.id.in_(posted_subquery)
            ).limit(limit).all()
            
            return available
            
        finally:
            session.close()
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance."""
        cls._instance = None


def get_order_vm() -> OrderVM:
    """Get the global OrderVM instance."""
    return OrderVM()
