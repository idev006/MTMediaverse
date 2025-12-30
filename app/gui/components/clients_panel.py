"""
ClientsPanel Component - จัดการ Clients/Bots

Features:
- Client list with status
- Add/Edit client
- View client activity
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QLineEdit, QLabel, QFormLayout, QDialog,
    QDialogButtonBox, QComboBox, QMessageBox
)
from PySide6.QtCore import Qt

from app.gui.store import get_store
from app.core.database import get_db, ClientAccount, Order


class AddClientDialog(QDialog):
    """Dialog to add a new client."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Client")
        self.setMinimumWidth(400)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        
        self.client_code = QLineEdit()
        self.client_code.setPlaceholderText("e.g., BOT-YT-001")
        form.addRow("Client Code:", self.client_code)
        
        self.name = QLineEdit()
        self.name.setPlaceholderText("e.g., YouTube Bot 1")
        form.addRow("Name:", self.name)
        
        self.platform = QComboBox()
        self.platform.addItems(["youtube", "tiktok", "facebook", "shopee"])
        form.addRow("Platform:", self.platform)
        
        layout.addLayout(form)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_data(self) -> dict:
        """Get form data."""
        return {
            'client_code': self.client_code.text().strip(),
            'name': self.name.text().strip(),
            'platform': self.platform.currentText(),
        }


