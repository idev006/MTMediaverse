"""
Database Layer - SQLAlchemy Models for MediaVerse
Defines all database tables and relationships.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Float, 
    DateTime, ForeignKey, UniqueConstraint, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
import os
import json

Base = declarative_base()


# ============================================================================
# Core Asset Tables
# ============================================================================

class Category(Base):
    """Product categories."""
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    
    # Relationships
    products = relationship("Product", back_populates="category")
    
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"


class Product(Base):
    """Products that can have media assets."""
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('categories.id'))
    sku = Column(String(100), unique=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    affiliate_link = Column(String(500))
    tags = Column(JSON)  # JSON Array of tags
    price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    category = relationship("Category", back_populates="products")
    media_assets = relationship("MediaAsset", back_populates="product")
    
    def get_tags_list(self) -> List[str]:
        """Get tags as a Python list."""
        if isinstance(self.tags, list):
            return self.tags
        if isinstance(self.tags, str):
            try:
                return json.loads(self.tags)
            except:
                return []
        return []
    
    def __repr__(self):
        return f"<Product(id={self.id}, sku='{self.sku}', name='{self.name}')>"


class MediaAsset(Base):
    """Video files and other media assets."""
    __tablename__ = 'media_assets'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_hash = Column(String(64), unique=True, nullable=False)  # SHA256
    duration = Column(Integer)  # Duration in seconds
    file_size = Column(Integer)  # Size in bytes
    mime_type = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="media_assets")
    order_items = relationship("OrderItem", back_populates="media_asset")
    posting_history = relationship("PostingHistory", back_populates="media_asset")
    
    def __repr__(self):
        return f"<MediaAsset(id={self.id}, filename='{self.filename}')>"


# ============================================================================
# Client & Order System Tables
# ============================================================================

class ClientAccount(Base):
    """Bot client accounts."""
    __tablename__ = 'client_accounts'
    
    id = Column(Integer, primary_key=True)
    client_code = Column(String(50), unique=True, nullable=False)  # e.g., "BOT-001"
    name = Column(String(255))
    platform = Column(String(50), nullable=False)  # 'youtube', 'tiktok', 'facebook'
    settings = Column(JSON)  # Platform-specific settings
    last_seen = Column(DateTime)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    orders = relationship("Order", back_populates="client")
    posting_history = relationship("PostingHistory", back_populates="client")
    
    def __repr__(self):
        return f"<ClientAccount(id={self.id}, client_code='{self.client_code}', platform='{self.platform}')>"


class Order(Base):
    """Orders for content distribution."""
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('client_accounts.id'))
    target_platform = Column(String(50), nullable=False)  # 'youtube', 'tiktok', 'facebook'
    status = Column(String(20), default='pending')  # 'pending', 'processing', 'completed', 'cancelled'
    priority = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationships
    client = relationship("ClientAccount", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Order(id={self.id}, client_id={self.client_id}, status='{self.status}')>"


class OrderItem(Base):
    """Individual items within an order."""
    __tablename__ = 'order_items'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    media_id = Column(Integer, ForeignKey('media_assets.id'))
    status = Column(String(20), default='new')  # 'new', 'processing', 'done', 'failed'
    posting_config = Column(JSON)  # Platform-specific configuration
    error_log = Column(Text)
    attempt_count = Column(Integer, default=0)
    assigned_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relationships
    order = relationship("Order", back_populates="items")
    media_asset = relationship("MediaAsset", back_populates="order_items")
    
    def get_posting_config(self) -> dict:
        """Get posting configuration as a dictionary."""
        if isinstance(self.posting_config, dict):
            return self.posting_config
        if isinstance(self.posting_config, str):
            try:
                return json.loads(self.posting_config)
            except:
                return {}
        return {}
    
    def __repr__(self):
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, status='{self.status}')>"


# ============================================================================
# Safety Layer - Duplicate Prevention
# ============================================================================

class PostingHistory(Base):
    """
    Tracks posted content to prevent duplicates.
    UNIQUE constraint on (client_id, media_id, platform) ensures
    a bot never posts the same media to the same platform twice.
    """
    __tablename__ = 'posting_history'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('client_accounts.id'))
    media_id = Column(Integer, ForeignKey('media_assets.id'))
    platform = Column(String(50), nullable=False)
    external_id = Column(String(255))  # Platform-specific post ID
    external_url = Column(String(500))  # URL to the posted content
    posted_at = Column(DateTime, default=datetime.utcnow)
    
    # Composite unique constraint - THE DUPLICATE GUARD
    __table_args__ = (
        UniqueConstraint('client_id', 'media_id', 'platform', name='uq_posting_history'),
    )
    
    # Relationships
    client = relationship("ClientAccount", back_populates="posting_history")
    media_asset = relationship("MediaAsset", back_populates="posting_history")
    
    def __repr__(self):
        return f"<PostingHistory(id={self.id}, client_id={self.client_id}, media_id={self.media_id}, platform='{self.platform}')>"


# ============================================================================
# Database Manager
# ============================================================================

class DatabaseManager:
    """
    Manages database connections and sessions.
    Singleton pattern for application-wide database access.
    """
    
    _instance: Optional['DatabaseManager'] = None
    
    def __new__(cls, db_path: Optional[str] = None) -> 'DatabaseManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_path: Optional[str] = None):
        if self._initialized:
            return
        
        if db_path is None:
            # Default to mt_media.db in the app/data directory
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(app_dir, 'data')
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, 'mt_media.db')
        
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        self._initialized = True
    
    def create_tables(self) -> None:
        """Create all database tables."""
        Base.metadata.create_all(self.engine)
    
    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()
    
    def close(self) -> None:
        """Close database connections."""
        self.engine.dispose()
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (useful for testing)."""
        if cls._instance:
            cls._instance.close()
        cls._instance = None


def get_db() -> DatabaseManager:
    """Get the global DatabaseManager instance."""
    return DatabaseManager()


def init_database(db_path: Optional[str] = None) -> DatabaseManager:
    """Initialize the database and create all tables."""
    db = DatabaseManager(db_path)
    db.create_tables()
    return db
