"""
VideoService - Business logic for video operations

Handles video file serving and base64 encoding.
"""

import base64
import mimetypes
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from app.core.database import get_db, MediaAsset
from app.core.log_orchestrator import get_log_orchestrator
from app.core.path_manager import get_path_manager


class VideoService:
    """
    Service layer for video operations.
    
    Provides:
    - Get video file by hash
    - Base64 encoding for browser injection
    - Video metadata
    """
    
    def __init__(self):
        self._db = get_db()
        self._log = get_log_orchestrator()
        self._path = get_path_manager()
    
    def get_video_path(self, file_hash: str) -> Optional[Path]:
        """
        Get video file path by hash.
        
        Args:
            file_hash: SHA256 hash
            
        Returns:
            Path to video file or None
        """
        session = self._db.get_session()
        try:
            media = session.query(MediaAsset).filter(
                MediaAsset.file_hash == file_hash
            ).first()
            
            if not media:
                return None
            
            video_path = Path(media.file_path)
            
            if not video_path.exists():
                self._log.warning(f"Video file not found: {video_path}")
                return None
            
            return video_path
            
        finally:
            session.close()
    
    def get_video_bytes(self, file_hash: str) -> Optional[Tuple[bytes, str]]:
        """
        Get video file bytes and MIME type.
        
        Args:
            file_hash: SHA256 hash
            
        Returns:
            Tuple of (bytes, mime_type) or None
        """
        video_path = self.get_video_path(file_hash)
        
        if not video_path:
            return None
        
        mime_type, _ = mimetypes.guess_type(str(video_path))
        if not mime_type:
            mime_type = 'video/mp4'
        
        return (video_path.read_bytes(), mime_type)
    
    def get_video_base64(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get video as base64 string for browser injection.
        
        Args:
            file_hash: SHA256 hash
            
        Returns:
            Dict with base64 data and metadata
        """
        result = self.get_video_bytes(file_hash)
        
        if not result:
            return None
        
        video_bytes, mime_type = result
        
        # Encode to base64
        base64_data = base64.b64encode(video_bytes).decode('utf-8')
        
        return {
            'hash': file_hash,
            'mime_type': mime_type,
            'size_bytes': len(video_bytes),
            'base64': base64_data,
        }
    
    def get_video_info(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get video metadata without file content.
        
        Args:
            file_hash: SHA256 hash
            
        Returns:
            Dict with video metadata
        """
        session = self._db.get_session()
        try:
            media = session.query(MediaAsset).filter(
                MediaAsset.file_hash == file_hash
            ).first()
            
            if not media:
                return None
            
            return {
                'id': media.id,
                'hash': media.file_hash,
                'filename': media.filename,
                'product_id': media.product_id,
                'duration': media.duration,
                'created_at': media.created_at.isoformat() if media.created_at else None,
            }
            
        finally:
            session.close()


# Singleton getter
_video_service: Optional[VideoService] = None


def get_video_service() -> VideoService:
    """Get global VideoService instance."""
    global _video_service
    if _video_service is None:
        _video_service = VideoService()
    return _video_service
