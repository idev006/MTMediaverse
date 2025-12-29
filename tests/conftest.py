"""
Test configuration and fixtures for pytest
"""

import os
import sys
import pytest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Use test database
os.environ['MEDIAVERSE_TEST'] = '1'


@pytest.fixture(scope='session')
def test_db():
    """Create a test database."""
    from app.core.database import DatabaseManager, init_database
    
    # Use in-memory database for tests
    test_db_path = PROJECT_ROOT / 'tests' / 'test_data' / 'test.db'
    test_db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Reset singleton
    DatabaseManager.reset_instance()
    
    # Create test database
    db = DatabaseManager(str(test_db_path))
    init_database()
    
    yield db
    
    # Cleanup
    DatabaseManager.reset_instance()
    if test_db_path.exists():
        os.remove(test_db_path)


@pytest.fixture
def sample_prod_config():
    """Sample product configuration."""
    return {
        "schema_version": "1.0",
        "prod_detail": {
            "prod_code": "TEST-001",
            "prod_name": "Test Product",
            "prod_short_descr": "Short description",
            "prod_long_descr": "Long description for testing",
            "prod_tags": ["test", "product", "sample"]
        },
        "platforms": {
            "youtube": {
                "category_id": 22,
                "privacy": "unlisted"
            },
            "tiktok": {
                "schedule_times": {"mon": ["10:00"]}
            },
            "shopee": {
                "urls_list": [
                    {"label": "Test Shop", "url": "https://test.shop", "is_primary": True}
                ]
            }
        }
    }


@pytest.fixture
def reset_singletons():
    """Reset all singleton instances for clean tests."""
    from app.core.database import DatabaseManager
    from app.core.event_bus import EventBus
    from app.core.message_orchestrator import MessageOrchestrator
    from app.core.log_orchestrator import LogOrchestrator
    from app.core.error_orchestrator import ErrorOrchestrator
    from app.viewmodels.media_vm import MediaVM
    from app.viewmodels.order_vm import OrderVM
    from app.viewmodels.product_vm import ProductVM
    
    yield
    
    # Reset all singletons
    DatabaseManager.reset_instance()
    EventBus.reset_instance()
    MessageOrchestrator.reset_instance()
    LogOrchestrator.reset_instance()
    ErrorOrchestrator.reset_instance()
    MediaVM.reset_instance()
    OrderVM.reset_instance()
    ProductVM.reset_instance()
