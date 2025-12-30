"""
ProductVM - Product ViewModel for MediaVerse
Handles product folder import with upsert logic.

Features:
- Drag & drop folder import
- Read prod.json for product data (via ProdConfig)
- Upsert: Create if not exists, Update if exists
- Video clip import with duplicate prevention
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.core.database import (
    get_db, DatabaseManager,
    Product, Category, MediaAsset
)
from app.core.event_bus import get_event_bus
from app.core.log_orchestrator import get_log_orchestrator
from app.core.error_orchestrator import get_error_orchestrator, ErrorCategory, ErrorSeverity
from app.core.prod_config import ProdConfig
from app.viewmodels.media_vm import MediaVM, get_media_vm, FolderImportResult


@dataclass
class ProductImportResult:
    """Result of a product folder import."""
    folder_path: str
    product_code: str
    product_name: str
    is_new: bool  # True if created, False if updated
    product_id: Optional[int] = None
    media_import: Optional[FolderImportResult] = None
    errors: List[str] = field(default_factory=list)
    
    @property
    def success(self) -> bool:
        return self.product_id is not None and len(self.errors) == 0
    
    @property
    def summary(self) -> str:
        action = "Created" if self.is_new else "Updated"
        media_summary = self.media_import.summary if self.media_import else "No media"
        return f"{action} product '{self.product_code}' | {media_summary}"


class ProductVM:
    """
    Product ViewModel - Manages products with folder import.
    
    Features:
    - Read prod.json from folder
    - Upsert product (create or update)
    - Import video clips with duplicate prevention
    """
    
    _instance: Optional['ProductVM'] = None
    
    # EventBus topics
    TOPIC_PRODUCT_CREATED = "product/created"
    TOPIC_PRODUCT_UPDATED = "product/updated"
    TOPIC_FOLDER_IMPORTED = "product/folder_imported"
    
    def __new__(cls) -> 'ProductVM':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._db = get_db()
        self._event_bus = get_event_bus()
        self._log = get_log_orchestrator()
        self._error = get_error_orchestrator()
        self._media_vm = get_media_vm()
        
        # Storage directory for prod.json files
        app_dir = Path(__file__).parent.parent
        self._prod_storage_dir = app_dir / 'data' / 'products'
        self._prod_storage_dir.mkdir(parents=True, exist_ok=True)
        
        self._initialized = True
        
        self._log.info("ProductVM initialized")
    
    # ========================================================================
    # prod.json Storage
    # ========================================================================
    
    def get_prod_json_path(self, prod_code: str) -> Path:
        """Get the storage path for a product's prod.json."""
        return self._prod_storage_dir / f"{prod_code}.json"
    
    def copy_prod_json_to_storage(self, source_path: str, prod_code: str) -> bool:
        """
        Copy prod.json to storage with prod_code as filename.
        
        Args:
            source_path: Path to source folder containing prod.json
            prod_code: Product code to use as filename
            
        Returns:
            True if copied successfully
        """
        import shutil
        
        source_file = os.path.join(source_path, 'prod.json')
        dest_file = self.get_prod_json_path(prod_code)
        
        try:
            shutil.copy2(source_file, dest_file)
            self._log.debug(f"Copied prod.json to storage: {dest_file}")
            return True
        except Exception as e:
            self._log.error(f"Failed to copy prod.json: {e}")
            return False
    
    def get_prod_config(self, prod_code: str) -> Optional[ProdConfig]:
        """
        Get ProdConfig for a product.
        
        ProdConfig is the bridge between prod.json and the system.
        
        Args:
            prod_code: Product code
            
        Returns:
            ProdConfig object or None if not found
        """
        json_path = self.get_prod_json_path(prod_code)
        
        if not json_path.exists():
            return None
        
        config = ProdConfig.from_file(str(json_path))
        if not config:
            self._log.error(f"Failed to read prod config for {prod_code}")
        return config
    
    def get_platform_config(self, prod_code: str, platform: str):
        """
        Get platform-specific config for a product.
        
        Args:
            prod_code: Product code
            platform: Platform name (youtube, tiktok, shopee, etc.)
            
        Returns:
            PlatformConfig object or None
        """
        config = self.get_prod_config(prod_code)
        if config:
            return config.get_platform(platform)
        return None
    
    # ========================================================================
    # Read prod.json
    # ========================================================================
    
    def read_prod_json(self, folder_path: str) -> Tuple[Optional[Dict], str]:
        """
        Read and parse prod.json from a folder.
        
        Args:
            folder_path: Path to the product folder
            
        Returns:
            Tuple of (parsed data or None, error message or empty string)
        """
        prod_json_path = os.path.join(folder_path, 'prod.json')
        
        if not os.path.exists(prod_json_path):
            return None, f"prod.json not found in {folder_path}"
        
        try:
            with open(prod_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data, ""
        except json.JSONDecodeError as e:
            return None, f"Invalid JSON: {e}"
        except Exception as e:
            return None, str(e)
    
    # ========================================================================
    # Category Management
    # ========================================================================
    
    def get_or_create_category(self, category_name: str) -> Category:
        """Get existing category or create new one."""
        session = self._db.get_session()
        try:
            category = session.query(Category).filter(
                Category.name == category_name
            ).first()
            
            if not category:
                category = Category(name=category_name)
                session.add(category)
                session.commit()
                self._log.debug(f"Created category: {category_name}")
            
            return category
        finally:
            session.close()
    
    # ========================================================================
    # Product Upsert (Create or Update)
    # ========================================================================
    
    def upsert_product(
        self, 
        prod_detail: Dict[str, Any],
        category_name: Optional[str] = None
    ) -> Tuple[Product, bool]:
        """
        Create or update a product based on prod_code.
        
        Args:
            prod_detail: Product detail from prod.json
            category_name: Optional category name
            
        Returns:
            Tuple of (Product, is_new)
        """
        session = self._db.get_session()
        try:
            prod_code = prod_detail.get('prod_code', '')
            
            # Check if product exists
            existing = session.query(Product).filter(
                Product.sku == prod_code
            ).first()
            
            # Get or create category
            category_id = None
            if category_name:
                category = self.get_or_create_category(category_name)
                category_id = category.id
            
            # Build tags JSON
            tags = prod_detail.get('prod_tags', [])
            
            if existing:
                # UPDATE existing product
                existing.name = prod_detail.get('prod_name', existing.name)
                existing.description = prod_detail.get('prod_long_descr', existing.description)
                existing.tags = tags
                if category_id:
                    existing.category_id = category_id
                
                session.commit()
                
                self._log.info(f"Updated product: {prod_code}")
                self._event_bus.publish(self.TOPIC_PRODUCT_UPDATED, {
                    'product_id': existing.id,
                    'prod_code': prod_code
                }, source='ProductVM')
                
                return existing, False
            else:
                # CREATE new product
                product = Product(
                    sku=prod_code,
                    name=prod_detail.get('prod_name', ''),
                    description=prod_detail.get('prod_long_descr', ''),
                    tags=tags,
                    category_id=category_id
                )
                session.add(product)
                session.commit()
                
                self._log.info(f"Created product: {prod_code}")
                self._event_bus.publish(self.TOPIC_PRODUCT_CREATED, {
                    'product_id': product.id,
                    'prod_code': prod_code
                }, source='ProductVM')
                
                return product, True
                
        except Exception as e:
            session.rollback()
            self._error.handle_error(e, ErrorCategory.DATABASE, ErrorSeverity.HIGH)
            raise
        finally:
            session.close()
    
    # ========================================================================
    # Main Folder Import
    # ========================================================================
    
    def import_product_folder(
        self,
        folder_path: str,
        category_name: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> ProductImportResult:
        """
        Import a product folder with prod.json and video clips.
        
        Process:
        1. Read prod.json
        2. Upsert product (create or update)
        3. Import video clips (skip duplicates)
        
        Args:
            folder_path: Path to the product folder
            category_name: Optional category name
            progress_callback: Optional progress callback
            
        Returns:
            ProductImportResult with all details
        """
        folder_path = os.path.abspath(folder_path)
        
        result = ProductImportResult(
            folder_path=folder_path,
            product_code="",
            product_name="",
            is_new=False
        )
        
        self._log.info(f"Importing product folder: {folder_path}")
        
        # Step 1: Read prod.json
        prod_data, error = self.read_prod_json(folder_path)
        
        if error:
            result.errors.append(error)
            self._log.error(f"Failed to read prod.json: {error}")
            return result
        
        prod_detail = prod_data.get('prod_detail', {})
        result.product_code = prod_detail.get('prod_code', 'UNKNOWN')
        result.product_name = prod_detail.get('prod_name', 'Unknown Product')
        
        # Step 2: Upsert product
        try:
            product, is_new = self.upsert_product(prod_detail, category_name)
            result.product_id = product.id
            result.is_new = is_new
        except Exception as e:
            result.errors.append(f"Product upsert failed: {e}")
            return result
        
        # Step 3: Import video clips (with SHA256 duplicate prevention)
        media_result = self._media_vm.import_folder(
            folder_path=folder_path,
            product_id=product.id,
            recursive=True,
            skip_duplicates=True,  # Skip duplicates gracefully
            progress_callback=progress_callback
        )
        result.media_import = media_result
        
        # Step 4: Copy prod.json to storage (for order preparation)
        self.copy_prod_json_to_storage(folder_path, result.product_code)
        
        # Log summary
        self._log.info(f"Product folder import complete: {result.summary}")
        self._event_bus.publish(self.TOPIC_FOLDER_IMPORTED, {
            'folder_path': folder_path,
            'product_id': product.id,
            'prod_code': result.product_code,
            'is_new': is_new,
            'media_imported': media_result.imported,
            'media_duplicates': media_result.duplicates
        }, source='ProductVM')
        
        return result
    
    # ========================================================================
    # Query Methods
    # ========================================================================
    
    def get_product_by_code(self, prod_code: str) -> Optional[Product]:
        """Get product by SKU/prod_code."""
        session = self._db.get_session()
        try:
            return session.query(Product).filter(
                Product.sku == prod_code
            ).first()
        finally:
            session.close()
    
    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Get product by ID."""
        session = self._db.get_session()
        try:
            return session.query(Product).filter(
                Product.id == product_id
            ).first()
        finally:
            session.close()
    
    def get_all_products(self, limit: int = 1000) -> List[Product]:
        """Get all products."""
        session = self._db.get_session()
        try:
            return session.query(Product).limit(limit).all()
        finally:
            session.close()
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance."""
        cls._instance = None


def get_product_vm() -> ProductVM:
    """Get the global ProductVM instance."""
    return ProductVM()
