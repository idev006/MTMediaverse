"""
OrderBuilder - สร้าง Order พร้อม Anti-Bot-Detection
Random select clips + Shuffle props

Features:
- Random clip selection (ORDER BY RANDOM)
- Shuffle tags order
- Randomly select affiliate link
- Vary description slightly
- Prevent pattern detection
"""

import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import func

from app.core.database import (
    get_db, MediaAsset, Product, ClientAccount, Order, OrderItem, PostingHistory
)
from app.core.event_bus import get_event_bus
from app.core.log_orchestrator import get_log_orchestrator
from app.viewmodels.product_vm import get_product_vm


@dataclass
class OrderItemPayload:
    """Payload for a single order item (sent to bot)."""
    job_id: int
    media_id: int
    media_hash: str
    title: str
    description: str
    tags: List[str]
    affiliate_url: str
    affiliate_label: str
    platform_config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'job_id': self.job_id,
            'media_id': self.media_id,
            'media_hash': self.media_hash,
            'title': self.title,
            'description': self.description,
            'tags': self.tags,
            'affiliate_url': self.affiliate_url,
            'affiliate_label': self.affiliate_label,
            'platform_config': self.platform_config
        }


@dataclass
class CreatedOrder:
    """Result of order creation."""
    order_id: int
    client_code: str
    platform: str
    items: List[OrderItemPayload]
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'order_id': self.order_id,
            'client_code': self.client_code,
            'platform': self.platform,
            'item_count': len(self.items),
            'items': [item.to_dict() for item in self.items],
            'created_at': self.created_at.isoformat()
        }


