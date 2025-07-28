"""
Enhanced Knowledge Base Manager
Combines vector search with fallback keyword search for robust document retrieval
"""

import os
import json
import hashlib
from typing import List, Optional, Dict, Any
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, insert, update, delete
from pydantic import BaseModel

# Local imports
from .knowledge_base import (
    KnowledgeBaseDocument, 
    KnowledgeBaseSearchRequest, 
    KnowledgeBaseSearchResult,
    KnowledgeBaseManager  # Original manager for fallback
)
from .vector_knowledge_base import VectorKnowledgeBaseManager


class EnhancedKnowledgeBaseManager:
    """
    Enhanced knowledge base manager that combines:
    1. Vector-based semantic search (primary)
    2. Keyword-based search (fallback)
    3. Multi-tenant document isolation
    """

    def __init__(self, agent_id: int, tenant_id: str = None):
        self.agent_id = agent_id
        self.tenant_id = tenant_id

        # Initialize both managers with tenant support
        self.vector_manager = VectorKnowledgeBaseManager(agent_id)
        self.keyword_manager = KnowledgeBaseManager(agent_id, tenant_id)

        # Tenant-aware storage managers
        from src.core.tenant_storage import get_tenant_storage_manager
        from src.core.tenant_vector_store import get_tenant_vector_store_manager

        self.storage_manager = get_tenant_storage_manager()
        self.vector_store_manager = get_tenant_vector_store_manager()
    
    async def add_document(
        self,
        db: AsyncSession,
        title: str,
        content: str,
        content_type: str = "text",
        file_path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tenant_id: str = None
    ) -> Optional[KnowledgeBaseDocument]:
        """Add a document to the knowledge base with tenant isolation and vector processing"""

        # Use provided tenant_id or instance tenant_id
        effective_tenant_id = tenant_id or self.tenant_id
        if not effective_tenant_id:
            raise ValueError("Tenant ID is required for document operations")

        try:
            print(f"📝 Adding document for tenant {effective_tenant_id}: {title}")

            # First, add to traditional knowledge base with tenant support
            document = await self.keyword_manager.add_document(
                db=db,
                title=title,
                content=content,
                content_type=content_type,
                metadata=metadata,
                tenant_id=effective_tenant_id
            )
            
            if not document:
                print(f"❌ Failed to add document to traditional KB: {title}")
                return None
            
            # Process with vector manager if available
            if self.vector_manager.is_available():
                success = await self.vector_manager.process_document(
                    db=db,
                    document=document,
                    file_path=file_path
                )
                
                if success:
                    print(f"✅ Document processed with vector embeddings: {title}")
                else:
                    print(f"⚠️ Vector processing failed, but document saved: {title}")
            else:
                print(f"⚠️ Vector processing not available, using keyword-only: {title}")
            
            return document
            
        except Exception as e:
            print(f"❌ Error adding document {title}: {e}")
            return None
    
    async def search_documents(
        self,
        db: AsyncSession,
        search_request: KnowledgeBaseSearchRequest,
        tenant_id: str = None
    ) -> List[KnowledgeBaseSearchResult]:
        """Search documents using vector search with keyword fallback and tenant isolation"""

        # Use provided tenant_id or instance tenant_id
        effective_tenant_id = tenant_id or self.tenant_id
        if not effective_tenant_id:
            raise ValueError("Tenant ID is required for document search")

        print(f"🔍 Enhanced search for tenant {effective_tenant_id}: {search_request.query}")

        # Try vector search first with tenant isolation
        if self.vector_manager.is_available():
            try:
                # Use tenant-aware vector search
                vector_results = self.vector_store_manager.search_vector_store(
                    tenant_id=effective_tenant_id,
                    agent_id=self.agent_id,
                    query=search_request.query,
                    k=search_request.limit
                )

                if vector_results:
                    print(f"✅ Vector search found {len(vector_results)} results")
                    # Convert to KnowledgeBaseSearchResult format
                    formatted_results = []
                    for result in vector_results:
                        formatted_results.append(KnowledgeBaseSearchResult(
                            document_id=0,  # Vector results don't have DB IDs
                            title=result.get("metadata", {}).get("title", "Vector Result"),
                            content_snippet=result["content"][:500],
                            relevance_score=result["similarity_score"],
                            content_type=result.get("metadata", {}).get("content_type", "text"),
                            metadata=result.get("metadata", {})
                        ))
                    return formatted_results
                else:
                    print("⚠️ Vector search returned no results, trying keyword search")
            except Exception as e:
                print(f"⚠️ Vector search failed: {e}, falling back to keyword search")

        # Fallback to keyword search with tenant isolation
        try:
            keyword_results = await self.keyword_manager.search_documents(
                db, search_request, effective_tenant_id
            )
            print(f"🔍 Keyword search found {len(keyword_results)} results")
            return keyword_results
        except Exception as e:
            print(f"❌ Both vector and keyword search failed: {e}")
            return []
    
    async def upload_pdf_document(
        self,
        db: AsyncSession,
        title: str,
        file_content: bytes,
        filename: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[KnowledgeBaseDocument]:
        """Upload and process a PDF document"""
        
        try:
            print(f"📄 Uploading PDF: {filename}")
            
            # Save file to disk
            file_path = self.docs_path / filename
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Extract text content for traditional storage
            if self.vector_manager.is_available():
                try:
                    # Use vector manager's PDF extraction
                    pages = self.vector_manager._extract_text_from_pdf(str(file_path))
                    content = "\n\n".join(pages)
                except Exception as e:
                    print(f"⚠️ PDF extraction failed: {e}")
                    content = f"PDF document: {filename}"
            else:
                # Fallback content
                content = f"PDF document: {filename} (content extraction not available)"
            
            # Add document with PDF processing
            document = await self.add_document(
                db=db,
                title=title,
                content=content,
                content_type="application/pdf",
                file_path=str(file_path),
                metadata=metadata or {}
            )
            
            if document:
                print(f"✅ PDF document uploaded successfully: {filename}")
            
            return document
            
        except Exception as e:
            print(f"❌ Error uploading PDF {filename}: {e}")
            return None
    
    async def delete_document(
        self,
        db: AsyncSession,
        document_id: int
    ) -> bool:
        """Delete a document from both vector and traditional storage"""
        
        try:
            print(f"🗑️ Deleting document: {document_id}")
            
            # Delete from vector store
            if self.vector_manager.is_available():
                await self.vector_manager.delete_document_vectors(document_id)
            
            # Delete from traditional storage
            success = await self.keyword_manager.delete_document(db, document_id)
            
            if success:
                print(f"✅ Document deleted successfully: {document_id}")
            
            return success
            
        except Exception as e:
            print(f"❌ Error deleting document {document_id}: {e}")
            return False
    
    async def list_documents(
        self,
        db: AsyncSession,
        limit: int = 50
    ) -> List[KnowledgeBaseDocument]:
        """List all documents in the knowledge base"""
        
        return await self.keyword_manager.list_documents(db, limit)
    
    async def get_document(
        self,
        db: AsyncSession,
        document_id: int
    ) -> Optional[KnowledgeBaseDocument]:
        """Get a specific document by ID"""
        
        return await self.keyword_manager.get_document(db, document_id)
    
    async def update_document(
        self,
        db: AsyncSession,
        document_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[KnowledgeBaseDocument]:
        """Update a document and reprocess vectors if needed"""
        
        try:
            print(f"📝 Updating document: {document_id}")
            
            # Update in traditional storage
            document = await self.keyword_manager.update_document(
                db=db,
                document_id=document_id,
                title=title,
                content=content,
                metadata=metadata
            )
            
            if not document:
                return None
            
            # Reprocess vectors if content changed
            if content is not None and self.vector_manager.is_available():
                # Delete old vectors
                await self.vector_manager.delete_document_vectors(document_id)
                
                # Create new vectors
                await self.vector_manager.process_document(db, document)
                print(f"✅ Document vectors updated: {document_id}")
            
            return document
            
        except Exception as e:
            print(f"❌ Error updating document {document_id}: {e}")
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get the status of the knowledge base system"""
        
        return {
            "agent_id": self.agent_id,
            "vector_search_available": self.vector_manager.is_available(),
            "keyword_search_available": True,
            "docs_path": str(self.docs_path),
            "vector_collection": self.vector_manager.collection_name
        }


# Factory function for easy integration
def create_knowledge_base_manager(agent_id: int, tenant_id: str = None) -> EnhancedKnowledgeBaseManager:
    """Create an enhanced knowledge base manager for an agent with tenant support"""
    return EnhancedKnowledgeBaseManager(agent_id, tenant_id)
