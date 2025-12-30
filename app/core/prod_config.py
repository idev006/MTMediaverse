"""
ProdConfig - Class สำหรับจัดการ prod.json

Abstraction layer สำหรับอ่าน/เขียน prod.json schema v2.0
ทำให้ส่วนอื่นของ code ไม่ต้องรู้โครงสร้างภายใน

Usage:
    config = ProdConfig.from_file("path/to/prod.json")
    
    # Get product info
    config.prod_code       # "AsepsoSoap001"
    config.prod_name       # "Asepso สบู่..."
    config.tags            # ["tag1", "tag2"]
    
    # Get platform config
    yt = config.get_platform("youtube")
    yt.enabled             # True
    yt.aff_urls            # [{"label": "...", "url": "..."}]
    yt.schedule            # {"sun": ["10:00", "14:00"], ...}
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class AffUrl:
    """Affiliate URL entry."""
    label: str
    url: str
    is_primary: bool = False
    aff_prod_code: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AffUrl':
        return cls(
            label=data.get('label', ''),
            url=data.get('url', ''),
            is_primary=data.get('is_primary', False),
            aff_prod_code=data.get('aff_prod_code'),
        )
    
    def to_dict(self) -> Dict:
        result = {
            'label': self.label,
            'url': self.url,
            'is_primary': self.is_primary,
        }
        if self.aff_prod_code:
            result['aff_prod_code'] = self.aff_prod_code
        return result


@dataclass
class PlatformConfig:
    """Configuration for a specific platform."""
    name: str
    enabled: bool = False
    platform_type: str = "video"
    privacy: str = "public"
    schedule: Dict[str, List[str]] = field(default_factory=dict)
    props: Dict[str, Any] = field(default_factory=dict)
    playlist: Dict[str, Any] = field(default_factory=dict)
    aff_urls: List[AffUrl] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, name: str, data: Dict) -> 'PlatformConfig':
        aff_urls = [AffUrl.from_dict(u) for u in data.get('aff_urls', [])]
        return cls(
            name=name,
            enabled=data.get('enabled', False),
            platform_type=data.get('platform_type', 'video'),
            privacy=data.get('privacy', 'public'),
            schedule=data.get('schedule', {}),
            props=data.get('props', {}),
            playlist=data.get('playlist', {}),
            aff_urls=aff_urls,
        )
    
    def to_dict(self) -> Dict:
        result = {
            'enabled': self.enabled,
            'platform_type': self.platform_type,
            'schedule': self.schedule,
            'props': self.props,
            'aff_urls': [u.to_dict() for u in self.aff_urls],
        }
        if self.privacy:
            result['privacy'] = self.privacy
        if self.playlist:
            result['playlist'] = self.playlist
        return result
    
    def get_primary_aff_url(self) -> Optional[AffUrl]:
        """Get primary affiliate URL."""
        for url in self.aff_urls:
            if url.is_primary:
                return url
        return self.aff_urls[0] if self.aff_urls else None
    
    def get_schedule_times(self, day: str) -> List[str]:
        """Get schedule times for a specific day (sun, mon, tue, ...)."""
        return self.schedule.get(day, [])
    
    def get_prop(self, key: str, default: Any = None) -> Any:
        """Get a platform-specific property."""
        return self.props.get(key, default)


@dataclass
class ProdDetail:
    """Product detail section."""
    prod_code: str
    prod_name: str
    prod_short_descr: str = ""
    prod_long_descr: str = ""
    prod_tags: List[str] = field(default_factory=list)
    category_id: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ProdDetail':
        return cls(
            prod_code=data.get('prod_code', ''),
            prod_name=data.get('prod_name', ''),
            prod_short_descr=data.get('prod_short_descr', ''),
            prod_long_descr=data.get('prod_long_descr', ''),
            prod_tags=data.get('prod_tags', []),
            category_id=data.get('category_id'),
        )
    
    def to_dict(self) -> Dict:
        result = {
            'prod_code': self.prod_code,
            'prod_name': self.prod_name,
            'prod_short_descr': self.prod_short_descr,
            'prod_long_descr': self.prod_long_descr,
            'prod_tags': self.prod_tags,
        }
        if self.category_id:
            result['category_id'] = self.category_id
        return result


class ProdConfig:
    """
    Main class for handling prod.json.
    
    Supports schema v1.0 and v2.0.
    """
    
    SCHEMA_VERSION = "2.0"
    SUPPORTED_PLATFORMS = ['youtube', 'tiktok', 'facebook', 'shopee', 'lazada']
    
    def __init__(self, data: Dict[str, Any]):
        self._raw_data = data
        self._schema_version = data.get('schema_version', '1.0')
        self._prod_detail = ProdDetail.from_dict(data.get('prod_detail', {}))
        self._platforms: Dict[str, PlatformConfig] = {}
        
        # Parse platforms
        platforms_data = data.get('platforms', {})
        for name in self.SUPPORTED_PLATFORMS:
            if name in platforms_data:
                self._platforms[name] = PlatformConfig.from_dict(name, platforms_data[name])
    
    # ========================================================================
    # Factory Methods
    # ========================================================================
    
    @classmethod
    def from_file(cls, path: str) -> Optional['ProdConfig']:
        """Load ProdConfig from a JSON file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls(data)
        except Exception as e:
            print(f"Error loading prod.json: {e}")
            return None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProdConfig':
        """Create ProdConfig from a dictionary."""
        return cls(data)
    
    # ========================================================================
    # Product Properties
    # ========================================================================
    
    @property
    def schema_version(self) -> str:
        return self._schema_version
    
    @property
    def prod_code(self) -> str:
        return self._prod_detail.prod_code
    
    @property
    def prod_name(self) -> str:
        return self._prod_detail.prod_name
    
    @property
    def short_description(self) -> str:
        return self._prod_detail.prod_short_descr
    
    @property
    def long_description(self) -> str:
        return self._prod_detail.prod_long_descr
    
    @property
    def tags(self) -> List[str]:
        return self._prod_detail.prod_tags
    
    @property
    def category_id(self) -> Optional[int]:
        return self._prod_detail.category_id
    
    @property
    def prod_detail(self) -> ProdDetail:
        return self._prod_detail
    
    # ========================================================================
    # Platform Methods
    # ========================================================================
    
    def get_platform(self, name: str) -> Optional[PlatformConfig]:
        """Get configuration for a specific platform."""
        return self._platforms.get(name)
    
    def get_enabled_platforms(self) -> List[PlatformConfig]:
        """Get list of enabled platforms."""
        return [p for p in self._platforms.values() if p.enabled]
    
    def is_platform_enabled(self, name: str) -> bool:
        """Check if a platform is enabled."""
        platform = self._platforms.get(name)
        return platform.enabled if platform else False
    
    def get_platform_aff_urls(self, name: str) -> List[AffUrl]:
        """Get affiliate URLs for a specific platform."""
        platform = self._platforms.get(name)
        return platform.aff_urls if platform else []
    
    def get_platform_schedule(self, name: str) -> Dict[str, List[str]]:
        """Get schedule for a specific platform."""
        platform = self._platforms.get(name)
        return platform.schedule if platform else {}
    
    def get_platform_props(self, name: str) -> Dict[str, Any]:
        """Get props for a specific platform."""
        platform = self._platforms.get(name)
        return platform.props if platform else {}
    
    # ========================================================================
    # Serialization
    # ========================================================================
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            'schema_version': self.SCHEMA_VERSION,
            'prod_detail': self._prod_detail.to_dict(),
            'platforms': {}
        }
        for name, platform in self._platforms.items():
            result['platforms'][name] = platform.to_dict()
        return result
    
    def to_json(self, indent: int = 4) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    def save(self, path: str) -> bool:
        """Save to JSON file."""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self.to_json())
            return True
        except Exception as e:
            print(f"Error saving prod.json: {e}")
            return False
    
    # ========================================================================
    # Raw Data Access (for compatibility)
    # ========================================================================
    
    @property
    def raw_data(self) -> Dict[str, Any]:
        """Get raw dictionary data."""
        return self._raw_data
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from raw data (for backward compatibility)."""
        return self._raw_data.get(key, default)
