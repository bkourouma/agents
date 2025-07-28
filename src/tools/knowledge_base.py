"""
Knowledge Base Tool for AI Agent Platform.
Provides document storage, retrieval, and search capabilities.
Enhanced with vector search and semantic retrieval.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, select, and_, Index

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import hashlib
import json
import numpy as np

from src.core.database import Base


class KnowledgeBaseDocument(Base):
    """Knowledge base document model with multi-tenant support."""

    __tablename__ = "knowledge_base_documents"

    id = Column(Integer, primary_key=True, index=True)

    # Multi-tenant support
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)

    # Agent relationship
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)

    # Document information
    title = Column(String(500), nullable=False, index=True)
    content = Column(Text, nullable=False)
    content_type = Column(String(50), nullable=False, default="text", index=True)  # text, pdf, docx, etc.
    file_path = Column(String(1000), nullable=True)  # Tenant-specific file path
    content_hash = Column(String(64), nullable=False, index=True)  # SHA-256 hash for deduplication
    doc_metadata = Column(Text, nullable=True)  # JSON metadata

    # Status and timestamps
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Table constraints and indexes for multi-tenant optimization
    __table_args__ = (
        Index('idx_kb_docs_tenant_agent', 'tenant_id', 'agent_id'),
        Index('idx_kb_docs_tenant_active', 'tenant_id', 'is_active'),
        Index('idx_kb_docs_tenant_type', 'tenant_id', 'content_type'),
        Index('idx_kb_docs_tenant_hash', 'tenant_id', 'content_hash'),
        Index('idx_kb_docs_created_at', 'created_at'),
    )

    # Relationships
    tenant = relationship("Tenant")
    agent = relationship("Agent")


# Pydantic models
class KnowledgeBaseDocumentCreate(BaseModel):
    """Create knowledge base document."""
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    content_type: str = Field(default="text", max_length=50)
    metadata: Optional[Dict[str, Any]] = None


class KnowledgeBaseDocumentResponse(BaseModel):
    """Knowledge base document response."""
    id: int
    agent_id: int
    title: str
    content: str
    content_type: str
    file_path: Optional[str]
    content_hash: str
    doc_metadata: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class KnowledgeBaseSearchRequest(BaseModel):
    """Knowledge base search request."""
    query: str = Field(..., min_length=1, max_length=1000)
    limit: int = Field(default=10, ge=1, le=20)
    content_types: Optional[List[str]] = None


class KnowledgeBaseSearchResult(BaseModel):
    """Knowledge base search result."""
    document_id: int
    title: str
    content_snippet: str
    relevance_score: float
    content_type: str
    metadata: Optional[Dict[str, Any]] = None


class KnowledgeBaseTool:
    """Knowledge base tool implementation with multi-tenant support."""

    def __init__(self, agent_id: int, tenant_id: str = None):
        self.agent_id = agent_id
        self.tenant_id = tenant_id
    
    @staticmethod
    def generate_content_hash(content: str) -> str:
        """Generate SHA-256 hash of content for deduplication."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    @staticmethod
    def _safe_parse_metadata(doc_metadata: str) -> Optional[Dict[str, Any]]:
        """Safely parse metadata that might be in Python dict format or JSON format."""
        if not doc_metadata:
            return None

        try:
            # First try JSON parsing
            return json.loads(doc_metadata)
        except json.JSONDecodeError:
            try:
                # If JSON fails, try evaluating as Python literal (safer than eval)
                import ast
                return ast.literal_eval(doc_metadata)
            except (ValueError, SyntaxError):
                # If both fail, return None
                print(f"⚠️ Could not parse metadata: {doc_metadata[:100]}...")
                return None
    
    async def add_document(
        self,
        db,
        document: KnowledgeBaseDocumentCreate,
        tenant_id: str = None
    ) -> KnowledgeBaseDocument:
        """Add a document to the knowledge base with tenant isolation."""
        # Use provided tenant_id or instance tenant_id
        effective_tenant_id = tenant_id or self.tenant_id
        if not effective_tenant_id:
            raise ValueError("Tenant ID is required for document operations")

        content_hash = self.generate_content_hash(document.content)

        # Check for duplicates within tenant and agent
        existing = await db.execute(
            select(KnowledgeBaseDocument).where(
                and_(
                    KnowledgeBaseDocument.tenant_id == effective_tenant_id,
                    KnowledgeBaseDocument.agent_id == self.agent_id,
                    KnowledgeBaseDocument.content_hash == content_hash,
                    KnowledgeBaseDocument.is_active == True
                )
            )
        )

        if existing.scalar_one_or_none():
            raise ValueError("Document with identical content already exists in this tenant")

        # Create new document with tenant isolation
        db_document = KnowledgeBaseDocument(
            tenant_id=effective_tenant_id,
            agent_id=self.agent_id,
            title=document.title,
            content=document.content,
            content_type=document.content_type,
            content_hash=content_hash,
            doc_metadata=str(document.metadata) if document.metadata else None
        )
        
        db.add(db_document)
        await db.commit()
        await db.refresh(db_document)
        return db_document
    
    async def search_documents(
        self,
        db,
        search_request: KnowledgeBaseSearchRequest,
        tenant_id: str = None
    ) -> List[KnowledgeBaseSearchResult]:
        """Search documents in the knowledge base with tenant isolation."""
        # Use provided tenant_id or instance tenant_id
        effective_tenant_id = tenant_id or self.tenant_id
        if not effective_tenant_id:
            raise ValueError("Tenant ID is required for document search")

        print(f"🔍 Knowledge base search for tenant {effective_tenant_id}: {search_request.query}")

        # Use simple keyword search for now (semantic search disabled)
        return await self._fallback_keyword_search(db, search_request, effective_tenant_id)

        # Semantic search code (disabled for now)
        try:
            # Import semantic search engine
            from src.tools.semantic_search import get_semantic_search_engine
            search_engine = get_semantic_search_engine()

            print(f"🔍 Semantic search for: {search_request.query}")

            # Get all active documents for this agent (select specific columns to avoid embedding column)
            result = await db.execute(
                select(
                    KnowledgeBaseDocument.id,
                    KnowledgeBaseDocument.agent_id,
                    KnowledgeBaseDocument.title,
                    KnowledgeBaseDocument.content,
                    KnowledgeBaseDocument.content_type,
                    KnowledgeBaseDocument.file_path,
                    KnowledgeBaseDocument.content_hash,
                    KnowledgeBaseDocument.doc_metadata,
                    KnowledgeBaseDocument.is_active,
                    KnowledgeBaseDocument.created_at,
                    KnowledgeBaseDocument.updated_at
                ).where(
                    and_(
                        KnowledgeBaseDocument.agent_id == self.agent_id,
                        KnowledgeBaseDocument.is_active == True
                    )
                )
            )
            documents = result.fetchall()  # Use fetchall() for tuple results
            print(f"🔍 Found {len(documents)} documents in database")

            if not documents:
                return []

            # Prepare documents for semantic search
            doc_data = []
            embeddings_list = []

            for doc in documents:
                # Generate embedding for each document
                print(f"🔍 Generating embedding for document: {doc.title if hasattr(doc, 'title') else doc[2]}")

                # Handle both ORM objects and tuple results
                if hasattr(doc, 'title'):
                    # ORM object
                    content = doc.content
                    doc_info = {
                        'id': doc.id,
                        'title': doc.title,
                        'content': doc.content,
                        'content_type': doc.content_type,
                        'metadata': doc.doc_metadata
                    }
                else:
                    # Tuple result from select query
                    content = doc[3]  # content is at index 3
                    doc_info = {
                        'id': doc[0],
                        'title': doc[2],
                        'content': doc[3],
                        'content_type': doc[4],
                        'metadata': doc[7]
                    }

                embedding = search_engine.encode_text(content)
                doc_data.append(doc_info)
                embeddings_list.append(embedding)

            # Convert to numpy array
            document_embeddings = np.array(embeddings_list)

            # Perform semantic search
            results = search_engine.search_similar(
                query=search_request.query,
                document_embeddings=document_embeddings,
                documents=doc_data,
                top_k=search_request.limit,
                min_similarity=0.1  # Lower threshold for better recall
            )

            print(f"🔍 Semantic search found {len(results)} results")

            # Convert to KnowledgeBaseSearchResult format
            search_results = []
            for doc_data, similarity in results:
                print(f"🔍 Result: {doc_data['title']} (similarity: {similarity:.3f})")

                # Create content snippet
                snippet = self._create_snippet(doc_data['content'], search_request.query)

                search_results.append(KnowledgeBaseSearchResult(
                    document_id=doc_data['id'],
                    title=doc_data['title'],
                    content_snippet=snippet,
                    relevance_score=similarity,
                    content_type=doc_data['content_type'],
                    metadata=json.loads(doc_data['metadata']) if doc_data['metadata'] else None
                ))

            return search_results

        except Exception as e:
            print(f"❌ Semantic search failed: {e}")
            import traceback
            traceback.print_exc()

            # Fallback to simple keyword search
            return await self._fallback_keyword_search(db, search_request, effective_tenant_id)
    
    def _create_snippet(self, content: str, query: str, snippet_length: int = 2000) -> str:
        """Create a comprehensive content snippet for better context."""
        content_lower = content.lower()
        query_lower = query.lower()

        # For DocuPro queries, extract relevant sections
        if any(term in query_lower for term in ['docupro', 'module', 'fonctionnalité', 'functionality']):
            return self._extract_docupro_sections(content, query_lower, snippet_length)

        # Find first occurrence of query (or just return beginning if not found)
        index = content_lower.find(query_lower)
        if index == -1:
            # If exact query not found, look for variations
            for variation in ['trésor', 'tresor', 'money', 'docupro', 'docu-', 'module', 'fonctionnalité']:
                index = content_lower.find(variation)
                if index != -1:
                    break

        if index == -1:
            # Still not found, return beginning of content with more context
            return content[:snippet_length] + "..." if len(content) > snippet_length else content

        # Create larger snippet around the match for better context
        start = max(0, index - snippet_length // 3)
        end = min(len(content), start + snippet_length)

        snippet = content[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."

        return snippet

    def _extract_docupro_sections(self, content: str, query: str, max_length: int = 3000) -> str:
        """Extract relevant DocuPro sections based on query."""
        content_lower = content.lower()

        # Key sections to extract for DocuPro
        sections = []

        # Extract introduction and overview
        intro_start = content_lower.find('introduction')
        if intro_start != -1:
            intro_end = content_lower.find('vue d\'ensemble', intro_start)
            if intro_end == -1:
                intro_end = intro_start + 1000
            sections.append(content[intro_start:intro_end])

        # Extract overview section
        overview_start = content_lower.find('vue d\'ensemble')
        if overview_start != -1:
            overview_end = content_lower.find('description fonctionnelle', overview_start)
            if overview_end == -1:
                overview_end = overview_start + 2000
            sections.append(content[overview_start:overview_end])

        # If asking about modules, extract module descriptions
        if 'module' in query:
            for module in ['docu-courriers', 'docu-archives', 'docu-ged', 'docu-flow']:
                module_start = content_lower.find(module)
                if module_start != -1:
                    # Find next major section or limit to reasonable length
                    module_end = module_start + 1500
                    for next_section in ['docu-', 'fiche technique']:
                        next_start = content_lower.find(next_section, module_start + 100)
                        if next_start != -1 and next_start < module_end:
                            module_end = next_start
                    sections.append(content[module_start:module_end])

        # Combine sections
        combined = '\n\n'.join(sections)

        # If no specific sections found, return larger beginning
        if not combined.strip():
            return content[:max_length] + "..." if len(content) > max_length else content

        # Truncate if too long
        if len(combined) > max_length:
            combined = combined[:max_length] + "..."

        return combined

    async def _fallback_keyword_search(
        self,
        db,
        search_request: KnowledgeBaseSearchRequest,
        tenant_id: str
    ) -> List[KnowledgeBaseSearchResult]:
        """Fallback keyword search with tenant isolation."""
        print(f"🔍 Using fallback keyword search for tenant {tenant_id}")

        # Get all active documents for this agent and tenant
        result = await db.execute(
            select(
                KnowledgeBaseDocument.id,
                KnowledgeBaseDocument.tenant_id,
                KnowledgeBaseDocument.agent_id,
                KnowledgeBaseDocument.title,
                KnowledgeBaseDocument.content,
                KnowledgeBaseDocument.content_type,
                KnowledgeBaseDocument.file_path,
                KnowledgeBaseDocument.content_hash,
                KnowledgeBaseDocument.doc_metadata,
                KnowledgeBaseDocument.is_active,
                KnowledgeBaseDocument.created_at,
                KnowledgeBaseDocument.updated_at
            ).where(
                and_(
                    KnowledgeBaseDocument.tenant_id == tenant_id,
                    KnowledgeBaseDocument.agent_id == self.agent_id,
                    KnowledgeBaseDocument.is_active == True
                )
            )
        )
        documents = result.fetchall()  # Use fetchall() for tuple results

        print(f"🔍 Found {len(documents)} documents for fallback search")

        # Simple keyword matching
        query_lower = search_request.query.lower()
        scored_results = []

        for doc in documents:
            # Handle both ORM objects and tuple results
            if hasattr(doc, 'title'):
                # ORM object
                content_lower = doc.content.lower()
                title_lower = doc.title.lower()
                doc_id = doc.id
                doc_title = doc.title
                doc_content = doc.content
                doc_content_type = doc.content_type
                doc_metadata = doc.doc_metadata
            else:
                # Tuple result
                content_lower = doc[3].lower()  # content at index 3
                title_lower = doc[2].lower()    # title at index 2
                doc_id = doc[0]
                doc_title = doc[2]
                doc_content = doc[3]
                doc_content_type = doc[4]
                doc_metadata = doc[7]

            # Check for any keyword matches
            score = 0

            # Split query into words and check each word
            query_words = query_lower.split()
            for word in query_words:
                # Skip very short words
                if len(word) < 3:
                    continue

                # Check in title (higher score)
                if word in title_lower:
                    score += 20

                # Check in content
                if word in content_lower:
                    score += 10

            # Specific keyword bonuses for known terms
            if 'tresor' in query_lower or 'trésor' in query_lower:
                if 'tresor' in content_lower or 'trésor' in content_lower:
                    score += 5
            if 'ussd' in query_lower:
                if 'ussd' in content_lower:
                    score += 5

            print(f"🔍 Document '{doc_title}' keyword score: {score}")

            if score > 0:
                snippet = self._create_snippet(doc_content, search_request.query)
                scored_results.append(KnowledgeBaseSearchResult(
                    document_id=doc_id,
                    title=doc_title,
                    content_snippet=snippet,
                    relevance_score=score,
                    content_type=doc_content_type,
                    metadata=self._safe_parse_metadata(doc_metadata)
                ))

        # Sort by score and return top results
        scored_results.sort(key=lambda x: x.relevance_score, reverse=True)
        return scored_results[:search_request.limit]

    async def get_document(self, db, document_id: int) -> Optional[KnowledgeBaseDocument]:
        """Get a specific document by ID."""
        # Select specific columns to avoid embedding column issues
        result = await db.execute(
            select(
                KnowledgeBaseDocument.id,
                KnowledgeBaseDocument.agent_id,
                KnowledgeBaseDocument.title,
                KnowledgeBaseDocument.content,
                KnowledgeBaseDocument.content_type,
                KnowledgeBaseDocument.file_path,
                KnowledgeBaseDocument.content_hash,
                KnowledgeBaseDocument.doc_metadata,
                KnowledgeBaseDocument.is_active,
                KnowledgeBaseDocument.created_at,
                KnowledgeBaseDocument.updated_at
            ).where(
                and_(
                    KnowledgeBaseDocument.id == document_id,
                    KnowledgeBaseDocument.agent_id == self.agent_id,
                    KnowledgeBaseDocument.is_active == True
                )
            )
        )

        row = result.fetchone()
        if not row:
            return None

        # Convert tuple to KnowledgeBaseDocument object
        return KnowledgeBaseDocument(
            id=row[0],
            agent_id=row[1],
            title=row[2],
            content=row[3],
            content_type=row[4],
            file_path=row[5],
            content_hash=row[6],
            doc_metadata=row[7],
            is_active=row[8],
            created_at=row[9],
            updated_at=row[10]
        )
    
    async def list_documents(self, db, limit: int = 50) -> List[KnowledgeBaseDocument]:
        """List all documents in the knowledge base."""
        # Select specific columns to avoid embedding column issues
        result = await db.execute(
            select(
                KnowledgeBaseDocument.id,
                KnowledgeBaseDocument.agent_id,
                KnowledgeBaseDocument.title,
                KnowledgeBaseDocument.content,
                KnowledgeBaseDocument.content_type,
                KnowledgeBaseDocument.file_path,
                KnowledgeBaseDocument.content_hash,
                KnowledgeBaseDocument.doc_metadata,
                KnowledgeBaseDocument.is_active,
                KnowledgeBaseDocument.created_at,
                KnowledgeBaseDocument.updated_at
            )
            .where(
                and_(
                    KnowledgeBaseDocument.agent_id == self.agent_id,
                    KnowledgeBaseDocument.is_active == True
                )
            )
            .order_by(KnowledgeBaseDocument.created_at.desc())
            .limit(limit)
        )

        # Convert tuples to KnowledgeBaseDocument objects
        documents = []
        for row in result.fetchall():
            doc = KnowledgeBaseDocument(
                id=row[0],
                agent_id=row[1],
                title=row[2],
                content=row[3],
                content_type=row[4],
                file_path=row[5],
                content_hash=row[6],
                doc_metadata=row[7],
                is_active=row[8],
                created_at=row[9],
                updated_at=row[10]
            )
            documents.append(doc)

        return documents
    
    async def delete_document(self, db, document_id: int) -> bool:
        """Soft delete a document."""
        # Use update query to avoid embedding column issues
        from sqlalchemy import update

        result = await db.execute(
            update(KnowledgeBaseDocument)
            .where(
                and_(
                    KnowledgeBaseDocument.id == document_id,
                    KnowledgeBaseDocument.agent_id == self.agent_id,
                    KnowledgeBaseDocument.is_active == True
                )
            )
            .values(is_active=False)
        )

        await db.commit()
        return result.rowcount > 0


# Tool configuration for agent integration
KNOWLEDGE_BASE_TOOL_CONFIG = {
    "name": "knowledge_base",
    "display_name": "Knowledge Base",
    "description": "Store and search through documents and information with semantic search",
    "capabilities": [
        "document_storage",
        "content_search",
        "information_retrieval",
        "semantic_search",
        "pdf_processing",
        "vector_embeddings"
    ],
    "configuration_schema": {
        "max_documents": {"type": "integer", "default": 1000},
        "max_document_size": {"type": "integer", "default": 100000},  # 100KB
        "search_limit": {"type": "integer", "default": 10},
        "use_vector_search": {"type": "boolean", "default": True},
        "chunk_size": {"type": "integer", "default": 1000},
        "chunk_overlap": {"type": "integer", "default": 200}
    }
}


# Enhanced Knowledge Base Manager Integration
def get_enhanced_knowledge_base_manager(agent_id: int, tenant_id: str = None):
    """Get an enhanced knowledge base manager for an agent with tenant support"""
    try:
        from .enhanced_knowledge_base import create_knowledge_base_manager
        return create_knowledge_base_manager(agent_id, tenant_id)
    except ImportError:
        print("⚠️ Enhanced knowledge base not available, using basic manager")
        return KnowledgeBaseTool(agent_id, tenant_id)
