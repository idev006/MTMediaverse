"""
ProductsPanel Component - จัดการ Products และ Clips

Features:
- Product list with search
- Clip list for selected product
- Import product from folder with prod.json
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QLineEdit, QLabel, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt

from app.gui.store import get_store
from app.core.database import get_db, Product, MediaAsset


class ProductsPanel(QWidget):
    """Products management panel."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.store = get_store()
        self._setup_ui()
        self._connect_signals()
        self.refresh_products()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        
        splitter = QSplitter(Qt.Horizontal)
        
        # Left: Products List
        left_panel = self._create_products_panel()
        splitter.addWidget(left_panel)
        
        # Right: Clips List
        right_panel = self._create_clips_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([400, 600])
        layout.addWidget(splitter)
    
    def _create_products_panel(self) -> QGroupBox:
        """Create products list panel."""
        group = QGroupBox("📦 Products")
        layout = QVBoxLayout(group)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search products...")
        self.search_input.textChanged.connect(self._on_search)
        toolbar.addWidget(self.search_input)
        
        self.import_btn = QPushButton("📁 Import Folder")
        self.import_btn.setToolTip("Import product from folder with prod.json")
        self.import_btn.clicked.connect(self._on_import_folder)
        toolbar.addWidget(self.import_btn)
        
        layout.addLayout(toolbar)
        
        # Products Table
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(3)
        self.products_table.setHorizontalHeaderLabels(["SKU", "Name", "Clips"])
        self.products_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.products_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.products_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.products_table.itemSelectionChanged.connect(self._on_product_selected)
        layout.addWidget(self.products_table)
        
        return group
    
    def _create_clips_panel(self) -> QGroupBox:
        """Create clips list panel."""
        group = QGroupBox("🎬 Clips")
        layout = QVBoxLayout(group)
        
        # Info Label
        self.clips_info = QLabel("Select a product to view clips")
        layout.addWidget(self.clips_info)
        
        # Clips Table
        self.clips_table = QTableWidget()
        self.clips_table.setColumnCount(4)
        self.clips_table.setHorizontalHeaderLabels(["Filename", "Duration", "Size", "Hash"])
        self.clips_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.clips_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.clips_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.clips_table)
        
        return group
    
    def _connect_signals(self):
        """Connect store signals."""
        self.store.state_changed.connect(self._on_state_changed)
    
    def _on_state_changed(self, key: str, value):
        """Handle store state changes."""
        if key == 'selected_product_id':
            self._load_clips_for_product(value)
    
    def refresh_products(self):
        """Refresh products list from database."""
        db = get_db()
        session = db.get_session()
        
        try:
            products = session.query(Product).all()
            self.products_table.setRowCount(len(products))
            
            for row, product in enumerate(products):
                self.products_table.setItem(row, 0, QTableWidgetItem(product.sku or ""))
                self.products_table.setItem(row, 1, QTableWidgetItem(product.name))
                
                clip_count = len(product.media_assets)
                self.products_table.setItem(row, 2, QTableWidgetItem(str(clip_count)))
                
                # Store product ID in first column
                self.products_table.item(row, 0).setData(Qt.UserRole, product.id)
                
        finally:
            session.close()
    
    def _on_search(self, text: str):
        """Filter products by search text."""
        for row in range(self.products_table.rowCount()):
            match = False
            for col in range(self.products_table.columnCount()):
                item = self.products_table.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.products_table.setRowHidden(row, not match)
    
    def _on_product_selected(self):
        """Handle product selection."""
        selected = self.products_table.selectedItems()
        if selected:
            product_id = selected[0].data(Qt.UserRole)
            self.store.select_order(None)  # Clear order selection
            self._load_clips_for_product(product_id)
    
    def _load_clips_for_product(self, product_id: int):
        """Load clips for selected product."""
        if not product_id:
            self.clips_table.setRowCount(0)
            self.clips_info.setText("Select a product to view clips")
            return
        
        db = get_db()
        session = db.get_session()
        
        try:
            product = session.query(Product).filter(Product.id == product_id).first()
            if not product:
                return
            
            clips = product.media_assets
            self.clips_info.setText(f"📦 {product.name} - {len(clips)} clips")
            self.clips_table.setRowCount(len(clips))
            
            for row, clip in enumerate(clips):
                self.clips_table.setItem(row, 0, QTableWidgetItem(clip.filename))
                
                duration = f"{clip.duration}s" if clip.duration else "-"
                self.clips_table.setItem(row, 1, QTableWidgetItem(duration))
                
                size = self._format_size(clip.file_size) if clip.file_size else "-"
                self.clips_table.setItem(row, 2, QTableWidgetItem(size))
                
                hash_short = clip.file_hash[:12] + "..." if clip.file_hash else "-"
                self.clips_table.setItem(row, 3, QTableWidgetItem(hash_short))
                
        finally:
            session.close()
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    
    def _on_import_folder(self):
        """Handle import folder button."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Product Folder", "",
            QFileDialog.ShowDirsOnly
        )
        
        if folder:
            from app.viewmodels.product_vm import get_product_vm
            
            pvm = get_product_vm()
            result = pvm.import_product_folder(folder)
            
            if result.success:
                action = "Created" if result.is_new else "Updated"
                msg = f"✅ {action} product: {result.product_code}\n"
                if result.media_import:
                    msg += f"📎 Imported: {result.media_import.imported} clips\n"
                    msg += f"⏭️ Skipped: {result.media_import.duplicates} duplicates"
                
                QMessageBox.information(self, "Import Complete", msg)
                self.refresh_products()
                self.store.refresh_stats()
            else:
                QMessageBox.warning(self, "Import Failed", 
                    f"Failed to import: {result.error}")
