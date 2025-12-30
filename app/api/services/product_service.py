"""
ProductService - Business logic for product operations

Handles:
- Product folder import (drag-drop)
- Product listing
- Product updates
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.database import get_db, Product, Category
from app.core.log_orchestrator import get_log_orchestrator
from app.core.prod_config import ProdConfig
from app.viewmodels.product_vm import get_product_vm, ProductImportResult


class ProductService:
    """
    Service layer for product operations.
    
    Provides:
    - Import product folder with prod.json
    - List all products
    - Get product by code
    """
    
    def __init__(self):
        self._db = get_db()
        self._log = get_log_orchestrator()
        self._product_vm = get_product_vm()
    
    def import_folder(
        self, 
        folder_path: str,
        category_name: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> ProductImportResult:
        """
        Import product folder with prod.json and video clips.
        
        Args:
            folder_path: Path to product folder
            category_name: Optional category name
            progress_callback: Optional callback for progress updates
            
        Returns:
            ProductImportResult with import details
        """
        self._log.info(f"Importing product folder: {folder_path}")
        
        result = self._product_vm.import_product_folder(
            folder_path=folder_path,
            category_name=category_name,
            progress_callback=progress_callback
        )
        
        if result.success:
            self._log.info(f"Import success: {result.product_code}")
        else:
            self._log.error(f"Import failed: {result.errors}")
        
        return result
    
    def validate_folder(self, folder_path: str) -> Dict[str, Any]:
        """
        Validate product folder before import.
        
        Args:
            folder_path: Path to folder
            
        Returns:
            Validation result with status and details
        """
        folder = Path(folder_path)
        
        if not folder.exists():
            return {
                'valid': False,
                'error': 'Folder does not exist',
            }
        
        if not folder.is_dir():
            return {
                'valid': False,
                'error': 'Path is not a directory',
            }
        
        # Check prod.json
        prod_json = folder / 'prod.json'
        if not prod_json.exists():
            return {
                'valid': False,
                'error': 'prod.json not found in folder',
            }
        
        # Try to parse prod.json
        config = ProdConfig.from_file(str(prod_json))
        if not config:
            return {
                'valid': False,
                'error': 'Invalid prod.json format',
            }
        
        # Count video files
        video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
        video_files = [
            f for f in folder.iterdir()
            if f.is_file() and f.suffix.lower() in video_extensions
        ]
        
        return {
            'valid': True,
            'prod_code': config.prod_code,
            'prod_name': config.prod_name,
            'video_count': len(video_files),
            'platforms_enabled': [p.name for p in config.get_enabled_platforms()],
        }
    
    def list_products(
        self, 
        limit: int = 100,
        category_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List all products.
        
        Args:
            limit: Max products to return
            category_id: Optional filter by category
            
        Returns:
            List of product dictionaries
        """
        session = self._db.get_session()
        try:
            query = session.query(Product)
            
            if category_id:
                query = query.filter(Product.category_id == category_id)
            
            products = query.limit(limit).all()
            
            return [
                {
                    'id': p.id,
                    'sku': p.sku,
                    'name': p.name,
                    'description': p.description[:100] + '...' if p.description and len(p.description) > 100 else p.description,
                    'category_id': p.category_id,
                    'clip_count': len(p.media_assets) if p.media_assets else 0,
                    'created_at': p.created_at.isoformat() if p.created_at else None,
                }
                for p in products
            ]
            
        finally:
            session.close()
    
    def get_product(self, prod_code: str) -> Optional[Dict[str, Any]]:
        """
        Get product by code with full details.
        
        Args:
            prod_code: Product SKU/code
            
        Returns:
            Product details or None
        """
        product = self._product_vm.get_product_by_code(prod_code)
        
        if not product:
            return None
        
        # Get ProdConfig for platform info
        config = self._product_vm.get_prod_config(prod_code)
        
        return {
            'id': product.id,
            'sku': product.sku,
            'name': product.name,
            'description': product.description,
            'tags': product.tags,
            'category_id': product.category_id,
            'clip_count': len(product.media_assets) if product.media_assets else 0,
            'platforms': {
                p.name: {
                    'enabled': p.enabled,
                    'aff_url_count': len(p.aff_urls),
                }
                for p in config.get_enabled_platforms()
            } if config else {},
            'created_at': product.created_at.isoformat() if product.created_at else None,
        }
    
    def list_categories(self) -> List[Dict[str, Any]]:
        """
        List all categories.
        
        Returns:
            List of category dictionaries
        """
        session = self._db.get_session()
        try:
            categories = session.query(Category).all()
            return [
                {
                    'id': c.id,
                    'name': c.name,
                    'product_count': len(c.products) if c.products else 0,
                }
                for c in categories
            ]
        finally:
            session.close()


# Singleton getter
_product_service: Optional[ProductService] = None


def get_product_service() -> ProductService:
    """Get global ProductService instance."""
    global _product_service
    if _product_service is None:
        _product_service = ProductService()
    return _product_service
