"""
TikTokManager - จัดเตรียม payload สำหรับ TikTok

Features:
- Caption: Max 2200 chars (รวม hashtags)
- Hashtags: ใส่ใน caption เลย
- Schedule times
"""

import random
from typing import Any, Dict, List

from .base import BasePlatformManager, PreparedPayload


class TikTokManager(BasePlatformManager):
    """
    TikTok-specific payload preparation
    
    Constraints:
    - Caption: Max 2200 characters (includes hashtags)
    - Hashtags: Part of caption, use # prefix
    """
    
    PLATFORM_NAME = "tiktok"
    
    MAX_CAPTION_LENGTH = 2200
    MAX_HASHTAGS = 10
    
    # ========================================================================
    # Title (TikTok ใช้ caption แทน title)
    # ========================================================================
    
    def prepare_title(self, prod_name: str, **kwargs) -> str:
        """TikTok ไม่มี title แยก - ใช้ caption"""
        return prod_name  # Will be combined in caption
    
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
        เตรียม TikTok caption
        - ใช้ short description (TikTok ชอบสั้นกระชับ)
        - เพิ่ม affiliate ท้าย (ถ้ามีที่)
        - Hashtags จะเพิ่มทีหลังโดย prepare_tags
        """
        parts = []
        
        # Hook opening (ดึงดูดความสนใจ)
        hooks = [
            "✨ ",
            "🔥 ",
            "💯 ",
            "👀 ",
            "‼️ ",
        ]
        
        # ใช้ short description
        caption = short_descr if short_descr else long_descr[:200]
        parts.append(random.choice(hooks) + caption)
        
        # Bio link reference (TikTok ใส่ link ใน caption ไม่ได้)
        if affiliate_url:
            link_refs = [
                "\n\n🔗 ลิงก์ในไบโอ",
                "\n\n👆 คลิกลิงก์ในโปรไฟล์",
                "\n\n📌 ดูลิงก์ในไบโอนะ",
            ]
            parts.append(random.choice(link_refs))
        
        return "".join(parts)
    
    # ========================================================================
    # Tags -> Hashtags in Caption
    # ========================================================================
    
    def prepare_tags(self, tags: List[str], **kwargs) -> List[str]:
        """
        เตรียม TikTok hashtags
        - เลือก random subset
        - เพิ่ม # prefix
        - Max 10 hashtags
        """
        if not tags:
            return []
        
        # Shuffle and select subset
        shuffled = self.shuffle_tags(tags, keep_first=2)
        max_count = min(self.MAX_HASHTAGS, len(shuffled))
        min_count = min(5, max_count)  # Ensure min <= max
        count = random.randint(min_count, max_count) if max_count > 0 else 0
        selected = shuffled[:count]
        
        # Add # prefix and clean
        hashtags = []
        for tag in selected:
            # Remove spaces, special chars
            clean_tag = tag.replace(" ", "").replace("#", "")
            if clean_tag:
                hashtags.append(f"#{clean_tag}")
        
        return hashtags
    
    def get_caption_with_hashtags(self, caption: str, hashtags: List[str]) -> str:
        """รวม caption กับ hashtags"""
        hashtag_str = " ".join(hashtags)
        full_caption = f"{caption}\n\n{hashtag_str}"
        return self.truncate_text(full_caption, self.MAX_CAPTION_LENGTH)
    
    # ========================================================================
    # Platform Specific
    # ========================================================================
    
    def get_platform_specific_config(self, config: Dict) -> Dict[str, Any]:
        """
        ดึง TikTok-specific config
        - schedule_times
        - duet/stitch settings
        """
        return {
            'schedule_times': config.get('schedule_times', {}),
            'allow_duet': config.get('allow_duet', True),
            'allow_stitch': config.get('allow_stitch', True),
            'allow_comment': config.get('allow_comment', True),
        }


def get_tiktok_manager() -> TikTokManager:
    """Get TikTokManager instance."""
    return TikTokManager()
