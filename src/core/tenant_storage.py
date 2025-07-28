"""
Tenant-aware file storage system for multi-tenant document management.
"""

import os
import uuid
import hashlib
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TenantStorageManager:
    """
    Manages tenant-isolated file storage for documents and vectors.
    Ensures complete separation of files between tenants.
    """
    
    def __init__(self, base_storage_path: str = "./data"):
        self.base_storage_path = Path(base_storage_path)
        self.base_storage_path.mkdir(parents=True, exist_ok=True)
        
        # Storage structure:
        # ./data/
        # ├── tenant_{tenant_id}/
        # │   ├── documents/
        # │   │   └── agent_{agent_id}/
        # │   │       └── {uuid}_{filename}
        # │   ├── vectors/
        # │   │   └── agent_{agent_id}/
        # │   │       └── chroma_collection/
        # │   └── temp/
        # └── shared/
        #     └── templates/
    
    def get_tenant_base_path(self, tenant_id: str) -> Path:
        """Get the base storage path for a tenant."""
        tenant_path = self.base_storage_path / f"tenant_{tenant_id}"
        tenant_path.mkdir(parents=True, exist_ok=True)
        return tenant_path
    
    def get_tenant_documents_path(self, tenant_id: str, agent_id: int) -> Path:
        """Get the documents storage path for a tenant's agent."""
        docs_path = self.get_tenant_base_path(tenant_id) / "documents" / f"agent_{agent_id}"
        docs_path.mkdir(parents=True, exist_ok=True)
        return docs_path
    
    def get_tenant_vectors_path(self, tenant_id: str, agent_id: int) -> Path:
        """Get the vector storage path for a tenant's agent."""
        vectors_path = self.get_tenant_base_path(tenant_id) / "vectors" / f"agent_{agent_id}"
        vectors_path.mkdir(parents=True, exist_ok=True)
        return vectors_path
    
    def get_tenant_temp_path(self, tenant_id: str) -> Path:
        """Get the temporary storage path for a tenant."""
        temp_path = self.get_tenant_base_path(tenant_id) / "temp"
        temp_path.mkdir(parents=True, exist_ok=True)
        return temp_path
    
    def store_document_file(
        self,
        tenant_id: str,
        agent_id: int,
        file_content: bytes,
        original_filename: str,
        content_hash: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Store a document file with tenant isolation.
        
        Returns:
            Dict containing storage information including paths and metadata.
        """
        try:
            # Get tenant-specific storage path
            storage_path = self.get_tenant_documents_path(tenant_id, agent_id)
            
            # Generate unique filename
            file_extension = Path(original_filename).suffix
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = storage_path / unique_filename
            
            # Store the file
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Create relative path for database storage
            relative_path = f"tenant_{tenant_id}/documents/agent_{agent_id}/{unique_filename}"
            
            # Prepare storage result
            storage_result = {
                "success": True,
                "unique_filename": unique_filename,
                "relative_path": relative_path,
                "absolute_path": str(file_path),
                "file_size": len(file_content),
                "content_hash": content_hash,
                "original_filename": original_filename,
                "tenant_id": tenant_id,
                "agent_id": agent_id,
                "stored_at": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            logger.info(f"Document stored successfully: {relative_path}")
            return storage_result
            
        except Exception as e:
            logger.error(f"Failed to store document for tenant {tenant_id}: {e}")
            raise
    
    def get_document_file(
        self,
        tenant_id: str,
        relative_path: str
    ) -> Optional[bytes]:
        """
        Retrieve a document file with tenant validation.
        
        Args:
            tenant_id: The tenant ID requesting the file
            relative_path: The relative path stored in the database
            
        Returns:
            File content as bytes, or None if not found or access denied
        """
        try:
            # Validate that the path belongs to the requesting tenant
            if not relative_path.startswith(f"tenant_{tenant_id}/"):
                logger.warning(f"Cross-tenant file access attempt: {tenant_id} -> {relative_path}")
                return None
            
            # Construct absolute path
            absolute_path = self.base_storage_path / relative_path
            
            # Check if file exists and is within tenant boundaries
            if not absolute_path.exists():
                logger.warning(f"File not found: {absolute_path}")
                return None
            
            # Additional security check - ensure resolved path is still within tenant directory
            tenant_base = self.get_tenant_base_path(tenant_id)
            try:
                absolute_path.resolve().relative_to(tenant_base.resolve())
            except ValueError:
                logger.error(f"Path traversal attempt detected: {relative_path}")
                return None
            
            # Read and return file content
            with open(absolute_path, 'rb') as f:
                return f.read()
                
        except Exception as e:
            logger.error(f"Failed to retrieve document for tenant {tenant_id}: {e}")
            return None
    
    def delete_document_file(
        self,
        tenant_id: str,
        relative_path: str
    ) -> bool:
        """
        Delete a document file with tenant validation.
        
        Args:
            tenant_id: The tenant ID requesting the deletion
            relative_path: The relative path stored in the database
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # Validate that the path belongs to the requesting tenant
            if not relative_path.startswith(f"tenant_{tenant_id}/"):
                logger.warning(f"Cross-tenant file deletion attempt: {tenant_id} -> {relative_path}")
                return False
            
            # Construct absolute path
            absolute_path = self.base_storage_path / relative_path
            
            # Additional security check
            tenant_base = self.get_tenant_base_path(tenant_id)
            try:
                absolute_path.resolve().relative_to(tenant_base.resolve())
            except ValueError:
                logger.error(f"Path traversal attempt in deletion: {relative_path}")
                return False
            
            # Delete file if it exists
            if absolute_path.exists():
                absolute_path.unlink()
                logger.info(f"Document deleted: {relative_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {relative_path}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete document for tenant {tenant_id}: {e}")
            return False
    
    def list_tenant_documents(
        self,
        tenant_id: str,
        agent_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List all documents for a tenant, optionally filtered by agent.
        
        Args:
            tenant_id: The tenant ID
            agent_id: Optional agent ID to filter by
            
        Returns:
            List of document information dictionaries
        """
        try:
            documents = []
            tenant_docs_path = self.get_tenant_base_path(tenant_id) / "documents"
            
            if not tenant_docs_path.exists():
                return documents
            
            # If agent_id specified, only check that agent's folder
            if agent_id:
                agent_paths = [tenant_docs_path / f"agent_{agent_id}"]
            else:
                # Get all agent folders
                agent_paths = [p for p in tenant_docs_path.iterdir() if p.is_dir() and p.name.startswith("agent_")]
            
            for agent_path in agent_paths:
                if not agent_path.exists():
                    continue
                
                extracted_agent_id = int(agent_path.name.replace("agent_", ""))
                
                for file_path in agent_path.iterdir():
                    if file_path.is_file():
                        relative_path = f"tenant_{tenant_id}/documents/{agent_path.name}/{file_path.name}"
                        
                        documents.append({
                            "filename": file_path.name,
                            "relative_path": relative_path,
                            "absolute_path": str(file_path),
                            "agent_id": extracted_agent_id,
                            "file_size": file_path.stat().st_size,
                            "modified_at": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                        })
            
            return documents
            
        except Exception as e:
            logger.error(f"Failed to list documents for tenant {tenant_id}: {e}")
            return []
    
    def get_tenant_storage_stats(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get storage statistics for a tenant.
        
        Args:
            tenant_id: The tenant ID
            
        Returns:
            Dictionary with storage statistics
        """
        try:
            tenant_path = self.get_tenant_base_path(tenant_id)
            
            if not tenant_path.exists():
                return {
                    "total_size_bytes": 0,
                    "total_files": 0,
                    "documents_count": 0,
                    "agents_count": 0
                }
            
            total_size = 0
            total_files = 0
            documents_count = 0
            agents_set = set()
            
            # Walk through all files in tenant directory
            for file_path in tenant_path.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    total_files += 1
                    
                    # Count documents and track agents
                    if "documents" in file_path.parts:
                        documents_count += 1
                        # Extract agent ID from path
                        for part in file_path.parts:
                            if part.startswith("agent_"):
                                agents_set.add(part)
            
            return {
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "total_files": total_files,
                "documents_count": documents_count,
                "agents_count": len(agents_set)
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage stats for tenant {tenant_id}: {e}")
            return {
                "total_size_bytes": 0,
                "total_files": 0,
                "documents_count": 0,
                "agents_count": 0,
                "error": str(e)
            }
    
    def cleanup_tenant_data(self, tenant_id: str) -> bool:
        """
        Clean up all data for a tenant (use with caution).
        
        Args:
            tenant_id: The tenant ID to clean up
            
        Returns:
            True if cleanup was successful, False otherwise
        """
        try:
            tenant_path = self.get_tenant_base_path(tenant_id)
            
            if tenant_path.exists():
                shutil.rmtree(tenant_path)
                logger.info(f"Tenant data cleaned up: {tenant_id}")
                return True
            else:
                logger.info(f"No data found for tenant: {tenant_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to cleanup tenant data {tenant_id}: {e}")
            return False


# Global instance
_storage_manager = None

def get_tenant_storage_manager() -> TenantStorageManager:
    """Get the global tenant storage manager instance."""
    global _storage_manager
    if _storage_manager is None:
        base_path = os.getenv("KNOWLEDGE_BASE_STORAGE_PATH", "./data")
        _storage_manager = TenantStorageManager(base_path)
    return _storage_manager
