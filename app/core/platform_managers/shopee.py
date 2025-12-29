"""
ShopeeManager - จัดเตรียม payload สำหรับ Shopee Video

Features:
- Product title/description
- Affiliate links (primary focus)
- Product tags
"""

import random
from typing import Any, Dict, List

from .base import BasePlatformManager, PreparedPayload


class ShopeeManager(BasePlatformManager):
    """
    Shopee-specific payload preparation
    
    Focus:
    - Affiliate links are primary content
    - Short, product-focused descriptions
    """
    
    PLATFORM_NAME = "shopee"
    
    MAX_TITLE_LENGTH = 100
    MAX_DESCRIPTION_LENGTH = 500
    
    # ========================================================================
    # Title
    # ========================================================================
    
    def prepare_title(self, prod_name: str, **kwargs) -> str:
        """เตรียม Shopee title - product-focused"""
        return self.truncate_text(prod_name, self.MAX_TITLE_LENGTH)
    
    # ========================================================================
    # Description
    # ========================================================================
    
    def prepare_description(
        self,
        short_descr: str,
        long_descr: str,
        affiliate_url: str,
        affiliate_label: str,
        **kwargs
    ) -> str:
        """
        เตรียม Shopee description
        - เน้นสั้น กระชับ
        - Affiliate link เป็นหลัก
        """
        parts = []
        
        # Short description only
        if short_descr:
            parts.append(short_descr[:200])
        
        # Affiliate is the main focus
        if affiliate_url:
            parts.append(f"\n\n🛒 {affiliate_label}")
            parts.append(f"👉 {affiliate_url}")
        
        return "\n".join(parts)
    
    # ========================================================================
    # Tags
    # ========================================================================
    
    def prepare_tags(self, tags: List[str], **kwargs) -> List[str]:
        """Shopee tags - product keywords"""
        if not tags:
            return []
        
        shuffled = self.shuffle_tags(tags, keep_first=3)
        return shuffled[:10]  # Max 10 tags
    
    # ========================================================================
    # Platform Specific
    # ========================================================================
    
    def get_platform_specific_config(self, config: Dict) -> Dict[str, Any]:
        """Shopee-specific config - mainly affiliate data"""
        return {
            'urls_list': config.get('urls_list', []),
            'discount_code': config.get('discount_code'),
        }


def get_shopee_manager() -> ShopeeManager:
    """Get ShopeeManager instance."""
    return ShopeeManager()
