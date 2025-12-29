"""
Theme Manager - จัดการ Themes สำหรับ Desktop GUI
รองรับ Dark, Light, และ Custom themes
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from app.core.path_manager import get_path_manager


@dataclass
class Theme:
    """Theme definition"""
    name: str
    display_name: str
    
    # Main colors
    background: str = "#1a1a1a"
    surface: str = "#2d2d2d"
    primary: str = "#0078d4"
    secondary: str = "#333333"
    
    # Text colors
    text_primary: str = "#ffffff"
    text_secondary: str = "#888888"
    text_muted: str = "#666666"
    
    # Status colors
    success: str = "#4caf50"
    warning: str = "#ff9800"
    error: str = "#f44336"
    info: str = "#2196f3"
    
    # Table colors
    table_bg: str = "#1e1e1e"
    table_alt: str = "#252525"
    table_header: str = "#2d2d2d"
    table_border: str = "#333333"
    
    # Tab colors
    tab_bg: str = "#2d2d2d"
    tab_selected: str = "#0078d4"
    tab_text: str = "#888888"
    tab_text_selected: str = "#ffffff"
    
    def to_dict(self) -> Dict[str, str]:
        return {
            'name': self.name,
            'display_name': self.display_name,
            'background': self.background,
            'surface': self.surface,
            'primary': self.primary,
            'secondary': self.secondary,
            'text_primary': self.text_primary,
            'text_secondary': self.text_secondary,
            'text_muted': self.text_muted,
            'success': self.success,
            'warning': self.warning,
            'error': self.error,
            'info': self.info,
            'table_bg': self.table_bg,
            'table_alt': self.table_alt,
            'table_header': self.table_header,
            'table_border': self.table_border,
            'tab_bg': self.tab_bg,
            'tab_selected': self.tab_selected,
            'tab_text': self.tab_text,
            'tab_text_selected': self.tab_text_selected,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'Theme':
        return cls(**data)


# ============================================================================
# Built-in Themes
# ============================================================================

THEME_DARK = Theme(
    name="dark",
    display_name="🌙 Dark Mode",
    background="#1a1a1a",
    surface="#2d2d2d",
    primary="#0078d4",
    text_primary="#ffffff",
)

THEME_MIDNIGHT = Theme(
    name="midnight",
    display_name="🌃 Midnight Blue",
    background="#0d1117",
    surface="#161b22",
    primary="#58a6ff",
    secondary="#21262d",
    text_primary="#c9d1d9",
    text_secondary="#8b949e",
    table_bg="#0d1117",
    table_alt="#161b22",
    table_header="#21262d",
    table_border="#30363d",
    tab_bg="#21262d",
    tab_selected="#58a6ff",
)

THEME_LIGHT = Theme(
    name="light",
    display_name="☀️ Light Mode",
    background="#f5f5f5",
    surface="#ffffff",
    primary="#0078d4",
    secondary="#e0e0e0",
    text_primary="#1a1a1a",
    text_secondary="#666666",
    text_muted="#999999",
    table_bg="#ffffff",
    table_alt="#f9f9f9",
    table_header="#f0f0f0",
    table_border="#e0e0e0",
    tab_bg="#e0e0e0",
    tab_selected="#0078d4",
    tab_text="#666666",
    tab_text_selected="#ffffff",
)

THEME_OCEAN = Theme(
    name="ocean",
    display_name="🌊 Ocean Blue",
    background="#0a192f",
    surface="#112240",
    primary="#64ffda",
    secondary="#1d3a5f",
    text_primary="#ccd6f6",
    text_secondary="#8892b0",
    success="#64ffda",
    warning="#ffd93d",
    error="#ff6b6b",
    info="#4ecdc4",
    table_bg="#0a192f",
    table_alt="#112240",
    table_header="#1d3a5f",
    table_border="#233554",
    tab_bg="#1d3a5f",
    tab_selected="#64ffda",
    tab_text="#8892b0",
    tab_text_selected="#0a192f",
)

THEME_PURPLE = Theme(
    name="purple",
    display_name="💜 Purple Night",
    background="#1a1a2e",
    surface="#16213e",
    primary="#e94560",
    secondary="#0f3460",
    text_primary="#eaeaea",
    text_secondary="#a0a0a0",
    success="#00d9ff",
    warning="#ffc107",
    error="#e94560",
    info="#7c4dff",
    table_bg="#1a1a2e",
    table_alt="#16213e",
    table_header="#0f3460",
    table_border="#2a2a4e",
    tab_bg="#0f3460",
    tab_selected="#e94560",
)


# ============================================================================
# Theme Manager
# ============================================================================

class ThemeManager:
    """จัดการ Themes"""
    
    _instance: Optional['ThemeManager'] = None
    
    # Built-in themes
    THEMES = {
        'dark': THEME_DARK,
        'midnight': THEME_MIDNIGHT,
        'light': THEME_LIGHT,
        'ocean': THEME_OCEAN,
        'purple': THEME_PURPLE,
    }
    
    def __new__(cls) -> 'ThemeManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._current_theme: Theme = THEME_DARK
        self._callbacks = []
        self._load_saved_theme()
        self._initialized = True
    
    def _load_saved_theme(self):
        """Load saved theme from config."""
        path_mgr = get_path_manager()
        theme_file = path_mgr.config_dir / 'theme.json'
        
        if theme_file.exists():
            try:
                with open(theme_file, 'r') as f:
                    data = json.load(f)
                theme_name = data.get('theme', 'dark')
                if theme_name in self.THEMES:
                    self._current_theme = self.THEMES[theme_name]
            except:
                pass
    
    def _save_theme(self):
        """Save current theme to config."""
        path_mgr = get_path_manager()
        theme_file = path_mgr.config_dir / 'theme.json'
        
        with open(theme_file, 'w') as f:
            json.dump({'theme': self._current_theme.name}, f)
    
    @property
    def current_theme(self) -> Theme:
        return self._current_theme
    
    def get_available_themes(self) -> Dict[str, Theme]:
        return self.THEMES.copy()
    
    def set_theme(self, name: str) -> bool:
        """Set current theme by name."""
        if name not in self.THEMES:
            return False
        
        self._current_theme = self.THEMES[name]
        self._save_theme()
        self._notify_callbacks()
        return True
    
    def register_callback(self, callback):
        """Register a callback to be called when theme changes."""
        self._callbacks.append(callback)
    
    def _notify_callbacks(self):
        """Notify all registered callbacks."""
        for callback in self._callbacks:
            try:
                callback(self._current_theme)
            except:
                pass
    
    def generate_stylesheet(self, theme: Optional[Theme] = None) -> str:
        """Generate Qt stylesheet from theme."""
        t = theme or self._current_theme
        
        return f"""
            QMainWindow {{
                background: {t.background};
            }}
            QWidget {{
                background: {t.background};
                color: {t.text_primary};
            }}
            QTabWidget::pane {{
                border: 1px solid {t.table_border};
                background: {t.surface};
            }}
            QTabBar::tab {{
                background: {t.tab_bg};
                color: {t.tab_text};
                padding: 10px 20px;
                border: none;
            }}
            QTabBar::tab:selected {{
                background: {t.tab_selected};
                color: {t.tab_text_selected};
            }}
            QStatusBar {{
                background: {t.surface};
                color: {t.text_secondary};
            }}
            QLabel {{
                color: {t.text_primary};
                background: transparent;
            }}
            QGroupBox {{
                border: 1px solid {t.table_border};
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                color: {t.text_primary};
            }}
            QTableWidget {{
                background: {t.table_bg};
                color: {t.text_primary};
                gridline-color: {t.table_border};
                alternate-background-color: {t.table_alt};
            }}
            QTableWidget::item:selected {{
                background: {t.primary};
            }}
            QHeaderView::section {{
                background: {t.table_header};
                color: {t.text_primary};
                padding: 8px;
                border: none;
            }}
            QFrame {{
                background: {t.surface};
                border-radius: 8px;
            }}
            QPushButton {{
                background: {t.primary};
                color: {t.tab_text_selected};
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background: {t.info};
            }}
            QComboBox {{
                background: {t.surface};
                color: {t.text_primary};
                border: 1px solid {t.table_border};
                padding: 5px;
                border-radius: 4px;
            }}
            QScrollBar:vertical {{
                background: {t.surface};
                width: 10px;
            }}
            QScrollBar::handle:vertical {{
                background: {t.secondary};
                border-radius: 5px;
            }}
        """
    
    @classmethod
    def reset_instance(cls):
        cls._instance = None


def get_theme_manager() -> ThemeManager:
    """Get the global ThemeManager instance."""
    return ThemeManager()
