"""
OrderService - Business logic for order operations

Separates business logic from API endpoints.
Used by both API and GUI.
"""

from typing import Any, Dict, List, Optional

from app.core.database import get_db, ClientAccount, Order, OrderItem, MediaAsset
from app.core.log_orchestrator import get_log_orchestrator
from app.viewmodels.order_builder import get_order_builder, CreatedOrder


class OrderService:
    """
    Service layer for order operations.
    
    Provides clean API for:
    - Creating orders (Just-in-Time)
    - Confirming jobs
    - Reporting results
    """
    
    def __init__(self):
        self._db = get_db()
        self._log = get_log_orchestrator()
        self._order_builder = get_order_builder()
    
    def create_order(
        self,
        client_code: str,
        quantity: int = 10,
        prod_code: Optional[str] = None
    ) -> Optional[CreatedOrder]:
        """
        Create order for a client (Just-in-Time).
        
        Args:
            client_code: Bot's client code
            quantity: Number of clips to include
            prod_code: Optional specific product
            
        Returns:
            CreatedOrder or None if failed
        """
        # Get client to find platform
        session = self._db.get_session()
        try:
            client = session.query(ClientAccount).filter(
                ClientAccount.client_code == client_code
            ).first()
            
            if not client:
                self._log.warning(f"Client not found: {client_code}")
                return None
            
            # Create order via OrderBuilder
            order = self._order_builder.create_order(
                client_code=client_code,
                platform=client.target_platform,
                quantity=quantity,
                prod_code=prod_code
            )
            
            return order
            
        finally:
            session.close()
    
    def confirm_job(self, job_id: int) -> Dict[str, Any]:
        """
        Confirm a job can be posted (double-check).
        
        Args:
            job_id: OrderItem ID
            
        Returns:
            {can_post: bool, reason: str}
        """
        session = self._db.get_session()
        try:
            job = session.query(OrderItem).filter(
                OrderItem.id == job_id
            ).first()
            
            if not job:
                return {'can_post': False, 'reason': 'Job not found'}
            
            if job.status != 'processing':
                return {'can_post': False, 'reason': f'Invalid status: {job.status}'}
            
            # Check if already posted (IRON RULE)
            from app.core.database import PostingHistory
            
            media = session.query(MediaAsset).filter(
                MediaAsset.id == job.media_id
            ).first()
            
            order = session.query(Order).filter(
                Order.id == job.order_id
            ).first()
            
            if media and order:
                existing = session.query(PostingHistory).filter(
                    PostingHistory.media_id == media.id,
                    PostingHistory.platform == order.target_platform
                ).first()
                
                if existing:
                    return {'can_post': False, 'reason': 'Already posted to this platform'}
            
            return {'can_post': True, 'reason': 'OK'}
            
        finally:
            session.close()
    
    def report_job(
        self,
        job_id: int,
        status: str,
        external_id: Optional[str] = None,
        external_url: Optional[str] = None,
        log_message: Optional[str] = None
    ) -> bool:
        """
        Report job completion.
        
        Args:
            job_id: OrderItem ID
            status: 'success' or 'failed'
            external_id: Platform's post ID
            external_url: URL of posted content
            log_message: Any log/error message
            
        Returns:
            True if recorded successfully
        """
        session = self._db.get_session()
        try:
            job = session.query(OrderItem).filter(
                OrderItem.id == job_id
            ).first()
            
            if not job:
                return False
            
            # Update job status
            job.status = 'done' if status == 'success' else 'failed'
            job.error_message = log_message or ''
            
            # If success, record in PostingHistory
            if status == 'success':
                from app.core.database import PostingHistory
                
                order = session.query(Order).filter(
                    Order.id == job.order_id
                ).first()
                
                if order:
                    history = PostingHistory(
                        client_id=order.client_id,
                        media_id=job.media_id,
                        platform=order.target_platform,
                        post_id=external_id,
                        post_url=external_url
                    )
                    session.add(history)
            
            session.commit()
            self._log.info(f"Job {job_id} reported: {status}")
            return True
            
        except Exception as e:
            session.rollback()
            self._log.error(f"Failed to report job: {e}")
            return False
        finally:
            session.close()


# Singleton getter
_order_service: Optional[OrderService] = None


def get_order_service() -> OrderService:
    """Get global OrderService instance."""
    global _order_service
    if _order_service is None:
        _order_service = OrderService()
    return _order_service
