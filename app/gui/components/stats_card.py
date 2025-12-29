"""
StatsCard Component - แสดงสถิติแบบ Card

Usage:
    card = StatsCard("Products")
    card.set_value("100")
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel


class StatsCard(QFrame):
    """Card แสดงสถิติ"""
    
    def __init__(self, title: str, value: str = "0", parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self._setup_ui(title, value)
    
    def _setup_ui(self, title: str, value: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(5)
        
        # Title
        self.title_label = QLabel(title)
        self.title_label.setObjectName("statsTitle")
        layout.addWidget(self.title_label)
        
        # Value  
        self.value_label = QLabel(value)
        self.value_label.setObjectName("statsValue")
        layout.addWidget(self.value_label)
        
        layout.addStretch()
    
    def set_value(self, value: str):
        """Update the displayed value."""
        self.value_label.setText(value)
    
    def set_title(self, title: str):
        """Update the title."""
        self.title_label.setText(title)
