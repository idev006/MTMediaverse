"""
MainWindow - หน้าต่างหลักของ MediaVerse Desktop

Uses Vue.js style component architecture.
Each component is a separate file under app/gui/components/
"""

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QTabWidget, QLabel
)

from app.gui.components import (
    DashboardPanel, SettingsPanel, 
    ProductsPanel, OrdersPanel, ClientsPanel
)
from app.gui.theme_manager import get_theme_manager


class MainWindow(QMainWindow):
    """MediaVerse Desktop Main Window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MediaVerse - Media Distribution Hub")
        self.setMinimumSize(1200, 700)
        
        self.theme_mgr = get_theme_manager()
        self._setup_ui()
        self.apply_theme()
    
    def _setup_ui(self):
        """Setup the main UI layout."""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Tab Widget
        self.tabs = QTabWidget()
        
        # Dashboard Tab
        self.dashboard = DashboardPanel()
        self.tabs.addTab(self.dashboard, "📊 Dashboard")
        
        # Products Tab
        self.products_panel = ProductsPanel()
        self.tabs.addTab(self.products_panel, "📦 Products")
        
        # Orders Tab
        self.orders_panel = OrdersPanel()
        self.tabs.addTab(self.orders_panel, "📋 Orders")
        
        # Clients Tab
        self.clients_panel = ClientsPanel()
        self.tabs.addTab(self.clients_panel, "🤖 Clients")
        
        # Settings Tab
        self.settings_panel = SettingsPanel(self)
        self.tabs.addTab(self.settings_panel, "⚙️ Settings")
        
        layout.addWidget(self.tabs)
        
        # Status Bar
        self._update_status_bar()
    
    def apply_theme(self):
        """Apply current theme from ThemeManager."""
        stylesheet = self.theme_mgr.generate_stylesheet()
        self.setStyleSheet(stylesheet)
        self._update_status_bar()
    
    def _update_status_bar(self):
        """Update status bar with current info."""
        theme = self.theme_mgr.current_theme
        self.statusBar().showMessage(
            f"MediaVerse Ready | Theme: {theme.display_name} | API: http://localhost:8000"
        )


def run_gui():
    """Run the GUI application."""
    from app.core.database import init_database
    from app.core.event_bus import get_event_bus
    
    # Initialize core
    init_database()
    get_event_bus().start_async_worker()
    
    # Run Qt App
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    run_gui()
