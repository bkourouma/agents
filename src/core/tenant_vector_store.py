"""
Tenant-aware vector store management for ChromaDB collections.
Ensures complete isolation of vector embeddings between tenants.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import uuid

logger = logging.getLogger(__name__)

# Check for ChromaDB availability
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("ChromaDB not available - vector search will be disabled")

# Check for LangChain ChromaDB integration
try:
    from langchain_chroma import Chroma
    from langchain_openai import OpenAIEmbeddings
    LANGCHAIN_CHROMA_AVAILABLE = True
except ImportError:
    LANGCHAIN_CHROMA_AVAILABLE = False
    logger.warning("LangChain ChromaDB integration not available")


class TenantVectorStoreManager:
    """
    Manages tenant-isolated ChromaDB collections for vector embeddings.
    Each tenant gets their own isolated vector storage.
    """
    
    def __init__(self, base_vector_path: str = "./data/vectors"):
        self.base_vector_path = Path(base_vector_path)
        self.base_vector_path.mkdir(parents=True, exist_ok=True)
        
        # Collection naming pattern: tenant_{tenant_id}_agent_{agent_id}
        # Storage structure:
        # ./data/vectors/
        # ├── tenant_{tenant_id}/
        # │   ├── agent_{agent_id}/
        # │   │   └── chroma_collection/
        # │   └── agent_{agent_id2}/
        # │       └── chroma_collection/
        # └── tenant_{tenant_id2}/
        #     └── ...
        
        self._clients = {}  # Cache for ChromaDB clients
        self._embeddings = None  # Cache for embeddings
    
    @property
    def embeddings(self):
        """Lazy initialization of OpenAI embeddings."""
        if self._embeddings is None and LANGCHAIN_CHROMA_AVAILABLE:
            try:
                self._embeddings = OpenAIEmbeddings()
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI embeddings: {e}")
                self._embeddings = None
        return self._embeddings
    
    def get_tenant_vector_path(self, tenant_id: str, agent_id: int) -> Path:
        """Get the vector storage path for a tenant's agent."""
        vector_path = self.base_vector_path / f"tenant_{tenant_id}" / f"agent_{agent_id}"
        vector_path.mkdir(parents=True, exist_ok=True)
        return vector_path
    
    def get_collection_name(self, tenant_id: str, agent_id: int) -> str:
        """Generate a unique collection name for tenant-agent combination."""
        return f"tenant_{tenant_id}_agent_{agent_id}"
    
    def get_chromadb_client(self, tenant_id: str, agent_id: int):
        """Get or create a ChromaDB client for a tenant-agent combination."""
        if not CHROMADB_AVAILABLE:
            logger.error("ChromaDB not available")
            return None
        
        client_key = f"{tenant_id}_{agent_id}"
        
        if client_key not in self._clients:
            try:
                vector_path = self.get_tenant_vector_path(tenant_id, agent_id)
                
                # Create persistent ChromaDB client with tenant isolation
                client = chromadb.PersistentClient(
                    path=str(vector_path),
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
                
                self._clients[client_key] = client
                logger.info(f"ChromaDB client created for tenant {tenant_id}, agent {agent_id}")
                
            except Exception as e:
                logger.error(f"Failed to create ChromaDB client for tenant {tenant_id}: {e}")
                return None
        
        return self._clients[client_key]
    
    def get_langchain_vector_store(self, tenant_id: str, agent_id: int):
        """Get a LangChain Chroma vector store for a tenant-agent combination."""
        if not LANGCHAIN_CHROMA_AVAILABLE or not self.embeddings:
            logger.error("LangChain ChromaDB integration or embeddings not available")
            return None
        
        try:
            vector_path = self.get_tenant_vector_path(tenant_id, agent_id)
            collection_name = self.get_collection_name(tenant_id, agent_id)
            
            # Create LangChain Chroma vector store with tenant isolation
            vector_store = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                persist_directory=str(vector_path)
            )
            
            logger.info(f"LangChain vector store created for tenant {tenant_id}, agent {agent_id}")
            return vector_store
            
        except Exception as e:
            logger.error(f"Failed to create LangChain vector store for tenant {tenant_id}: {e}")
            return None
    
    def add_documents_to_vector_store(
        self,
        tenant_id: str,
        agent_id: int,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> bool:
        """
        Add documents to the tenant-isolated vector store.
        
        Args:
            tenant_id: The tenant ID
            agent_id: The agent ID
            documents: List of document texts to add
            metadatas: Optional list of metadata dictionaries
            ids: Optional list of document IDs
            
        Returns:
            True if successful, False otherwise
        """
        try:
            vector_store = self.get_langchain_vector_store(tenant_id, agent_id)
            if not vector_store:
                return False
            
            # Generate IDs if not provided
            if ids is None:
                ids = [str(uuid.uuid4()) for _ in documents]
            
            # Add documents to vector store
            vector_store.add_texts(
                texts=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(documents)} documents to vector store for tenant {tenant_id}, agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add documents to vector store for tenant {tenant_id}: {e}")
            return False
    
    def search_vector_store(
        self,
        tenant_id: str,
        agent_id: int,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search the tenant-isolated vector store.
        
        Args:
            tenant_id: The tenant ID
            agent_id: The agent ID
            query: The search query
            k: Number of results to return
            filter_dict: Optional metadata filter
            
        Returns:
            List of search results with content and metadata
        """
        try:
            vector_store = self.get_langchain_vector_store(tenant_id, agent_id)
            if not vector_store:
                return []
            
            # Perform similarity search
            results = vector_store.similarity_search_with_score(
                query=query,
                k=k,
                filter=filter_dict
            )
            
            # Format results
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity_score": float(score)
                })
            
            logger.info(f"Vector search returned {len(formatted_results)} results for tenant {tenant_id}, agent {agent_id}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to search vector store for tenant {tenant_id}: {e}")
            return []
    
    def delete_documents_from_vector_store(
        self,
        tenant_id: str,
        agent_id: int,
        ids: List[str]
    ) -> bool:
        """
        Delete documents from the tenant-isolated vector store.
        
        Args:
            tenant_id: The tenant ID
            agent_id: The agent ID
            ids: List of document IDs to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            vector_store = self.get_langchain_vector_store(tenant_id, agent_id)
            if not vector_store:
                return False
            
            # Delete documents by IDs
            vector_store.delete(ids=ids)
            
            logger.info(f"Deleted {len(ids)} documents from vector store for tenant {tenant_id}, agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete documents from vector store for tenant {tenant_id}: {e}")
            return False
    
    def get_collection_stats(self, tenant_id: str, agent_id: int) -> Dict[str, Any]:
        """
        Get statistics for a tenant-agent vector collection.
        
        Args:
            tenant_id: The tenant ID
            agent_id: The agent ID
            
        Returns:
            Dictionary with collection statistics
        """
        try:
            client = self.get_chromadb_client(tenant_id, agent_id)
            if not client:
                return {"error": "ChromaDB client not available"}
            
            collection_name = self.get_collection_name(tenant_id, agent_id)
            
            try:
                collection = client.get_collection(collection_name)
                count = collection.count()
                
                return {
                    "collection_name": collection_name,
                    "document_count": count,
                    "tenant_id": tenant_id,
                    "agent_id": agent_id
                }
                
            except Exception:
                # Collection doesn't exist yet
                return {
                    "collection_name": collection_name,
                    "document_count": 0,
                    "tenant_id": tenant_id,
                    "agent_id": agent_id
                }
                
        except Exception as e:
            logger.error(f"Failed to get collection stats for tenant {tenant_id}: {e}")
            return {"error": str(e)}
    
    def list_tenant_collections(self, tenant_id: str) -> List[Dict[str, Any]]:
        """
        List all vector collections for a tenant.
        
        Args:
            tenant_id: The tenant ID
            
        Returns:
            List of collection information
        """
        try:
            collections = []
            tenant_vector_path = self.base_vector_path / f"tenant_{tenant_id}"
            
            if not tenant_vector_path.exists():
                return collections
            
            # Find all agent directories
            for agent_path in tenant_vector_path.iterdir():
                if agent_path.is_dir() and agent_path.name.startswith("agent_"):
                    try:
                        agent_id = int(agent_path.name.replace("agent_", ""))
                        stats = self.get_collection_stats(tenant_id, agent_id)
                        collections.append(stats)
                    except ValueError:
                        continue
            
            return collections
            
        except Exception as e:
            logger.error(f"Failed to list collections for tenant {tenant_id}: {e}")
            return []
    
    def cleanup_tenant_vectors(self, tenant_id: str) -> bool:
        """
        Clean up all vector data for a tenant.
        
        Args:
            tenant_id: The tenant ID to clean up
            
        Returns:
            True if cleanup was successful, False otherwise
        """
        try:
            import shutil
            
            tenant_vector_path = self.base_vector_path / f"tenant_{tenant_id}"
            
            if tenant_vector_path.exists():
                shutil.rmtree(tenant_vector_path)
                logger.info(f"Tenant vector data cleaned up: {tenant_id}")
            
            # Clear cached clients for this tenant
            keys_to_remove = [k for k in self._clients.keys() if k.startswith(f"{tenant_id}_")]
            for key in keys_to_remove:
                del self._clients[key]
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup tenant vector data {tenant_id}: {e}")
            return False


# Global instance
_vector_store_manager = None

def get_tenant_vector_store_manager() -> TenantVectorStoreManager:
    """Get the global tenant vector store manager instance."""
    global _vector_store_manager
    if _vector_store_manager is None:
        base_path = os.getenv("KNOWLEDGE_BASE_VECTOR_PATH", "./data/vectors")
        _vector_store_manager = TenantVectorStoreManager(base_path)
    return _vector_store_manager
