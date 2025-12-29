"""
MainWindow - หน้าต่างหลักของ MediaVerse Desktop
Real-time monitoring with EventBus integration
"""

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QStatusBar, QFrame, QSplitter,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QGroupBox, QGridLayout, QProgressBar
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor

from app.gui.qt_event_bridge import get_qt_event_bridge
from app.core.database import get_db, Order, OrderItem, ClientAccount, MediaAsset


class StatsCard(QFrame):
    """Card แสดงสถิติ"""
    
    def __init__(self, title: str, value: str = "0", parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet("""
            StatsCard {
                background: #2d2d2d;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(self.title_label)
        
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("color: #fff; font-size: 28px; font-weight: bold;")
        layout.addWidget(self.value_label)
    
    def set_value(self, value: str):
        self.value_label.setText(value)


class OrderTable(QTableWidget):
    """ตารางแสดงรายการ Orders"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels([
            "Order ID", "Client", "Platform", "Status", "Progress"
        ])
        
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        self.setAlternatingRowColors(True)
        self.setStyleSheet("""
            QTableWidget {
                background: #1e1e1e;
                color: #fff;
                gridline-color: #333;
            }
            QTableWidget::item:selected {
                background: #0078d4;
            }
            QHeaderView::section {
                background: #2d2d2d;
                color: #fff;
                padding: 8px;
                border: none;
            }
        """)
    
    def refresh_orders(self):
        """โหลดข้อมูล Orders จาก Database"""
        db = get_db()
        session = db.get_session()
        
        try:
            orders = session.query(Order).order_by(Order.id.desc()).limit(50).all()
            self.setRowCount(len(orders))
            
            for row, order in enumerate(orders):
                # Order ID
                self.setItem(row, 0, QTableWidgetItem(str(order.id)))
                
                # Client
                client_code = order.client.client_code if order.client else "Unknown"
                self.setItem(row, 1, QTableWidgetItem(client_code))
                
                # Platform
                self.setItem(row, 2, QTableWidgetItem(order.target_platform))
                
                # Status
                status_item = QTableWidgetItem(order.status)
                if order.status == 'completed':
                    status_item.setForeground(QColor("#4caf50"))
                elif order.status == 'processing':
                    status_item.setForeground(QColor("#2196f3"))
                elif order.status == 'pending':
                    status_item.setForeground(QColor("#ff9800"))
                self.setItem(row, 3, status_item)
                
                # Progress
                total = len(order.items)
                done = sum(1 for item in order.items if item.status == 'done')
                progress = f"{done}/{total}"
                self.setItem(row, 4, QTableWidgetItem(progress))
                
        finally:
            session.close()


