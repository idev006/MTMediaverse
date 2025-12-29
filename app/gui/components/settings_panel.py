"""
SettingsPanel Component - หน้าตั้งค่า

Usage:
    settings = SettingsPanel(main_window)
    # Theme changes apply immediately
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QFormLayout, QComboBox, QLabel,
    QPushButton, QCheckBox
)

from app.gui.theme_manager import get_theme_manager


class SettingsPanel(QWidget):
    """Settings panel with theme selector and options."""
    
    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Appearance Section
        self._setup_appearance_section(layout)
        
        # API Section
        self._setup_api_section(layout)
        
        layout.addStretch()
    
    def _setup_appearance_section(self, parent_layout):
        """Setup appearance settings."""
        group = QGroupBox("🎨 Appearance")
        form_layout = QFormLayout(group)
        
        # Theme Selector
        self.theme_combo = QComboBox()
        theme_mgr = get_theme_manager()
        
        for name, theme in theme_mgr.get_available_themes().items():
            self.theme_combo.addItem(theme.display_name, name)
            if name == theme_mgr.current_theme.name:
                self.theme_combo.setCurrentIndex(self.theme_combo.count() - 1)
        
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        form_layout.addRow("Theme:", self.theme_combo)
        
        parent_layout.addWidget(group)
    
    def _setup_api_section(self, parent_layout):
        """Setup API settings."""
        group = QGroupBox("🌐 API Settings")
        form_layout = QFormLayout(group)
        
        # API Status
        api_status = QLabel("🟢 Running on http://localhost:8000")
        form_layout.addRow("Status:", api_status)
        
        parent_layout.addWidget(group)
    
    def _on_theme_changed(self, index):
        """Handle theme change."""
        theme_name = self.theme_combo.currentData()
        theme_mgr = get_theme_manager()
        theme_mgr.set_theme(theme_name)
        
        if self.main_window and hasattr(self.main_window, 'apply_theme'):
            self.main_window.apply_theme()