class OrderBuilder:
    """
    สร้าง Order พร้อม Anti-Bot-Detection
    
    - Random select clips
    - Shuffle props (tags, affiliate links)
    """
    
    def __init__(self):
        self._db = get_db()
        self._event_bus = get_event_bus()
        self._log = get_log_orchestrator()
        self._product_vm = get_product_vm()
    
    # ========================================================================
    # Anti-Bot-Detection: Shuffle/Randomize
    # ========================================================================
    
    def shuffle_tags(self, tags: List[str], keep_first: int = 2) -> List[str]:
        """
        Shuffle tags แต่เก็บ N ตัวแรกไว้ (มักเป็น keyword สำคัญ)
        
        Args:
            tags: Original tag list
            keep_first: Number of tags to keep at the start
        """
        if len(tags) <= keep_first:
            return tags.copy()
        
        first_tags = tags[:keep_first]
        rest_tags = tags[keep_first:]
        random.shuffle(rest_tags)
        
        return first_tags + rest_tags
    
    def pick_random_affiliate(self, urls_list: List[Dict]) -> Dict:
        """
        เลือก affiliate link แบบ random
        มีโอกาสเลือก primary มากกว่า (70%)
        """
        if not urls_list:
            return {'url': '', 'label': ''}
        
        primary = [u for u in urls_list if u.get('is_primary', False)]
        secondary = [u for u in urls_list if not u.get('is_primary', False)]
        
        # 70% chance เลือก primary (ถ้ามี)
        if primary and random.random() < 0.7:
            chosen = random.choice(primary)
        elif secondary:
            chosen = random.choice(secondary)
        elif primary:
            chosen = random.choice(primary)
        else:
            chosen = urls_list[0]
        
        return {
            'url': chosen.get('url', ''),
            'label': chosen.get('label', '')
        }
    
    def vary_description(self, description: str) -> str:
        """
        เพิ่มความหลากหลายให้ description เล็กน้อย
        เช่น เพิ่ม emoji, เปลี่ยน spacing
        """
        # เพิ่ม/ไม่เพิ่ม line break ท้าย
        if random.random() < 0.5:
            description = description.rstrip() + "\n"
        
        # เพิ่ม emoji random ท้าย (30% chance)
        if random.random() < 0.3:
            emojis = ['👇', '⬇️', '🔽', '📌', '✨', '💯']
            description = description.rstrip() + f" {random.choice(emojis)}"
        
        return description
    
    def select_random_tags_subset(
        self, 
        tags: List[str], 
        min_count: int = 5, 
        max_count: int = 10
    ) -> List[str]:
        """
        เลือก subset ของ tags แบบ random
        ไม่ใช้ทุก tag ทุกครั้ง
        """
        if len(tags) <= min_count:
            return self.shuffle_tags(tags)
        
        count = random.randint(min_count, min(max_count, len(tags)))
        
        # เลือก N ตัวแรก (keyword สำคัญ) + random จากที่เหลือ
        important = tags[:min(3, len(tags))]
        rest = tags[3:]
        
        need_more = count - len(important)
        if need_more > 0 and rest:
            extra = random.sample(rest, min(need_more, len(rest)))
            selected = important + extra
        else:
            selected = important
        
        return self.shuffle_tags(selected)
    
    # ========================================================================
    # Select Available Clips (Random)
    # ========================================================================
    
    def get_available_clips_random(
        self,
        client_id: int,
        platform: str,
        prod_code: Optional[str] = None,
        quantity: int = 10
    ) -> List[MediaAsset]:
        """
        เลือก clips ที่ยังไม่ถูกโพสต์ แบบ RANDOM
        
        Args:
            client_id: Client account ID
            platform: Target platform
            prod_code: Optional - filter by product code
            quantity: Number of clips to select
        """
        session = self._db.get_session()
        try:
            # Subquery: clips ที่โพสต์แล้ว
            posted_subquery = session.query(PostingHistory.media_id).filter(
                PostingHistory.client_id == client_id,
                PostingHistory.platform == platform
            ).subquery()
            
            # Query clips ที่ยังไม่โพสต์
            query = session.query(MediaAsset).filter(
                ~MediaAsset.id.in_(posted_subquery)
            )
            
            # Filter by product if specified
            if prod_code:
                product = session.query(Product).filter(Product.sku == prod_code).first()
                if product:
                    query = query.filter(MediaAsset.product_id == product.id)
            
            # Random order + limit
            clips = query.order_by(func.random()).limit(quantity).all()
            
            return clips
            
        finally:
            session.close()
    
    # ========================================================================
    # Build Order
    # ========================================================================
    
    def create_order(
        self,
        client_code: str,
        platform: str,
        quantity: int = 10,
        prod_code: Optional[str] = None
    ) -> Optional[CreatedOrder]:
        """
        สร้าง Order ให้ Bot พร้อม:
        - Random select clips
        - Shuffled props (anti-detection)
        
        Args:
            client_code: Bot's client code
            platform: Target platform (youtube, tiktok, facebook)
            quantity: Number of clips requested
            prod_code: Optional - specific product
            
        Returns:
            CreatedOrder with all items and shuffled payloads
        """
        session = self._db.get_session()
        try:
            # Get client
            client = session.query(ClientAccount).filter(
                ClientAccount.client_code == client_code
            ).first()
            
            if not client:
                self._log.warning(f"Client not found: {client_code}")
                return None
            
            # Get random available clips
            clips = self.get_available_clips_random(
                client_id=client.id,
                platform=platform,
                prod_code=prod_code,
                quantity=quantity
            )
            
            if not clips:
                self._log.info(f"No available clips for {client_code} on {platform}")
                return None
            
            # Create Order
            order = Order(
                client_id=client.id,
                target_platform=platform,
                status='pending'
            )
            session.add(order)
            session.flush()
            
            # Build items with shuffled payloads
            items: List[OrderItemPayload] = []
            
            for clip in clips:
                # Get product config
                product = session.query(Product).filter(Product.id == clip.product_id).first()
                prod_config = self._product_vm.get_prod_config(product.sku) if product else None
                platform_config = self._product_vm.get_platform_config(product.sku, platform) if product else {}
                
                # Get prod_detail and platform urls
                prod_detail = prod_config.get('prod_detail', {}) if prod_config else {}
                platforms = prod_config.get('platforms', {}) if prod_config else {}
                shopee_config = platforms.get('shopee', {})
                
                # Build payload with shuffling
                tags = prod_detail.get('prod_tags', [])
                shuffled_tags = self.select_random_tags_subset(tags)
                
                affiliate = self.pick_random_affiliate(shopee_config.get('urls_list', []))
                
                description = prod_detail.get('prod_long_descr', '')
                varied_description = self.vary_description(description)
                
                # Create OrderItem in DB
                order_item = OrderItem(
                    order_id=order.id,
                    media_id=clip.id,
                    status='new',
                    posting_config={
                        'title': prod_detail.get('prod_name', clip.filename),
                        'description': varied_description,
                        'tags': shuffled_tags,
                        'affiliate_url': affiliate['url'],
                        'affiliate_label': affiliate['label'],
                        'platform_config': platform_config or {}
                    }
                )
                session.add(order_item)
                session.flush()
                
                # Build response payload
                payload = OrderItemPayload(
                    job_id=order_item.id,
                    media_id=clip.id,
                    media_hash=clip.file_hash,
                    title=prod_detail.get('prod_name', clip.filename),
                    description=varied_description,
                    tags=shuffled_tags,
                    affiliate_url=affiliate['url'],
                    affiliate_label=affiliate['label'],
                    platform_config=platform_config or {}
                )
                items.append(payload)
            
            session.commit()
            
            self._log.info(f"Order {order.id} created for {client_code}: {len(items)} items")
            
            return CreatedOrder(
                order_id=order.id,
                client_code=client_code,
                platform=platform,
                items=items
            )
            
        except Exception as e:
            session.rollback()
            self._log.error(f"Failed to create order: {e}")
            return None
        finally:
            session.close()


def get_order_builder() -> OrderBuilder:
    """Get OrderBuilder instance."""
    return OrderBuilder()