class ClientTable(QTableWidget):
    """ตารางแสดงรายการ Clients"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels([
            "Client Code", "Platform", "Status", "Last Seen"
        ])
        
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        self.setAlternatingRowColors(True)
        self.setStyleSheet("""
            QTableWidget {
                background: #1e1e1e;
                color: #fff;
                gridline-color: #333;
            }
            QHeaderView::section {
                background: #2d2d2d;
                color: #fff;
                padding: 8px;
                border: none;
            }
        """)
    
    def refresh_clients(self):
        """โหลดข้อมูล Clients จาก Database"""
        db = get_db()
        session = db.get_session()
        
        try:
            clients = session.query(ClientAccount).all()
            self.setRowCount(len(clients))
            
            for row, client in enumerate(clients):
                self.setItem(row, 0, QTableWidgetItem(client.client_code))
                self.setItem(row, 1, QTableWidgetItem(client.platform))
                
                status = "🟢 Online" if client.is_active else "🔴 Offline"
                self.setItem(row, 2, QTableWidgetItem(status))
                
                last_seen = client.last_seen.strftime("%H:%M:%S") if client.last_seen else "-"
                self.setItem(row, 3, QTableWidgetItem(last_seen))
                
        finally:
            session.close()


class DashboardPanel(QWidget):
    """Dashboard หลักแสดงข้อมูลสรุป"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_events()
        self._start_refresh_timer()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Stats Cards Row
        stats_layout = QHBoxLayout()
        
        self.card_products = StatsCard("Products")
        self.card_clips = StatsCard("Clips")
        self.card_orders = StatsCard("Orders")
        self.card_clients = StatsCard("Clients Online")
        
        stats_layout.addWidget(self.card_products)
        stats_layout.addWidget(self.card_clips)
        stats_layout.addWidget(self.card_orders)
        stats_layout.addWidget(self.card_clients)
        
        layout.addLayout(stats_layout)
        
        # Tables Splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Orders Table
        orders_group = QGroupBox("Recent Orders")
        orders_group.setStyleSheet("QGroupBox { color: #fff; font-weight: bold; }")
        orders_layout = QVBoxLayout(orders_group)
        self.order_table = OrderTable()
        orders_layout.addWidget(self.order_table)
        splitter.addWidget(orders_group)
        
        # Clients Table
        clients_group = QGroupBox("Connected Clients")
        clients_group.setStyleSheet("QGroupBox { color: #fff; font-weight: bold; }")
        clients_layout = QVBoxLayout(clients_group)
        self.client_table = ClientTable()
        clients_layout.addWidget(self.client_table)
        splitter.addWidget(clients_group)
        
        layout.addWidget(splitter)
    
    def _connect_events(self):
        """Connect EventBus signals for real-time updates"""
        bridge = get_qt_event_bridge()
        bridge.order_created.connect(self._on_order_event)
        bridge.order_updated.connect(self._on_order_event)
        bridge.item_completed.connect(self._on_order_event)
        bridge.client_online.connect(self._on_client_event)
        bridge.client_offline.connect(self._on_client_event)
    
    def _on_order_event(self, payload: dict):
        """Handle order events - refresh table"""
        self.order_table.refresh_orders()
        self._refresh_stats()
    
    def _on_client_event(self, payload: dict):
        """Handle client events - refresh table"""
        self.client_table.refresh_clients()
        self._refresh_stats()
    
    def _start_refresh_timer(self):
        """Timer สำหรับ refresh ทุก 5 วินาที"""
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._refresh_all)
        self.refresh_timer.start(5000)
        
        # Initial load
        self._refresh_all()
    
    def _refresh_all(self):
        """Refresh all data"""
        self._refresh_stats()
        self.order_table.refresh_orders()
        self.client_table.refresh_clients()
    
    def _refresh_stats(self):
        """Refresh stats cards"""
        db = get_db()
        session = db.get_session()
        
        try:
            from app.core.database import Product
            
            products = session.query(Product).count()
            clips = session.query(MediaAsset).count()
            orders = session.query(Order).count()
            clients = session.query(ClientAccount).filter(
                ClientAccount.is_active == 1
            ).count()
            
            self.card_products.set_value(str(products))
            self.card_clips.set_value(str(clips))
            self.card_orders.set_value(str(orders))
            self.card_clients.set_value(str(clients))
            
        finally:
            session.close()


class MainWindow(QMainWindow):
    """MediaVerse Desktop Main Window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MediaVerse - Media Distribution Hub")
        self.setMinimumSize(1200, 700)
        
        self._setup_ui()
        self._apply_dark_theme()
    
    def _setup_ui(self):
        # Central Widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Tab Widget
        tabs = QTabWidget()
        
        # Dashboard Tab
        self.dashboard = DashboardPanel()
        tabs.addTab(self.dashboard, "📊 Dashboard")
        
        # Placeholder tabs
        tabs.addTab(QLabel("Products & Clips management"), "📦 Products")
        tabs.addTab(QLabel("Order history and details"), "📋 Orders")
        tabs.addTab(QLabel("Client management"), "🤖 Clients")
        tabs.addTab(QLabel("System settings"), "⚙️ Settings")
        
        layout.addWidget(tabs)
        
        # Status Bar
        self.statusBar().showMessage("MediaVerse Ready | API: http://localhost:8000")
    
    def _apply_dark_theme(self):
        """Apply dark theme"""
        self.setStyleSheet("""
            QMainWindow {
                background: #1a1a1a;
            }
            QTabWidget::pane {
                border: 1px solid #333;
                background: #1e1e1e;
            }
            QTabBar::tab {
                background: #2d2d2d;
                color: #888;
                padding: 10px 20px;
                border: none;
            }
            QTabBar::tab:selected {
                background: #0078d4;
                color: #fff;
            }
            QStatusBar {
                background: #2d2d2d;
                color: #888;
            }
            QLabel {
                color: #fff;
            }
            QGroupBox {
                border: 1px solid #333;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)


def run_gui():
    """Run the GUI application."""
    from app.core.database import init_database
    from app.core.event_bus import get_event_bus
    
    # Initialize
    init_database()
    get_event_bus().start_async_worker()
    
    # Run Qt App
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    run_gui()
