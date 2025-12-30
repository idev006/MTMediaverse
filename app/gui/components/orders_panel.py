"""
OrdersPanel Component - จัดการ Orders และ OrderItems

Features:
- Order list with filters
- Order items detail
- Status updates
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QComboBox, QLabel
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from app.gui.store import get_store
from app.core.database import get_db, Order, OrderItem


class OrdersPanel(QWidget):
    """Orders management panel."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.store = get_store()
        self._setup_ui()
        self._connect_signals()
        self.refresh_orders()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        
        splitter = QSplitter(Qt.Horizontal)
        
        # Left: Orders List
        left_panel = self._create_orders_panel()
        splitter.addWidget(left_panel)
        
        # Right: Order Items
        right_panel = self._create_items_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([400, 600])
        layout.addWidget(splitter)
    
    def _create_orders_panel(self) -> QGroupBox:
        """Create orders list panel."""
        group = QGroupBox("📋 Orders")
        layout = QVBoxLayout(group)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "pending", "processing", "completed", "cancelled"])
        self.status_filter.currentTextChanged.connect(self._on_filter_changed)
        toolbar.addWidget(QLabel("Status:"))
        toolbar.addWidget(self.status_filter)
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh_orders)
        toolbar.addWidget(self.refresh_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Orders Table
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(5)
        self.orders_table.setHorizontalHeaderLabels([
            "ID", "Client", "Platform", "Status", "Progress"
        ])
        self.orders_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.orders_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.orders_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.orders_table.itemSelectionChanged.connect(self._on_order_selected)
        layout.addWidget(self.orders_table)
        
        return group
    
    def _create_items_panel(self) -> QGroupBox:
        """Create order items panel."""
        group = QGroupBox("📦 Order Items")
        layout = QVBoxLayout(group)
        
        # Info Label
        self.items_info = QLabel("Select an order to view items")
        layout.addWidget(self.items_info)
        
        # Items Table
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels([
            "Job ID", "Media", "Status", "Attempts", "Completed"
        ])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.items_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.items_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.items_table)
        
        return group
    
    def _connect_signals(self):
        """Connect store signals."""
        self.store.state_changed.connect(self._on_state_changed)
    
    def _on_state_changed(self, key: str, value):
        """Handle store state changes."""
        if key == 'orders':
            self._populate_orders_table(value)
    
    def refresh_orders(self):
        """Refresh orders from database."""
        self.store.load_orders()
    
    def _populate_orders_table(self, orders: list):
        """Populate orders table."""
        status_filter = self.status_filter.currentText()
        
        filtered = orders
        if status_filter != "All":
            filtered = [o for o in orders if o['status'] == status_filter]
        
        self.orders_table.setRowCount(len(filtered))
        
        for row, order in enumerate(filtered):
            self.orders_table.setItem(row, 0, QTableWidgetItem(str(order['id'])))
            self.orders_table.setItem(row, 1, QTableWidgetItem(order['client_code']))
            self.orders_table.setItem(row, 2, QTableWidgetItem(order['platform']))
            
            status_item = QTableWidgetItem(order['status'])
            status_item.setForeground(self._get_status_color(order['status']))
            self.orders_table.setItem(row, 3, status_item)
            
            progress = f"{order['done_count']}/{order['item_count']}"
            self.orders_table.setItem(row, 4, QTableWidgetItem(progress))
            
            # Store order ID
            self.orders_table.item(row, 0).setData(Qt.UserRole, order['id'])
    
    def _get_status_color(self, status: str) -> QColor:
        """Get color for status."""
        colors = {
            'completed': QColor("#4caf50"),
            'processing': QColor("#2196f3"),
            'pending': QColor("#ff9800"),
            'cancelled': QColor("#f44336"),
        }
        return colors.get(status, QColor("#888888"))
    
    def _on_filter_changed(self, text: str):
        """Handle filter change."""
        orders = self.store.state.orders
        self._populate_orders_table(orders)
    
    def _on_order_selected(self):
        """Handle order selection."""
        selected = self.orders_table.selectedItems()
        if selected:
            order_id = selected[0].data(Qt.UserRole)
            self.store.select_order(order_id)
            self._load_order_items(order_id)
    
    def _load_order_items(self, order_id: int):
        """Load items for selected order."""
        if not order_id:
            self.items_table.setRowCount(0)
            self.items_info.setText("Select an order to view items")
            return
        
        db = get_db()
        session = db.get_session()
        
        try:
            order = session.query(Order).filter(Order.id == order_id).first()
            if not order:
                return
            
            items = order.items
            self.items_info.setText(
                f"Order #{order.id} - {order.client.client_code if order.client else 'Unknown'} - {len(items)} items"
            )
            self.items_table.setRowCount(len(items))
            
            for row, item in enumerate(items):
                self.items_table.setItem(row, 0, QTableWidgetItem(str(item.id)))
                
                media_name = item.media_asset.filename if item.media_asset else "-"
                self.items_table.setItem(row, 1, QTableWidgetItem(media_name))
                
                status_item = QTableWidgetItem(item.status)
                status_item.setForeground(self._get_status_color(item.status))
                self.items_table.setItem(row, 2, status_item)
                
                self.items_table.setItem(row, 3, QTableWidgetItem(str(item.attempt_count)))
                
                completed = item.completed_at.strftime("%H:%M:%S") if item.completed_at else "-"
                self.items_table.setItem(row, 4, QTableWidgetItem(completed))
                
        finally:
            session.close()
