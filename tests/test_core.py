"""
Tests for Core Components (EventBus, Database, etc.)
"""

import pytest
from datetime import datetime


class TestEventBus:
    """Test EventBus pub/sub functionality."""
    
    def test_subscribe_and_publish(self, reset_singletons):
        from app.core.event_bus import EventBus
        
        bus = EventBus()
        received = []
        
        def handler(msg):
            received.append(msg)
        
        bus.subscribe("test/topic", handler)
        bus.publish("test/topic", {"data": "hello"})
        
        assert len(received) == 1
        assert received[0].payload["data"] == "hello"
    
    def test_wildcard_subscribe(self, reset_singletons):
        from app.core.event_bus import EventBus
        
        bus = EventBus()
        received = []
        
        def handler(msg):
            received.append(msg.topic)
        
        bus.subscribe("order/#", handler)
        bus.publish("order/created", {})
        bus.publish("order/completed", {})
        
        assert len(received) == 2
        assert "order/created" in received
        assert "order/completed" in received
    
    def test_unsubscribe(self, reset_singletons):
        from app.core.event_bus import EventBus
        
        bus = EventBus()
        received = []
        
        def handler(msg):
            received.append(msg)
        
        bus.subscribe("test/topic", handler)
        bus.unsubscribe("test/topic", handler)
        bus.publish("test/topic", {})
        
        assert len(received) == 0


class TestDatabase:
    """Test database operations."""
    
    def test_create_product(self, test_db):
        from app.core.database import Product
        
        session = test_db.get_session()
        try:
            product = Product(
                sku="TEST-001",
                name="Test Product",
                description="Description"
            )
            session.add(product)
            session.commit()
            
            # Verify
            found = session.query(Product).filter(Product.sku == "TEST-001").first()
            assert found is not None
            assert found.name == "Test Product"
        finally:
            session.close()
    
    def test_posting_history_unique_constraint(self, test_db):
        from app.core.database import ClientAccount, MediaAsset, PostingHistory
        from sqlalchemy.exc import IntegrityError
        
        session = test_db.get_session()
        try:
            # Create client and media
            client = ClientAccount(client_code="TEST-BOT", platform="youtube")
            media = MediaAsset(filename="test.mp4", file_path="/test.mp4", file_hash="abc123")
            session.add_all([client, media])
            session.commit()
            
            # First posting - should succeed
            history1 = PostingHistory(
                client_id=client.id,
                media_id=media.id,
                platform="youtube"
            )
            session.add(history1)
            session.commit()
            
            # Duplicate posting - should fail (IRON RULE)
            history2 = PostingHistory(
                client_id=client.id,
                media_id=media.id,
                platform="youtube"
            )
            session.add(history2)
            
            with pytest.raises(IntegrityError):
                session.commit()
                
        finally:
            session.rollback()
            session.close()


class TestMediaVM:
    """Test MediaVM functionality."""
    
    def test_calculate_file_hash(self, test_db, tmp_path, reset_singletons):
        from app.viewmodels.media_vm import MediaVM
        
        # Create test file
        test_file = tmp_path / "test.mp4"
        test_file.write_bytes(b"test video content")
        
        vm = MediaVM()
        hash1 = vm.calculate_file_hash(str(test_file))
        hash2 = vm.calculate_file_hash(str(test_file))
        
        # Same content should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length
    
    def test_duplicate_detection(self, test_db, tmp_path, reset_singletons):
        from app.viewmodels.media_vm import MediaVM
        
        # Create test file
        test_file = tmp_path / "test.mp4"
        test_file.write_bytes(b"test video content")
        
        vm = MediaVM()
        
        # First import
        result1 = vm.import_media(str(test_file))
        assert result1.status == 'imported'
        
        # Second import (duplicate)
        result2 = vm.import_media(str(test_file))
        assert result2.status == 'duplicate'
