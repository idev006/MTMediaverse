"""
Configuration management for MediaVerse
Supports external config files for PyInstaller builds
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
import sys


def get_base_dir() -> Path:
    """Get base directory (works with PyInstaller frozen builds)."""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return Path(sys.executable).parent
    else:
        # Running as script
        return Path(__file__).parent.parent


def get_config_dir() -> Path:
    """Get configuration directory."""
    base = get_base_dir()
    config_dir = base / 'config'
    config_dir.mkdir(exist_ok=True)
    return config_dir


def get_data_dir() -> Path:
    """Get data directory."""
    base = get_base_dir()
    data_dir = base / 'app' / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_logs_dir() -> Path:
    """Get logs directory."""
    base = get_base_dir()
    logs_dir = base / 'app' / 'logs'
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


class Config:
    """
    Configuration manager
    
    Loads settings from external JSON file.
    Falls back to defaults if file doesn't exist.
    """
    
    _instance: Optional['Config'] = None
    
    DEFAULT_SETTINGS = {
        'api': {
            'host': '0.0.0.0',
            'port': 8000
        },
        'database': {
            'path': None  # Will use default
        },
        'logging': {
            'level': 'INFO',
            'file_enabled': True,
            'console_enabled': True
        },
        'security': {
            'api_key_required': False
        }
    }
    
    def __new__(cls) -> 'Config':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._settings: Dict[str, Any] = {}
        self._config_path = get_config_dir() / 'settings.json'
        self._load()
        self._initialized = True
    
    def _load(self) -> None:
        """Load settings from file or create with defaults."""
        if self._config_path.exists():
            try:
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    self._settings = json.load(f)
            except Exception:
                self._settings = self.DEFAULT_SETTINGS.copy()
        else:
            self._settings = self.DEFAULT_SETTINGS.copy()
            self._save()  # Create default config
    
    def _save(self) -> None:
        """Save settings to file."""
        with open(self._config_path, 'w', encoding='utf-8') as f:
            json.dump(self._settings, f, indent=4, ensure_ascii=False)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value by dot notation key (e.g., 'api.port')."""
        keys = key.split('.')
        value = self._settings
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any, save: bool = True) -> None:
        """Set a setting value."""
        keys = key.split('.')
        target = self._settings
        
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        
        target[keys[-1]] = value
        
        if save:
            self._save()
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance."""
        cls._instance = None


def get_config() -> Config:
    """Get the global Config instance."""
    return Config()
