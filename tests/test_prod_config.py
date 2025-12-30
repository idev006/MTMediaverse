"""
Test ProdConfig class.
"""
import pytest
import json
import tempfile
from pathlib import Path

from app.core.prod_config import ProdConfig, PlatformConfig, AffUrl


class TestProdConfig:
    """Tests for ProdConfig class."""
    
    def test_from_dict(self, sample_prod_json):
        """Test creating ProdConfig from dictionary."""
        config = ProdConfig.from_dict(sample_prod_json)
        
        assert config.prod_code == "TEST001"
        assert config.prod_name == "Test Product"
        assert len(config.tags) == 3
    
    def test_get_platform(self, sample_prod_json):
        """Test getting platform config."""
        config = ProdConfig.from_dict(sample_prod_json)
        
        yt = config.get_platform("youtube")
        assert yt is not None
        assert yt.enabled == True
        assert yt.platform_type == "shorts"
    
    def test_get_enabled_platforms(self, sample_prod_json):
        """Test getting enabled platforms."""
        config = ProdConfig.from_dict(sample_prod_json)
        
        enabled = config.get_enabled_platforms()
        assert len(enabled) == 2
    
    def test_aff_urls(self, sample_prod_json):
        """Test affiliate URLs."""
        config = ProdConfig.from_dict(sample_prod_json)
        
        yt = config.get_platform("youtube")
        primary = yt.get_primary_aff_url()
        
        assert primary is not None
        assert primary.label == "Shop A"
        assert primary.is_primary == True
    
    def test_from_file(self, sample_prod_json, tmp_path):
        """Test loading from file."""
        file_path = tmp_path / "test_prod.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(sample_prod_json, f)
        
        config = ProdConfig.from_file(str(file_path))
        
        assert config is not None
        assert config.prod_code == "TEST001"
    
    def test_to_json(self, sample_prod_json):
        """Test serialization to JSON."""
        config = ProdConfig.from_dict(sample_prod_json)
        json_str = config.to_json()
        
        data = json.loads(json_str)
        assert data['schema_version'] == "2.0"
        assert data['prod_detail']['prod_code'] == "TEST001"


class TestPlatformConfig:
    """Tests for PlatformConfig class."""
    
    def test_schedule_times(self):
        """Test getting schedule times."""
        data = {
            "enabled": True,
            "schedule": {"sun": ["10:00", "14:00"], "mon": ["12:00"]}
        }
        config = PlatformConfig.from_dict("youtube", data)
        
        assert config.get_schedule_times("sun") == ["10:00", "14:00"]
        assert config.get_schedule_times("tue") == []
    
    def test_props(self):
        """Test getting props."""
        data = {
            "enabled": True,
            "props": {"made_for_kids": False, "notify_subscribers": True}
        }
        config = PlatformConfig.from_dict("youtube", data)
        
        assert config.get_prop("made_for_kids") == False
        assert config.get_prop("missing", "default") == "default"
