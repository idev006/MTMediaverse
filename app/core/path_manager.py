"""
Path Manager - Cross-OS Path Management
รองรับ Windows, macOS, Linux
"""

import os
import sys
from pathlib import Path
from typing import Optional


class PathManager:
    """
    จัดการ paths สำหรับ application
    รองรับ:
    - Development mode (run from source)
    - Frozen mode (PyInstaller executable)
    - Cross-OS (Windows/macOS/Linux)
    """
    
    _instance: Optional['PathManager'] = None
    
    def __new__(cls) -> 'PathManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._is_frozen = getattr(sys, 'frozen', False)
        self._base_dir = self._determine_base_dir()
        self._initialized = True
    
    def _determine_base_dir(self) -> Path:
        """Determine the base directory based on execution context."""
        if self._is_frozen:
            # Running as compiled executable
            return Path(sys.executable).parent
        else:
            # Running as script - go up from app/core/path_manager.py
            return Path(__file__).parent.parent.parent
    
    # ========================================================================
    # Core Directories
    # ========================================================================
    
    @property
    def base_dir(self) -> Path:
        """Project root directory."""
        return self._base_dir
    
    @property
    def app_dir(self) -> Path:
        """App source directory."""
        return self._base_dir / 'app'
    
    @property
    def data_dir(self) -> Path:
        """Data directory (database, products, etc.)."""
        path = self._base_dir / 'app' / 'data'
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @property
    def config_dir(self) -> Path:
        """Configuration directory."""
        path = self._base_dir / 'config'
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @property
    def logs_dir(self) -> Path:
        """Logs directory."""
        path = self._base_dir / 'app' / 'logs'
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @property
    def temp_dir(self) -> Path:
        """Temporary files directory."""
        path = self._base_dir / 'temp'
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    # ========================================================================
    # Specific Paths
    # ========================================================================
    
    @property
    def database_path(self) -> Path:
        """SQLite database path."""
        return self.data_dir / 'mt_media.db'
    
    @property
    def products_dir(self) -> Path:
        """Product configs storage."""
        path = self.data_dir / 'products'
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @property
    def settings_path(self) -> Path:
        """Settings JSON path."""
        return self.config_dir / 'settings.json'
    
    # ========================================================================
    # UI Directories
    # ========================================================================
    
    @property
    def ui_desktop_dir(self) -> Path:
        """Desktop UI (PySide6) directory."""
        return self.app_dir / 'ui' / 'desktop'
    
    @property
    def ui_webapp_dir(self) -> Path:
        """Web app UI directory."""
        return self.app_dir / 'ui' / 'webapp'
    
    @property
    def ui_console_dir(self) -> Path:
        """Console UI directory."""
        return self.app_dir / 'ui' / 'console'
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    @property
    def is_frozen(self) -> bool:
        """Check if running as frozen executable."""
        return self._is_frozen
    
    @property
    def is_windows(self) -> bool:
        """Check if running on Windows."""
        return sys.platform == 'win32'
    
    @property
    def is_macos(self) -> bool:
        """Check if running on macOS."""
        return sys.platform == 'darwin'
    
    @property
    def is_linux(self) -> bool:
        """Check if running on Linux."""
        return sys.platform.startswith('linux')
    
    def get_path(self, *parts) -> Path:
        """Get a path relative to base directory."""
        return self._base_dir.joinpath(*parts)
    
    def ensure_dir(self, path: Path) -> Path:
        """Ensure a directory exists."""
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance."""
        cls._instance = None
    
    def __repr__(self) -> str:
        return f"PathManager(base={self._base_dir}, frozen={self._is_frozen})"


def get_path_manager() -> PathManager:
    """Get the global PathManager instance."""
    return PathManager()
