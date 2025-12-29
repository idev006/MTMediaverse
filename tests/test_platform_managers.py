"""
Tests for Platform Managers
"""

import pytest
from app.core.platform_managers import (
    get_platform_manager,
    YouTubeManager,
    TikTokManager,
    FacebookManager,
    ShopeeManager
)


class TestPlatformManagerFactory:
    """Test platform manager factory function."""
    
    def test_get_youtube_manager(self):
        manager = get_platform_manager('youtube')
        assert isinstance(manager, YouTubeManager)
        assert manager.PLATFORM_NAME == 'youtube'
    
    def test_get_tiktok_manager(self):
        manager = get_platform_manager('tiktok')
        assert isinstance(manager, TikTokManager)
        assert manager.PLATFORM_NAME == 'tiktok'
    
    def test_get_facebook_manager(self):
        manager = get_platform_manager('facebook')
        assert isinstance(manager, FacebookManager)
        assert manager.PLATFORM_NAME == 'facebook'
    
    def test_get_shopee_manager(self):
        manager = get_platform_manager('shopee')
        assert isinstance(manager, ShopeeManager)
        assert manager.PLATFORM_NAME == 'shopee'
    
    def test_unknown_platform_raises(self):
        with pytest.raises(ValueError):
            get_platform_manager('unknown_platform')


class TestYouTubeManager:
    """Test YouTube-specific payload preparation."""
    
    @pytest.fixture
    def manager(self):
        return YouTubeManager()
    
    def test_prepare_title_truncates(self, manager):
        long_title = "A" * 150
        result = manager.prepare_title(long_title)
        assert len(result) <= manager.MAX_TITLE_LENGTH
    
    def test_prepare_tags_limits_count(self, manager):
        many_tags = [f"tag{i}" for i in range(50)]
        result = manager.prepare_tags(many_tags)
        assert len(result) <= manager.MAX_TAGS_COUNT
    
    def test_shuffle_tags_keeps_first(self, manager):
        tags = ['important1', 'important2', 'other1', 'other2']
        result = manager.shuffle_tags(tags, keep_first=2)
        assert result[0] == 'important1'
        assert result[1] == 'important2'


class TestTikTokManager:
    """Test TikTok-specific payload preparation."""
    
    @pytest.fixture
    def manager(self):
        return TikTokManager()
    
    def test_prepare_tags_adds_hashtag(self, manager):
        tags = ['test', 'sample']
        result = manager.prepare_tags(tags)
        assert all(t.startswith('#') for t in result)
    
    def test_caption_with_hashtags(self, manager):
        caption = "Test caption"
        hashtags = ["#test", "#sample"]
        result = manager.get_caption_with_hashtags(caption, hashtags)
        assert "#test" in result
        assert "#sample" in result


class TestAffiliatePicking:
    """Test affiliate URL selection."""
    
    def test_pick_from_list(self):
        manager = YouTubeManager()
        urls_list = [
            {"url": "https://primary.com", "label": "Primary", "is_primary": True},
            {"url": "https://secondary.com", "label": "Secondary", "is_primary": False}
        ]
        
        # Run multiple times to test randomness
        results = [manager.pick_random_affiliate(urls_list) for _ in range(10)]
        
        # Should return valid URLs
        assert all(r['url'] in ["https://primary.com", "https://secondary.com"] for r in results)
    
    def test_empty_list_returns_empty(self):
        manager = YouTubeManager()
        result = manager.pick_random_affiliate([])
        assert result['url'] == ''
        assert result['label'] == ''