class ClientsPanel(QWidget):
    """Clients management panel."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.store = get_store()
        self._setup_ui()
        self._connect_signals()
        self.refresh_clients()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        
        splitter = QSplitter(Qt.Horizontal)
        
        # Left: Clients List
        left_panel = self._create_clients_panel()
        splitter.addWidget(left_panel)
        
        # Right: Client Details
        right_panel = self._create_details_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([500, 500])
        layout.addWidget(splitter)
    
    def _create_clients_panel(self) -> QGroupBox:
        """Create clients list panel."""
        group = QGroupBox("🤖 Clients")
        layout = QVBoxLayout(group)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.add_btn = QPushButton("➕ Add Client")
        self.add_btn.clicked.connect(self._on_add_client)
        toolbar.addWidget(self.add_btn)
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh_clients)
        toolbar.addWidget(self.refresh_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Clients Table
        self.clients_table = QTableWidget()
        self.clients_table.setColumnCount(4)
        self.clients_table.setHorizontalHeaderLabels([
            "Client Code", "Platform", "Status", "Last Seen"
        ])
        self.clients_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.clients_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.clients_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.clients_table.itemSelectionChanged.connect(self._on_client_selected)
        layout.addWidget(self.clients_table)
        
        return group
    
    def _create_details_panel(self) -> QGroupBox:
        """Create client details panel."""
        group = QGroupBox("📊 Client Details")
        layout = QVBoxLayout(group)
        
        # Info
        self.details_info = QLabel("Select a client to view details")
        layout.addWidget(self.details_info)
        
        # Stats
        stats_layout = QHBoxLayout()
        
        self.stat_orders = QLabel("Orders: -")
        stats_layout.addWidget(self.stat_orders)
        
        self.stat_completed = QLabel("Completed: -")
        stats_layout.addWidget(self.stat_completed)
        
        self.stat_failed = QLabel("Failed: -")
        stats_layout.addWidget(self.stat_failed)
        
        layout.addLayout(stats_layout)
        
        # Recent Orders
        layout.addWidget(QLabel("Recent Orders:"))
        
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(4)
        self.orders_table.setHorizontalHeaderLabels([
            "Order ID", "Platform", "Status", "Created"
        ])
        self.orders_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.orders_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.orders_table)
        
        # Actions
        actions_layout = QHBoxLayout()
        
        self.toggle_btn = QPushButton("🔴 Deactivate")
        self.toggle_btn.clicked.connect(self._on_toggle_client)
        self.toggle_btn.setEnabled(False)
        actions_layout.addWidget(self.toggle_btn)
        
        actions_layout.addStretch()
        layout.addLayout(actions_layout)
        
        return group
    
    def _connect_signals(self):
        """Connect store signals."""
        self.store.state_changed.connect(self._on_state_changed)
    
    def _on_state_changed(self, key: str, value):
        """Handle store state changes."""
        if key == 'clients':
            self._populate_clients_table(value)
    
    def refresh_clients(self):
        """Refresh clients from database."""
        self.store.load_clients()
    
    def _populate_clients_table(self, clients: list):
        """Populate clients table."""
        self.clients_table.setRowCount(len(clients))
        
        for row, client in enumerate(clients):
            self.clients_table.setItem(row, 0, QTableWidgetItem(client['client_code']))
            self.clients_table.setItem(row, 1, QTableWidgetItem(client['platform']))
            
            status = "🟢 Online" if client['is_active'] else "🔴 Offline"
            self.clients_table.setItem(row, 2, QTableWidgetItem(status))
            
            last_seen = client['last_seen'][:8] if client['last_seen'] else "-"
            self.clients_table.setItem(row, 3, QTableWidgetItem(last_seen))
            
            # Store client code
            self.clients_table.item(row, 0).setData(Qt.UserRole, client['client_code'])
    
    def _on_client_selected(self):
        """Handle client selection."""
        selected = self.clients_table.selectedItems()
        if selected:
            client_code = selected[0].data(Qt.UserRole)
            self.store.select_client(client_code)
            self._load_client_details(client_code)
            self.toggle_btn.setEnabled(True)
    
    def _load_client_details(self, client_code: str):
        """Load details for selected client."""
        db = get_db()
        session = db.get_session()
        
        try:
            client = session.query(ClientAccount).filter(
                ClientAccount.client_code == client_code
            ).first()
            
            if not client:
                return
            
            self.details_info.setText(f"🤖 {client.client_code} ({client.platform})")
            
            # Update toggle button
            if client.is_active:
                self.toggle_btn.setText("🔴 Deactivate")
            else:
                self.toggle_btn.setText("🟢 Activate")
            
            # Get stats
            orders = session.query(Order).filter(Order.client_id == client.id).all()
            completed = sum(1 for o in orders if o.status == 'completed')
            
            self.stat_orders.setText(f"Orders: {len(orders)}")
            self.stat_completed.setText(f"Completed: {completed}")
            self.stat_failed.setText(f"Pending: {len(orders) - completed}")
            
            # Recent orders
            recent = orders[:10]
            self.orders_table.setRowCount(len(recent))
            
            for row, order in enumerate(recent):
                self.orders_table.setItem(row, 0, QTableWidgetItem(str(order.id)))
                self.orders_table.setItem(row, 1, QTableWidgetItem(order.target_platform))
                self.orders_table.setItem(row, 2, QTableWidgetItem(order.status))
                created = order.created_at.strftime("%Y-%m-%d") if order.created_at else "-"
                self.orders_table.setItem(row, 3, QTableWidgetItem(created))
                
        finally:
            session.close()
    
    def _on_add_client(self):
        """Handle add client button."""
        dialog = AddClientDialog(self)
        
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            
            if not data['client_code']:
                QMessageBox.warning(self, "Error", "Client code is required")
                return
            
            db = get_db()
            session = db.get_session()
            
            try:
                # Check if exists
                existing = session.query(ClientAccount).filter(
                    ClientAccount.client_code == data['client_code']
                ).first()
                
                if existing:
                    QMessageBox.warning(self, "Error", "Client code already exists")
                    return
                
                client = ClientAccount(
                    client_code=data['client_code'],
                    name=data['name'],
                    platform=data['platform'],
                    is_active=1
                )
                session.add(client)
                session.commit()
                
                QMessageBox.information(self, "Success", 
                    f"Client {data['client_code']} created!")
                self.refresh_clients()
                self.store.refresh_stats()
                
            finally:
                session.close()
    
    def _on_toggle_client(self):
        """Toggle client active status."""
        selected = self.clients_table.selectedItems()
        if not selected:
            return
        
        client_code = selected[0].data(Qt.UserRole)
        
        db = get_db()
        session = db.get_session()
        
        try:
            client = session.query(ClientAccount).filter(
                ClientAccount.client_code == client_code
            ).first()
            
            if client:
                client.is_active = 0 if client.is_active else 1
                session.commit()
                self.refresh_clients()
                self._load_client_details(client_code)
                
        finally:
            session.close()
