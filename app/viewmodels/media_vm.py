"""
MediaVM - Media ViewModel for MediaVerse
Handles media import, folder scanning, and duplicate detection using SHA256.

Supports:
- Drag & Drop folder import
- SHA256 hash-based duplicate detection
- Graceful handling of duplicates (skip, don't error)
"""

import hashlib
import mimetypes
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import and_

from app.core.database import (
    get_db, DatabaseManager,
    MediaAsset, Product, Category
)
from app.core.event_bus import get_event_bus
from app.core.log_orchestrator import get_log_orchestrator
from app.core.error_orchestrator import get_error_orchestrator, ErrorCategory, ErrorSeverity


# Supported video extensions
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}


@dataclass
class ImportResult:
    """Result of a file import operation."""
    filename: str
    file_path: str
    status: str  # 'imported', 'duplicate', 'error', 'skipped'
    message: str
    media_id: Optional[int] = None
    file_hash: Optional[str] = None


@dataclass
class FolderImportResult:
    """Result of a folder import operation."""
    folder_path: str
    total_files: int = 0
    imported: int = 0
    duplicates: int = 0
    errors: int = 0
    skipped: int = 0
    results: List[ImportResult] = field(default_factory=list)
    
    @property
    def summary(self) -> str:
        return (
            f"Imported: {self.imported}, "
            f"Duplicates (skipped): {self.duplicates}, "
            f"Errors: {self.errors}, "
            f"Skipped (non-video): {self.skipped}"
        )


