"""
ClientTable Component - ตารางแสดง Clients

Usage:
    table = ClientTable()
    table.refresh_clients()
"""

from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView

from app.core.database import get_db, ClientAccount


class ClientTable(QTableWidget):
    """ตารางแสดงรายการ Clients"""
    
    COLUMNS = ["Client Code", "Platform", "Status", "Last Seen"]
    
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
    
    def refresh_clients(self):
        """โหลดข้อมูล Clients จาก Database"""
        db = get_db()
        session = db.get_session()
        
        try:
            clients = session.query(ClientAccount).all()
            self.setRowCount(len(clients))
            
            for row, client in enumerate(clients):
                self._populate_row(row, client)
                
        finally:
            session.close()
    
    def _populate_row(self, row: int, client: ClientAccount):
        """Populate a single row with client data."""
        # Client Code
        self.setItem(row, 0, QTableWidgetItem(client.client_code))
        
        # Platform
        self.setItem(row, 1, QTableWidgetItem(client.platform))
        
        # Status
        status = "🟢 Online" if client.is_active else "🔴 Offline"
        self.setItem(row, 2, QTableWidgetItem(status))
        
        # Last Seen
        last_seen = client.last_seen.strftime("%H:%M:%S") if client.last_seen else "-"
        self.setItem(row, 3, QTableWidgetItem(last_seen))
