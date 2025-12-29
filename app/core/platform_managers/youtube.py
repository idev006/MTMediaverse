"""
YouTubeManager - จัดเตรียม payload สำหรับ YouTube

Features:
- Title: Max 100 chars
- Description: พร้อม affiliate links + timestamps
- Tags: Max 500 chars รวม
- Category, Privacy, Playlist
"""

import random
from typing import Any, Dict, List

from .base import BasePlatformManager, PreparedPayload


class YouTubeManager(BasePlatformManager):
    """
    YouTube-specific payload preparation
    
    Constraints:
    - Title: Max 100 characters
    - Description: Max 5000 characters
    - Tags: Max 500 characters total, max 30 tags
    """
    
    PLATFORM_NAME = "youtube"
    
    MAX_TITLE_LENGTH = 100
    MAX_DESCRIPTION_LENGTH = 5000
    MAX_TAGS_CHARS = 500
    MAX_TAGS_COUNT = 30
    
    # ========================================================================
    # Title
    # ========================================================================
    
    def prepare_title(self, prod_name: str, **kwargs) -> str:
        """
        เตรียม YouTube title
        - Max 100 chars
        - อาจเพิ่ม emoji หรือ variation
        """
        title = prod_name
        
        # เพิ่ม emoji prefix บางครั้ง (30% chance)
        if random.random() < 0.3:
            prefixes = ['🔥', '✨', '💯', '⭐', '🎯', '👍']
            title = f"{random.choice(prefixes)} {title}"
        
        return self.truncate_text(title, self.MAX_TITLE_LENGTH)
    
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
        เตรียม YouTube description
        - ใช้ long description
        - เพิ่ม affiliate link section
        - เพิ่ม call-to-action
        """
        parts = []
        
        # Main description
        if long_descr:
            parts.append(long_descr)
        elif short_descr:
            parts.append(short_descr)
        
        # Separator
        parts.append("\n" + "═" * 30 + "\n")
        
        # Affiliate section
        if affiliate_url:
            cta_variants = [
                "🛒 สั่งซื้อได้ที่นี่:",
                "🔗 ลิงก์สั่งซื้อ:",
                "📦 คลิกเลย:",
                "✅ ซื้อเลย:",
            ]
            parts.append(random.choice(cta_variants))
            parts.append(f"{affiliate_label}")
            parts.append(f"👉 {affiliate_url}")
        
        # Footer variations
        footers = [
            "\n\n#สบู่ #ของใช้ส่วนตัว",
            "\n\n💬 คอมเมนต์ถามได้นะครับ",
            "\n\n👍 กดไลค์ กดติดตามด้วยนะครับ",
        ]
        parts.append(random.choice(footers))
        
        description = "\n".join(parts)
        return self.truncate_text(description, self.MAX_DESCRIPTION_LENGTH)
    
    # ========================================================================
    # Tags
    # ========================================================================
    
    def prepare_tags(self, tags: List[str], **kwargs) -> List[str]:
        """
        เตรียม YouTube tags
        - Max 500 chars รวม
        - Max 30 tags
        - Shuffle แต่เก็บ important tags
        """
        if not tags:
            return []
        
        # Shuffle
        shuffled = self.shuffle_tags(tags, keep_first=3)
        
        # Limit count
        shuffled = shuffled[:self.MAX_TAGS_COUNT]
        
        # Check total chars
        result = []
        total_chars = 0
        for tag in shuffled:
            if total_chars + len(tag) + 1 <= self.MAX_TAGS_CHARS:  # +1 for comma
                result.append(tag)
                total_chars += len(tag) + 1
            else:
                break
        
        return result
    
    # ========================================================================
    # Platform Specific
    # ========================================================================
    
    def get_platform_specific_config(self, config: Dict) -> Dict[str, Any]:
        """
        ดึง YouTube-specific config
        - category_id
        - privacy (public/unlisted/private)
        - playlist
        - upload_config (made_for_kids, etc.)
        """
        return {
            'category_id': config.get('category_id', 22),  # 22 = People & Blogs
            'privacy': config.get('privacy', 'unlisted'),
            'playlist': config.get('playlist', {}),
            'upload_config': config.get('upload_config', {
                'made_for_kids': False,
                'notify_subscribers': True,
                'embeddable': True
            })
        }


def get_youtube_manager() -> YouTubeManager:
    """Get YouTubeManager instance."""
    return YouTubeManager()