class MediaVM:
    """
    Media ViewModel - Manages media assets with duplicate detection.
    
    Features:
    - Folder scanning for video files
    - SHA256 hash-based duplicate detection
    - Graceful duplicate handling (skip and report, no errors)
    - Product association
    """
    
    _instance: Optional['MediaVM'] = None
    
    # EventBus topics
    TOPIC_MEDIA_IMPORTED = "media/imported"
    TOPIC_MEDIA_DUPLICATE = "media/duplicate"
    TOPIC_MEDIA_ERROR = "media/error"
    TOPIC_FOLDER_IMPORT_START = "media/folder_import_start"
    TOPIC_FOLDER_IMPORT_COMPLETE = "media/folder_import_complete"
    TOPIC_IMPORT_PROGRESS = "media/import_progress"
    
    def __new__(cls) -> 'MediaVM':
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
        self._initialized = True
        
        self._log.info("MediaVM initialized with SHA256 duplicate detection")
    
    # ========================================================================
    # SHA256 Hashing
    # ========================================================================
    
    def calculate_file_hash(self, file_path: str, chunk_size: int = 8192) -> str:
        """
        Calculate SHA256 hash of a file.
        
        Args:
            file_path: Path to the file
            chunk_size: Size of chunks to read (for memory efficiency)
            
        Returns:
            SHA256 hash as hexadecimal string
        """
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    # ========================================================================
    # Duplicate Detection
    # ========================================================================
    
    def check_duplicate(self, file_hash: str) -> Optional[MediaAsset]:
        """
        Check if a file with this hash already exists.
        
        Args:
            file_hash: SHA256 hash to check
            
        Returns:
            Existing MediaAsset if duplicate, None otherwise
        """
        session = self._db.get_session()
        try:
            return session.query(MediaAsset).filter(
                MediaAsset.file_hash == file_hash
            ).first()
        finally:
            session.close()
    
    def is_duplicate(self, file_path: str) -> Tuple[bool, str, Optional[MediaAsset]]:
        """
        Check if a file is a duplicate.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (is_duplicate, file_hash, existing_asset or None)
        """
        file_hash = self.calculate_file_hash(file_path)
        existing = self.check_duplicate(file_hash)
        return existing is not None, file_hash, existing
    
    # ========================================================================
    # Single File Import
    # ========================================================================
    
    def import_media(
        self,
        file_path: str,
        product_id: Optional[int] = None,
        skip_duplicates: bool = True
    ) -> ImportResult:
        """
        Import a single media file.
        
        Args:
            file_path: Path to the media file
            product_id: Optional product to associate with
            skip_duplicates: If True, skip duplicates silently; if False, return error
            
        Returns:
            ImportResult with status and details
        """
        file_path = os.path.abspath(file_path)
        filename = os.path.basename(file_path)
        
        # Check file exists
        if not os.path.exists(file_path):
            return ImportResult(
                filename=filename,
                file_path=file_path,
                status='error',
                message=f"File not found: {file_path}"
            )
        
        # Check extension
        ext = os.path.splitext(filename)[1].lower()
        if ext not in VIDEO_EXTENSIONS:
            return ImportResult(
                filename=filename,
                file_path=file_path,
                status='skipped',
                message=f"Not a video file: {ext}"
            )
        
        try:
            # Calculate hash and check duplicate
            is_dup, file_hash, existing = self.is_duplicate(file_path)
            
            if is_dup:
                self._log.debug(f"Duplicate detected: {filename} (hash: {file_hash[:16]}...)")
                self._event_bus.publish(self.TOPIC_MEDIA_DUPLICATE, {
                    'filename': filename,
                    'file_hash': file_hash,
                    'existing_id': existing.id if existing else None
                }, source='MediaVM')
                
                if skip_duplicates:
                    return ImportResult(
                        filename=filename,
                        file_path=file_path,
                        status='duplicate',
                        message=f"Already exists as ID {existing.id}",
                        media_id=existing.id,
                        file_hash=file_hash
                    )
                else:
                    return ImportResult(
                        filename=filename,
                        file_path=file_path,
                        status='error',
                        message=f"Duplicate file (ID: {existing.id})",
                        file_hash=file_hash
                    )
            
            # Get file info
            file_size = os.path.getsize(file_path)
            mime_type, _ = mimetypes.guess_type(file_path)
            
            # Create database entry
            session = self._db.get_session()
            try:
                asset = MediaAsset(
                    product_id=product_id,
                    filename=filename,
                    file_path=file_path,
                    file_hash=file_hash,
                    file_size=file_size,
                    mime_type=mime_type or "video/mp4"
                )
                session.add(asset)
                session.commit()
                
                self._log.info(f"Imported media: {filename} (ID: {asset.id})")
                self._event_bus.publish(self.TOPIC_MEDIA_IMPORTED, {
                    'media_id': asset.id,
                    'filename': filename,
                    'file_hash': file_hash,
                    'product_id': product_id
                }, source='MediaVM')
                
                return ImportResult(
                    filename=filename,
                    file_path=file_path,
                    status='imported',
                    message='Successfully imported',
                    media_id=asset.id,
                    file_hash=file_hash
                )
                
            except Exception as e:
                session.rollback()
                raise
            finally:
                session.close()
                
        except Exception as e:
            self._error.handle_error(e, ErrorCategory.FILE_IO, ErrorSeverity.MEDIUM)
            self._event_bus.publish(self.TOPIC_MEDIA_ERROR, {
                'filename': filename,
                'error': str(e)
            }, source='MediaVM')
            
            return ImportResult(
                filename=filename,
                file_path=file_path,
                status='error',
                message=str(e)
            )
    
    # ========================================================================
    # Folder Import (Drag & Drop support)
    # ========================================================================
    
    def import_folder(
        self,
        folder_path: str,
        product_id: Optional[int] = None,
        recursive: bool = True,
        skip_duplicates: bool = True,
        progress_callback: Optional[callable] = None
    ) -> FolderImportResult:
        """
        Import all video files from a folder.
        
        Supports drag & drop of entire folders.
        Automatically skips non-video files and duplicates.
        
        Args:
            folder_path: Path to the folder
            product_id: Optional product to associate all files with
            recursive: If True, scan subdirectories
            skip_duplicates: If True, skip duplicates silently
            progress_callback: Optional callback(current, total, filename)
            
        Returns:
            FolderImportResult with summary and details
        """
        folder_path = os.path.abspath(folder_path)
        result = FolderImportResult(folder_path=folder_path)
        
        if not os.path.isdir(folder_path):
            self._log.error(f"Not a directory: {folder_path}")
            return result
        
        self._log.info(f"Starting folder import: {folder_path}")
        self._event_bus.publish(self.TOPIC_FOLDER_IMPORT_START, {
            'folder_path': folder_path,
            'recursive': recursive
        }, source='MediaVM')
        
        # Collect all video files
        video_files: List[str] = []
        
        if recursive:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in VIDEO_EXTENSIONS:
                        video_files.append(os.path.join(root, file))
        else:
            for file in os.listdir(folder_path):
                ext = os.path.splitext(file)[1].lower()
                if ext in VIDEO_EXTENSIONS:
                    video_files.append(os.path.join(folder_path, file))
        
        result.total_files = len(video_files)
        self._log.info(f"Found {len(video_files)} video files")
        
        # Import each file
        for i, file_path in enumerate(video_files):
            # Progress callback
            if progress_callback:
                progress_callback(i + 1, len(video_files), os.path.basename(file_path))
            
            # Publish progress
            self._event_bus.publish(self.TOPIC_IMPORT_PROGRESS, {
                'current': i + 1,
                'total': len(video_files),
                'filename': os.path.basename(file_path),
                'percent': int((i + 1) / len(video_files) * 100)
            }, source='MediaVM')
            
            # Import file
            import_result = self.import_media(file_path, product_id, skip_duplicates)
            result.results.append(import_result)
            
            # Update counts
            if import_result.status == 'imported':
                result.imported += 1
            elif import_result.status == 'duplicate':
                result.duplicates += 1
            elif import_result.status == 'error':
                result.errors += 1
            else:
                result.skipped += 1
        
        self._log.info(f"Folder import complete: {result.summary}")
        self._event_bus.publish(self.TOPIC_FOLDER_IMPORT_COMPLETE, {
            'folder_path': folder_path,
            'imported': result.imported,
            'duplicates': result.duplicates,
            'errors': result.errors,
            'summary': result.summary
        }, source='MediaVM')
        
        return result
    
    # ========================================================================
    # Query Methods
    # ========================================================================
    
    def get_all_media(self, limit: int = 1000) -> List[MediaAsset]:
        """Get all media assets."""
        session = self._db.get_session()
        try:
            return session.query(MediaAsset).limit(limit).all()
        finally:
            session.close()
    
    def get_media_by_product(self, product_id: int) -> List[MediaAsset]:
        """Get all media assets for a product."""
        session = self._db.get_session()
        try:
            return session.query(MediaAsset).filter(
                MediaAsset.product_id == product_id
            ).all()
        finally:
            session.close()
    
    def get_media_by_hash(self, file_hash: str) -> Optional[MediaAsset]:
        """Get media asset by SHA256 hash."""
        return self.check_duplicate(file_hash)
    
    def get_media_by_id(self, media_id: int) -> Optional[MediaAsset]:
        """Get media asset by ID."""
        session = self._db.get_session()
        try:
            return session.query(MediaAsset).filter(
                MediaAsset.id == media_id
            ).first()
        finally:
            session.close()
    
    def delete_media(self, media_id: int, delete_file: bool = False) -> bool:
        """
        Delete a media asset.
        
        Args:
            media_id: ID of the media to delete
            delete_file: If True, also delete the physical file
            
        Returns:
            True if deleted successfully
        """
        session = self._db.get_session()
        try:
            asset = session.query(MediaAsset).filter(
                MediaAsset.id == media_id
            ).first()
            
            if not asset:
                return False
            
            file_path = asset.file_path
            
            session.delete(asset)
            session.commit()
            
            if delete_file and os.path.exists(file_path):
                os.remove(file_path)
            
            self._log.info(f"Deleted media: {media_id}")
            return True
            
        except Exception as e:
            session.rollback()
            self._error.handle_error(e, ErrorCategory.DATABASE, ErrorSeverity.MEDIUM)
            return False
        finally:
            session.close()
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance."""
        cls._instance = None


def get_media_vm() -> MediaVM:
    """Get the global MediaVM instance."""
    return MediaVM()
