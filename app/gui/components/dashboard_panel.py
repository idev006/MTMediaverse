"""
DashboardPanel Component - หน้า Dashboard หลัก

Usage:
    dashboard = DashboardPanel()
    # Auto-refreshes every 5 seconds
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QGroupBox, QSplitter
)
from PySide6.QtCore import Qt, QTimer

from app.gui.components.stats_card import StatsCard
from app.gui.components.order_table import OrderTable
from app.gui.components.client_table import ClientTable
from app.gui.qt_event_bridge import get_qt_event_bridge
from app.core.database import get_db, Order, ClientAccount, MediaAsset


class DashboardPanel(QWidget):
    """Dashboard หลักแสดงข้อมูลสรุป"""
    
    REFRESH_INTERVAL_MS = 5000  # 5 seconds
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_events()
        self._start_refresh_timer()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Stats Cards Row
        self._setup_stats_cards(layout)
        
        # Tables Splitter
        self._setup_tables(layout)
    
    def _setup_stats_cards(self, parent_layout):
        """Setup stats cards row."""
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)
        
        self.card_products = StatsCard("📦 Products")
        self.card_clips = StatsCard("🎬 Clips")
        self.card_orders = StatsCard("📋 Orders")
        self.card_clients = StatsCard("🤖 Clients Online")
        
        stats_layout.addWidget(self.card_products)
        stats_layout.addWidget(self.card_clips)
        stats_layout.addWidget(self.card_orders)
        stats_layout.addWidget(self.card_clients)
        
        parent_layout.addLayout(stats_layout)
    
    def _setup_tables(self, parent_layout):
        """Setup orders and clients tables."""
        splitter = QSplitter(Qt.Horizontal)
        
        # Orders Table
        orders_group = QGroupBox("Recent Orders")
        orders_layout = QVBoxLayout(orders_group)
        self.order_table = OrderTable()
        orders_layout.addWidget(self.order_table)
        splitter.addWidget(orders_group)
        
        # Clients Table
        clients_group = QGroupBox("Connected Clients")
        clients_layout = QVBoxLayout(clients_group)
        self.client_table = ClientTable()
        clients_layout.addWidget(self.client_table)
        splitter.addWidget(clients_group)
        
        parent_layout.addWidget(splitter)
    
    def _connect_events(self):
        """Connect EventBus signals for real-time updates."""
        bridge = get_qt_event_bridge()
        bridge.order_created.connect(self._on_order_event)
        bridge.order_updated.connect(self._on_order_event)
        bridge.item_completed.connect(self._on_order_event)
        bridge.client_online.connect(self._on_client_event)
        bridge.client_offline.connect(self._on_client_event)
    
    def _on_order_event(self, payload: dict):
        """Handle order events - refresh table."""
        self.order_table.refresh_orders()
        self._refresh_stats()
    
    def _on_client_event(self, payload: dict):
        """Handle client events - refresh table."""
        self.client_table.refresh_clients()
        self._refresh_stats()
    
    def _start_refresh_timer(self):
        """Start timer for periodic refresh."""
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_all)
        self.refresh_timer.start(self.REFRESH_INTERVAL_MS)
        
        # Initial load
        self.refresh_all()
    
    def refresh_all(self):
        """Refresh all data."""
        self._refresh_stats()
        self.order_table.refresh_orders()
        self.client_table.refresh_clients()
    
    def _refresh_stats(self):
        """Refresh stats cards."""
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
