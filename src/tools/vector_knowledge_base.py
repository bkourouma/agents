"""
Enhanced Vector-based Knowledge Base System
Implements semantic search using ChromaDB and OpenAI embeddings
"""

import os
import json
import hashlib
import asyncio
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime

# Core dependencies
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel

# LangChain and Vector Store
try:
    from langchain.document_loaders import PyPDFLoader
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_openai import OpenAIEmbeddings
    from langchain_chroma import Chroma
    import chromadb
    VECTOR_DEPS_AVAILABLE = True
except ImportError:
    VECTOR_DEPS_AVAILABLE = False
    print("⚠️ Vector dependencies not available. Install: pip install langchain-chroma chromadb pypdf")

# Local imports
from .knowledge_base import KnowledgeBaseDocument, KnowledgeBaseSearchRequest, KnowledgeBaseSearchResult


class VectorKnowledgeBaseConfig:
    """Configuration for the vector knowledge base system"""
    
    # Document processing
    CHUNK_SIZE: int = int(os.getenv("KB_CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("KB_CHUNK_OVERLAP", "200"))
    
    # OpenAI settings
    OPENAI_MODEL: str = os.getenv("KB_OPENAI_MODEL", "gpt-3.5-turbo")
    OPENAI_TEMPERATURE: float = float(os.getenv("KB_OPENAI_TEMPERATURE", "0.0"))
    
    # Vector store settings
    VECTOR_STORE_PATH: str = os.getenv("KB_VECTOR_STORE_PATH", "./data/vector_store")
    COLLECTION_PREFIX: str = "agent_kb"
    
    # Search settings
    MAX_SEARCH_RESULTS: int = int(os.getenv("KB_MAX_SEARCH_RESULTS", "5"))
    MIN_RELEVANCE_SCORE: float = float(os.getenv("KB_MIN_RELEVANCE_SCORE", "0.7"))


class DocumentChunk(BaseModel):
    """Represents a chunk of a document"""
    chunk_id: str
    document_id: int
    content: str
    metadata: Dict[str, Any]
    page_number: Optional[int] = None
    chunk_index: int


class VectorKnowledgeBaseManager:
    """Enhanced knowledge base manager with vector search capabilities"""
    
    def __init__(self, agent_id: int):
        self.agent_id = agent_id
        self.config = VectorKnowledgeBaseConfig()
        self.collection_name = f"{self.config.COLLECTION_PREFIX}_{agent_id}"
        
        # Initialize components
        self._embeddings = None
        self._vector_store = None
        self._text_splitter = None
        
        # Ensure vector store directory exists
        Path(self.config.VECTOR_STORE_PATH).mkdir(parents=True, exist_ok=True)
    
    @property
    def embeddings(self):
        """Lazy initialization of OpenAI embeddings"""
        if self._embeddings is None and VECTOR_DEPS_AVAILABLE:
            try:
                self._embeddings = OpenAIEmbeddings()
            except Exception as e:
                print(f"⚠️ Failed to initialize OpenAI embeddings: {e}")
                self._embeddings = None
        return self._embeddings
    
    @property
    def text_splitter(self):
        """Lazy initialization of text splitter"""
        if self._text_splitter is None and VECTOR_DEPS_AVAILABLE:
            self._text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.config.CHUNK_SIZE,
                chunk_overlap=self.config.CHUNK_OVERLAP,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
        return self._text_splitter
    
    @property
    def vector_store(self):
        """Lazy initialization of vector store"""
        if self._vector_store is None and VECTOR_DEPS_AVAILABLE and self.embeddings:
            try:
                # Initialize ChromaDB client
                client = chromadb.PersistentClient(path=self.config.VECTOR_STORE_PATH)
                
                # Initialize Chroma vector store
                self._vector_store = Chroma(
                    client=client,
                    collection_name=self.collection_name,
                    embedding_function=self.embeddings,
                )
            except Exception as e:
                print(f"⚠️ Failed to initialize vector store: {e}")
                self._vector_store = None
        return self._vector_store
    
    def _create_chunk_id(self, document_id: int, chunk_index: int) -> str:
        """Create a unique chunk ID"""
        return f"doc_{document_id}_chunk_{chunk_index}"
    
    def _extract_text_from_pdf(self, file_path: str) -> List[str]:
        """Extract text from PDF using multiple fallback methods"""
        if not VECTOR_DEPS_AVAILABLE:
            raise ImportError("Vector dependencies not available")
        
        try:
            # Primary method: PyPDFLoader
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            return [doc.page_content for doc in documents]
        except Exception as e:
            print(f"⚠️ PyPDFLoader failed: {e}")
            
            # Fallback: Try PyPDF2 directly
            try:
                import PyPDF2
                with open(file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    pages = []
                    for page in reader.pages:
                        pages.append(page.extract_text())
                    return pages
            except Exception as e2:
                print(f"⚠️ PyPDF2 fallback failed: {e2}")
                raise Exception(f"Failed to extract text from PDF: {e}")
    
    async def process_document(
        self, 
        db: AsyncSession, 
        document: KnowledgeBaseDocument,
        file_path: Optional[str] = None
    ) -> bool:
        """Process a document and create vector embeddings"""
        
        if not VECTOR_DEPS_AVAILABLE:
            print("⚠️ Vector processing not available, falling back to simple storage")
            return True
        
        if not self.vector_store:
            print("⚠️ Vector store not initialized")
            return False
        
        try:
            print(f"🔄 Processing document: {document.title}")
            
            # Extract text content
            if file_path and document.content_type == "application/pdf":
                # Extract from PDF file
                pages = self._extract_text_from_pdf(file_path)
                full_text = "\n\n".join(pages)
            else:
                # Use existing content
                full_text = document.content
            
            # Split text into chunks
            chunks = self.text_splitter.split_text(full_text)
            print(f"📄 Split document into {len(chunks)} chunks")
            
            # Prepare documents for vector store
            documents = []
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = self._create_chunk_id(document.id, i)
                
                # Prepare metadata
                metadata = {
                    "document_id": document.id,
                    "document_title": document.title,
                    "chunk_index": i,
                    "content_type": document.content_type,
                    "agent_id": self.agent_id,
                    "created_at": document.created_at.isoformat() if document.created_at else None
                }
                
                # Add custom metadata if available
                if document.doc_metadata:
                    try:
                        custom_meta = json.loads(document.doc_metadata)
                        metadata.update(custom_meta)
                    except:
                        pass
                
                documents.append(chunk)
                metadatas.append(metadata)
                ids.append(chunk_id)
            
            # Add to vector store
            self.vector_store.add_texts(
                texts=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            print(f"✅ Successfully processed {len(chunks)} chunks for document: {document.title}")
            return True
            
        except Exception as e:
            print(f"❌ Error processing document {document.title}: {e}")
            return False
    
    async def search_documents(
        self, 
        search_request: KnowledgeBaseSearchRequest
    ) -> List[KnowledgeBaseSearchResult]:
        """Search documents using vector similarity"""
        
        if not VECTOR_DEPS_AVAILABLE or not self.vector_store:
            print("⚠️ Vector search not available, falling back to keyword search")
            return []
        
        try:
            print(f"🔍 Vector search for: {search_request.query}")
            
            # Perform similarity search
            results = self.vector_store.similarity_search_with_score(
                query=search_request.query,
                k=search_request.limit or self.config.MAX_SEARCH_RESULTS,
                filter={"agent_id": self.agent_id}  # Filter by agent
            )
            
            print(f"🔍 Found {len(results)} vector search results")
            
            # Convert to our result format
            search_results = []
            seen_documents = set()
            
            for doc, score in results:
                # Skip if relevance score is too low
                relevance_score = 1.0 - score  # Convert distance to similarity
                if relevance_score < self.config.MIN_RELEVANCE_SCORE:
                    continue
                
                metadata = doc.metadata
                document_id = metadata.get("document_id")
                document_title = metadata.get("document_title", "Unknown Document")
                
                # Avoid duplicate documents in results
                if document_id in seen_documents:
                    continue
                seen_documents.add(document_id)
                
                # Create search result
                result = KnowledgeBaseSearchResult(
                    document_id=document_id,
                    title=document_title,
                    content_snippet=doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                    relevance_score=relevance_score,
                    content_type=metadata.get("content_type", "text"),
                    metadata=metadata
                )
                
                search_results.append(result)
                print(f"🔍 Result: {document_title} (score: {relevance_score:.3f})")
            
            return search_results
            
        except Exception as e:
            print(f"❌ Vector search error: {e}")
            return []
    
    async def delete_document_vectors(self, document_id: int) -> bool:
        """Delete all vector embeddings for a document"""
        
        if not VECTOR_DEPS_AVAILABLE or not self.vector_store:
            return True  # Nothing to delete
        
        try:
            # Get all chunk IDs for this document
            collection = self.vector_store._collection
            results = collection.get(
                where={"document_id": document_id}
            )
            
            if results and results['ids']:
                # Delete the chunks
                collection.delete(ids=results['ids'])
                print(f"🗑️ Deleted {len(results['ids'])} vector chunks for document {document_id}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error deleting document vectors: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if vector search is available"""
        return VECTOR_DEPS_AVAILABLE and self.vector_store is not None
