"""
BasePlatformManager - Interface/Abstract Base Class
แต่ละ platform จะ inherit และ implement methods เฉพาะของตัวเอง
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import random


@dataclass
class PreparedPayload:
    """Payload ที่เตรียมพร้อมสำหรับ Bot"""
    title: str
    description: str
    tags: List[str]
    affiliate_url: str
    affiliate_label: str
    platform_specific: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'description': self.description,
            'tags': self.tags,
            'affiliate_url': self.affiliate_url,
            'affiliate_label': self.affiliate_label,
            **self.platform_specific
        }


class BasePlatformManager(ABC):
    """
    Abstract Base Class สำหรับ Platform Managers
    
    แต่ละ platform implement methods ตามความต้องการเฉพาะ:
    - YouTube: title length, description format, category, privacy
    - TikTok: caption length, hashtags format
    - Facebook/Reels: share-to-feed, music selection
    """
    
    PLATFORM_NAME: str = "base"
    
    # ========================================================================
    # Abstract Methods - ต้อง implement ใน subclass
    # ========================================================================
    
    @abstractmethod
    def prepare_title(self, prod_name: str, **kwargs) -> str:
        """เตรียม title ตาม format ของ platform"""
        pass
    
    @abstractmethod
    def prepare_description(
        self, 
        short_descr: str, 
        long_descr: str,
        affiliate_url: str,
        affiliate_label: str,
        **kwargs
    ) -> str:
        """เตรียม description พร้อม affiliate link"""
        pass
    
    @abstractmethod
    def prepare_tags(self, tags: List[str], **kwargs) -> List[str]:
        """เตรียม tags/hashtags ตาม format ของ platform"""
        pass
    
    @abstractmethod
    def get_platform_specific_config(self, config: Dict) -> Dict[str, Any]:
        """ดึง config เฉพาะ platform (playlist, privacy, etc.)"""
        pass
    
    # ========================================================================
    # Common Methods - ใช้ร่วมกันได้
    # ========================================================================
    
    def shuffle_tags(self, tags: List[str], keep_first: int = 2) -> List[str]:
        """Shuffle tags แต่เก็บ N ตัวแรก"""
        if len(tags) <= keep_first:
            return tags.copy()
        
        first_tags = tags[:keep_first]
        rest_tags = tags[keep_first:]
        random.shuffle(rest_tags)
        
        return first_tags + rest_tags
    
    def pick_random_affiliate(self, urls_list: List[Dict]) -> Dict[str, str]:
        """เลือก affiliate link แบบ random (70% primary)"""
        if not urls_list:
            return {'url': '', 'label': ''}
        
        primary = [u for u in urls_list if u.get('is_primary', False)]
        secondary = [u for u in urls_list if not u.get('is_primary', False)]
        
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
    
    def truncate_text(self, text: str, max_length: int, suffix: str = "...") -> str:
        """ตัด text ถ้ายาวเกินไป"""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
    
    # ========================================================================
    # Main Method - เตรียม Payload สมบูรณ์
    # ========================================================================
    
    def prepare_payload(
        self,
        prod_config: Dict[str, Any],
        platform_config: Optional[Dict[str, Any]] = None
    ) -> PreparedPayload:
        """
        เตรียม Payload สมบูรณ์สำหรับ Bot
        
        Args:
            prod_config: Full prod.json content
            platform_config: Platform-specific config
        """
        prod_detail = prod_config.get('prod_detail', {})
        platforms = prod_config.get('platforms', {})
        shopee_config = platforms.get('shopee', {})
        
        # Pick affiliate
        affiliate = self.pick_random_affiliate(shopee_config.get('urls_list', []))
        
        # Prepare each component
        title = self.prepare_title(
            prod_name=prod_detail.get('prod_name', ''),
            short_descr=prod_detail.get('prod_short_descr', '')
        )
        
        description = self.prepare_description(
            short_descr=prod_detail.get('prod_short_descr', ''),
            long_descr=prod_detail.get('prod_long_descr', ''),
            affiliate_url=affiliate['url'],
            affiliate_label=affiliate['label']
        )
        
        tags = self.prepare_tags(prod_detail.get('prod_tags', []))
        
        platform_specific = self.get_platform_specific_config(platform_config or {})
        
        return PreparedPayload(
            title=title,
            description=description,
            tags=tags,
            affiliate_url=affiliate['url'],
            affiliate_label=affiliate['label'],
            platform_specific=platform_specific
        )
