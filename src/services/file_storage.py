"""
Enhanced File Storage Service for AI Agent Platform.
Provides agent-isolated storage with UUID-based filenames and organized directory structure.
"""

import os
import uuid
import shutil
import logging
from typing import Optional, Dict, Any, Tuple, List
from pathlib import Path
import tempfile
import hashlib
from datetime import datetime

from src.config.document_processing import config

logger = logging.getLogger(__name__)


class FileStorageError(Exception):
    """Custom exception for file storage errors."""
    pass


class FileStorageService:
    """Enhanced file storage service with agent isolation."""
    
    def __init__(self):
        self.base_documents_path = Path(config.DOCUMENTS_BASE_PATH)
        self.base_vector_path = Path(config.VECTOR_STORE_PATH)
        
        # Ensure base directories exist
        self.base_documents_path.mkdir(parents=True, exist_ok=True)
        self.base_vector_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"File storage initialized:")
        logger.info(f"  Documents path: {self.base_documents_path}")
        logger.info(f"  Vector path: {self.base_vector_path}")
    
    def get_agent_paths(self, agent_id: int) -> Tuple[Path, Path]:
        """Get agent-specific storage paths."""
        docs_path = self.base_documents_path / f"agent_{agent_id}"
        vector_path = self.base_vector_path / f"agent_{agent_id}"
        
        # Create agent directories if they don't exist
        docs_path.mkdir(parents=True, exist_ok=True)
        vector_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (docs_path / "documents").mkdir(exist_ok=True)
        (docs_path / "temp").mkdir(exist_ok=True)
        (docs_path / "backups").mkdir(exist_ok=True)
        
        return docs_path, vector_path
    
    def generate_unique_filename(
        self, 
        original_filename: str, 
        content_hash: str,
        agent_id: int
    ) -> str:
        """
        Generate a unique filename using UUID and content hash.
        
        Args:
            original_filename: Original file name
            content_hash: SHA-256 hash of file content
            agent_id: Agent ID for isolation
            
        Returns:
            Unique filename with format: {uuid}_{hash_prefix}_{sanitized_original}.{ext}
        """
        # Extract file extension
        file_path = Path(original_filename)
        file_ext = file_path.suffix.lower()
        base_name = file_path.stem
        
        # Sanitize base name (remove special characters)
        sanitized_name = "".join(c for c in base_name if c.isalnum() or c in ('-', '_', ' ')).strip()
        sanitized_name = sanitized_name.replace(' ', '_')[:50]  # Limit length
        
        # Generate UUID
        file_uuid = str(uuid.uuid4())[:8]  # Short UUID
        
        # Use first 8 characters of content hash
        hash_prefix = content_hash[:8]
        
        # Create unique filename
        unique_filename = f"{file_uuid}_{hash_prefix}_{sanitized_name}{file_ext}"
        
        return unique_filename
    
    def store_document_file(
        self,
        agent_id: int,
        file_content: bytes,
        original_filename: str,
        content_hash: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Store document file in agent-specific directory.
        
        Args:
            agent_id: Agent ID
            file_content: File content as bytes
            original_filename: Original filename
            content_hash: Content hash for deduplication
            metadata: Optional metadata
            
        Returns:
            Storage result with file path and metadata
        """
        try:
            docs_path, _ = self.get_agent_paths(agent_id)
            
            # Generate unique filename
            unique_filename = self.generate_unique_filename(
                original_filename, content_hash, agent_id
            )
            
            # Full file path
            file_path = docs_path / "documents" / unique_filename
            
            # Check if file already exists (shouldn't happen with UUID, but safety check)
            if file_path.exists():
                logger.warning(f"File already exists: {file_path}")
                # Add timestamp to make it unique
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                name_parts = unique_filename.rsplit('.', 1)
                if len(name_parts) == 2:
                    unique_filename = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
                else:
                    unique_filename = f"{unique_filename}_{timestamp}"
                file_path = docs_path / "documents" / unique_filename
            
            # Write file
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Create metadata file
            metadata_path = file_path.with_suffix(file_path.suffix + '.meta')
            file_metadata = {
                "original_filename": original_filename,
                "stored_filename": unique_filename,
                "content_hash": content_hash,
                "file_size": len(file_content),
                "stored_at": datetime.now().isoformat(),
                "agent_id": agent_id,
                "custom_metadata": metadata or {}
            }
            
            import json
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(file_metadata, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ File stored successfully:")
            logger.info(f"  Original: {original_filename}")
            logger.info(f"  Stored as: {unique_filename}")
            logger.info(f"  Path: {file_path}")
            logger.info(f"  Size: {len(file_content)} bytes")
            
            return {
                "success": True,
                "file_path": str(file_path),
                "relative_path": f"agent_{agent_id}/documents/{unique_filename}",
                "unique_filename": unique_filename,
                "metadata_path": str(metadata_path),
                "file_size": len(file_content),
                "metadata": file_metadata
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to store file {original_filename}: {e}")
            raise FileStorageError(f"Failed to store file: {str(e)}")
    
    def retrieve_document_file(
        self, 
        agent_id: int, 
        relative_path: str
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Retrieve document file and metadata.
        
        Args:
            agent_id: Agent ID
            relative_path: Relative path to file
            
        Returns:
            Tuple of (file_content, metadata)
        """
        try:
            docs_path, _ = self.get_agent_paths(agent_id)
            
            # Construct full path
            if relative_path.startswith(f"agent_{agent_id}/"):
                # Remove agent prefix if present
                relative_path = relative_path[len(f"agent_{agent_id}/"):]
            
            file_path = docs_path / relative_path
            
            if not file_path.exists():
                raise FileStorageError(f"File not found: {relative_path}")
            
            # Read file content
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # Read metadata if available
            metadata_path = file_path.with_suffix(file_path.suffix + '.meta')
            metadata = {}
            if metadata_path.exists():
                import json
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            
            return file_content, metadata
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve file {relative_path}: {e}")
            raise FileStorageError(f"Failed to retrieve file: {str(e)}")
    
    def delete_document_file(self, agent_id: int, relative_path: str) -> bool:
        """
        Delete document file and metadata.
        
        Args:
            agent_id: Agent ID
            relative_path: Relative path to file
            
        Returns:
            True if deleted successfully
        """
        try:
            docs_path, _ = self.get_agent_paths(agent_id)
            
            # Construct full path
            if relative_path.startswith(f"agent_{agent_id}/"):
                relative_path = relative_path[len(f"agent_{agent_id}/"):]
            
            file_path = docs_path / relative_path
            
            if file_path.exists():
                # Create backup before deletion
                backup_path = docs_path / "backups" / f"{file_path.name}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
                shutil.copy2(file_path, backup_path)
                
                # Delete main file
                file_path.unlink()
                
                # Delete metadata file if exists
                metadata_path = file_path.with_suffix(file_path.suffix + '.meta')
                if metadata_path.exists():
                    metadata_path.unlink()
                
                logger.info(f"✅ File deleted: {relative_path} (backup created)")
                return True
            else:
                logger.warning(f"⚠️ File not found for deletion: {relative_path}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to delete file {relative_path}: {e}")
            raise FileStorageError(f"Failed to delete file: {str(e)}")
    
    def list_agent_files(self, agent_id: int) -> List[Dict[str, Any]]:
        """
        List all files for an agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            List of file information dictionaries
        """
        try:
            docs_path, _ = self.get_agent_paths(agent_id)
            documents_path = docs_path / "documents"
            
            files = []
            if documents_path.exists():
                for file_path in documents_path.iterdir():
                    if file_path.is_file() and not file_path.name.endswith('.meta'):
                        # Get file stats
                        stat = file_path.stat()
                        
                        # Try to load metadata
                        metadata_path = file_path.with_suffix(file_path.suffix + '.meta')
                        metadata = {}
                        if metadata_path.exists():
                            import json
                            try:
                                with open(metadata_path, 'r', encoding='utf-8') as f:
                                    metadata = json.load(f)
                            except Exception:
                                pass
                        
                        files.append({
                            "filename": file_path.name,
                            "relative_path": f"documents/{file_path.name}",
                            "size": stat.st_size,
                            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "original_filename": metadata.get("original_filename", file_path.name),
                            "content_hash": metadata.get("content_hash"),
                            "metadata": metadata
                        })
            
            return sorted(files, key=lambda x: x["created_at"], reverse=True)
            
        except Exception as e:
            logger.error(f"❌ Failed to list files for agent {agent_id}: {e}")
            raise FileStorageError(f"Failed to list files: {str(e)}")
    
    def cleanup_temp_files(self, agent_id: int, max_age_hours: int = 24) -> int:
        """
        Clean up temporary files older than specified age.
        
        Args:
            agent_id: Agent ID
            max_age_hours: Maximum age in hours
            
        Returns:
            Number of files cleaned up
        """
        try:
            docs_path, _ = self.get_agent_paths(agent_id)
            temp_path = docs_path / "temp"
            
            if not temp_path.exists():
                return 0
            
            import time
            max_age_seconds = max_age_hours * 3600
            current_time = time.time()
            cleaned_count = 0
            
            for file_path in temp_path.iterdir():
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        file_path.unlink()
                        cleaned_count += 1
            
            logger.info(f"✅ Cleaned up {cleaned_count} temporary files for agent {agent_id}")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"❌ Failed to cleanup temp files for agent {agent_id}: {e}")
            return 0
    
    def get_storage_stats(self, agent_id: int) -> Dict[str, Any]:
        """
        Get storage statistics for an agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Storage statistics
        """
        try:
            docs_path, vector_path = self.get_agent_paths(agent_id)
            
            def get_directory_size(path: Path) -> int:
                """Get total size of directory."""
                total_size = 0
                if path.exists():
                    for file_path in path.rglob('*'):
                        if file_path.is_file():
                            total_size += file_path.stat().st_size
                return total_size
            
            def count_files(path: Path) -> int:
                """Count files in directory."""
                count = 0
                if path.exists():
                    for file_path in path.rglob('*'):
                        if file_path.is_file():
                            count += 1
                return count
            
            stats = {
                "agent_id": agent_id,
                "documents": {
                    "path": str(docs_path),
                    "total_size_bytes": get_directory_size(docs_path),
                    "total_files": count_files(docs_path / "documents"),
                    "temp_files": count_files(docs_path / "temp"),
                    "backup_files": count_files(docs_path / "backups")
                },
                "vectors": {
                    "path": str(vector_path),
                    "total_size_bytes": get_directory_size(vector_path),
                    "total_files": count_files(vector_path)
                }
            }
            
            # Convert bytes to human readable
            for category in ["documents", "vectors"]:
                size_bytes = stats[category]["total_size_bytes"]
                if size_bytes < 1024:
                    stats[category]["total_size_human"] = f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    stats[category]["total_size_human"] = f"{size_bytes / 1024:.1f} KB"
                elif size_bytes < 1024 * 1024 * 1024:
                    stats[category]["total_size_human"] = f"{size_bytes / (1024 * 1024):.1f} MB"
                else:
                    stats[category]["total_size_human"] = f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get storage stats for agent {agent_id}: {e}")
            raise FileStorageError(f"Failed to get storage stats: {str(e)}")


# Global storage service instance
file_storage = FileStorageService()
