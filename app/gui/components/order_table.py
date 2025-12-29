"""
OrderTable Component - ตารางแสดง Orders

Usage:
    table = OrderTable()
    table.refresh_orders()
"""

from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtGui import QColor

from app.core.database import get_db, Order


class OrderTable(QTableWidget):
    """ตารางแสดงรายการ Orders"""
    
    COLUMNS = ["Order ID", "Client", "Platform", "Status", "Progress"]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        self.setColumnCount(len(self.COLUMNS))
        self.setHorizontalHeaderLabels(self.COLUMNS)
        
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
    
    def refresh_orders(self, limit: int = 50):
        """โหลดข้อมูล Orders จาก Database"""
        db = get_db()
        session = db.get_session()
        
        try:
            orders = session.query(Order).order_by(Order.id.desc()).limit(limit).all()
            self.setRowCount(len(orders))
            
            for row, order in enumerate(orders):
                self._populate_row(row, order)
                
        finally:
            session.close()
    
    def _populate_row(self, row: int, order: Order):
        """Populate a single row with order data."""
        # Order ID
        self.setItem(row, 0, QTableWidgetItem(str(order.id)))
        
        # Client
        client_code = order.client.client_code if order.client else "Unknown"
        self.setItem(row, 1, QTableWidgetItem(client_code))
        
        # Platform
        self.setItem(row, 2, QTableWidgetItem(order.target_platform))
        
        # Status with color
        status_item = QTableWidgetItem(order.status)
        status_item.setForeground(self._get_status_color(order.status))
        self.setItem(row, 3, status_item)
        
        # Progress
        total = len(order.items)
        done = sum(1 for item in order.items if item.status == 'done')
        progress = f"{done}/{total}"
        self.setItem(row, 4, QTableWidgetItem(progress))
    
    def _get_status_color(self, status: str) -> QColor:
        """Get color for status."""
        colors = {
            'completed': QColor("#4caf50"),
            'processing': QColor("#2196f3"),
            'pending': QColor("#ff9800"),
            'cancelled': QColor("#f44336"),
        }
        return colors.get(status, QColor("#888888"))
