# Platform Managers - Strategy Pattern for platform-specific payload preparation

from .base import BasePlatformManager, PreparedPayload
from .youtube import YouTubeManager, get_youtube_manager
from .tiktok import TikTokManager, get_tiktok_manager
from .facebook import FacebookManager, get_facebook_manager
from .shopee import ShopeeManager, get_shopee_manager

# Factory function to get the right manager
def get_platform_manager(platform: str) -> BasePlatformManager:
    """Get the appropriate Platform Manager for a given platform."""
    managers = {
        'youtube': get_youtube_manager,
        'tiktok': get_tiktok_manager,
        'facebook': get_facebook_manager,
        'shopee': get_shopee_manager,
    }
    
    factory = managers.get(platform.lower())
    if factory:
        return factory()
    
    raise ValueError(f"Unknown platform: {platform}")


__all__ = [
    'BasePlatformManager', 'PreparedPayload',
    'YouTubeManager', 'get_youtube_manager',
    'TikTokManager', 'get_tiktok_manager',
    'FacebookManager', 'get_facebook_manager',
    'ShopeeManager', 'get_shopee_manager',
    'get_platform_manager',
]
