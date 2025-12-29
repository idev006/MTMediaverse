"""
FacebookManager - จัดเตรียม payload สำหรับ Facebook (Reels/Posts)

Features:
- Description/Caption
- Share to Feed option
- Hashtags (ไม่ค่อยสำคัญใน FB)
"""

import random
from typing import Any, Dict, List

from .base import BasePlatformManager, PreparedPayload


class FacebookManager(BasePlatformManager):
    """
    Facebook-specific payload preparation (Reels & Posts)
    
    Constraints:
    - Post text: Max 63,206 characters
    - Reels: Similar to TikTok format
    """
    
    PLATFORM_NAME = "facebook"
    
    MAX_CAPTION_LENGTH = 2000  # Practical limit for Reels
    MAX_HASHTAGS = 5  # FB doesn't emphasize hashtags
    
    # ========================================================================
    # Title
    # ========================================================================
    
    def prepare_title(self, prod_name: str, **kwargs) -> str:
        """Facebook ใช้ caption แทน title"""
        return prod_name
    
    # ========================================================================
    # Description -> Caption
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
        เตรียม Facebook caption
        - FB สามารถใส่ link ได้เลย
        - Reels ชอบ short และ engaging
        """
        parts = []
        
        # Main content
        caption = short_descr if short_descr else long_descr[:300]
        parts.append(caption)
        
        # Affiliate link (FB allows links in captions)
        if affiliate_url:
            separators = ["\n\n🛒 ", "\n\n👉 ", "\n\n✨ "]
            parts.append(random.choice(separators))
            parts.append(f"{affiliate_label}\n{affiliate_url}")
        
        return "".join(parts)
    
    # ========================================================================
    # Tags -> Hashtags
    # ========================================================================
    
    def prepare_tags(self, tags: List[str], **kwargs) -> List[str]:
        """
        เตรียม Facebook hashtags
        - FB ไม่เน้น hashtags มาก
        - ใช้แค่ 3-5 อัน
        """
        if not tags:
            return []
        
        shuffled = self.shuffle_tags(tags, keep_first=2)
        count = random.randint(3, min(self.MAX_HASHTAGS, len(shuffled)))
        selected = shuffled[:count]
        
        # Add # prefix
        return [f"#{tag.replace(' ', '')}" for tag in selected if tag]
    
    # ========================================================================
    # Platform Specific
    # ========================================================================
    
    def get_platform_specific_config(self, config: Dict) -> Dict[str, Any]:
        """
        ดึง Facebook-specific config
        - share_to_feed (for Reels)
        - audience settings
        """
        return {
            'share_to_feed': config.get('share_to_feed', True),
            'share_to_stories': config.get('share_to_stories', False),
            'audience': config.get('audience', 'public'),
        }


def get_facebook_manager() -> FacebookManager:
    """Get FacebookManager instance."""
    return FacebookManager()
