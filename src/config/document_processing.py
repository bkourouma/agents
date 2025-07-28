"""
Document Processing Configuration for AI Agent Platform.
Provides configurable settings for document ingestion pipeline.
"""

import os
from typing import List, Dict, Any
from pathlib import Path


class DocumentProcessingConfig:
    """Configuration for document processing pipeline."""
    
    # File upload limits
    MAX_FILE_SIZE_MB: int = int(os.getenv("DOC_MAX_FILE_SIZE_MB", "25"))
    MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024
    
    # Supported file extensions (dynamic based on available libraries)
    BASE_ALLOWED_EXTENSIONS: List[str] = [".txt", ".md"]
    
    # Document processing
    CHUNK_SIZE: int = int(os.getenv("DOC_CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("DOC_CHUNK_OVERLAP", "200"))
    
    # OpenAI settings
    OPENAI_MODEL: str = os.getenv("DOC_OPENAI_MODEL", "gpt-3.5-turbo")
    OPENAI_TEMPERATURE: float = float(os.getenv("DOC_OPENAI_TEMPERATURE", "0.0"))
    EMBEDDING_MODEL: str = os.getenv("DOC_EMBEDDING_MODEL", "text-embedding-ada-002")
    
    # Storage paths
    DOCUMENTS_BASE_PATH: str = os.getenv("DOC_STORAGE_PATH", "./agent_documents")
    VECTOR_STORE_PATH: str = os.getenv("DOC_VECTOR_PATH", "./agent_vectors")
    
    # Processing options
    ENABLE_CONTENT_CLEANING: bool = os.getenv("DOC_ENABLE_CLEANING", "true").lower() == "true"
    ENABLE_ENCODING_CLEANUP: bool = os.getenv("DOC_ENABLE_ENCODING_CLEANUP", "true").lower() == "true"
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("DOC_RATE_LIMIT", "30"))
    
    @classmethod
    def get_allowed_extensions(cls) -> List[str]:
        """Get dynamically determined allowed file extensions based on available libraries."""
        allowed = cls.BASE_ALLOWED_EXTENSIONS.copy()
        
        # Check for PDF support
        try:
            import PyPDF2
            allowed.extend([".pdf"])
        except ImportError:
            pass
        
        # Check for DOCX support
        try:
            import docx
            allowed.extend([".docx", ".doc"])
        except ImportError:
            pass
        
        # Check for additional text formats
        allowed.extend([".csv", ".json"])
        
        return list(set(allowed))  # Remove duplicates
    
    @classmethod
    def get_allowed_content_types(cls) -> List[str]:
        """Get allowed MIME content types based on available libraries."""
        content_types = [
            "text/plain",
            "text/markdown",
            "text/csv",
            "application/json"
        ]
        
        # Check for PDF support
        try:
            import PyPDF2
            content_types.append("application/pdf")
        except ImportError:
            pass
        
        # Check for DOCX support
        try:
            import docx
            content_types.extend([
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ])
        except ImportError:
            pass
        
        return content_types
    
    @classmethod
    def get_processing_capabilities(cls) -> Dict[str, bool]:
        """Get available processing capabilities."""
        capabilities = {
            "pdf_support": False,
            "docx_support": False,
            "vector_support": False,
            "advanced_pdf_support": False
        }
        
        # Check PDF support
        try:
            import PyPDF2
            capabilities["pdf_support"] = True
        except ImportError:
            pass
        
        # Check DOCX support
        try:
            import docx
            capabilities["docx_support"] = True
        except ImportError:
            pass
        
        # Check vector support
        try:
            import chromadb
            from langchain_openai import OpenAIEmbeddings
            capabilities["vector_support"] = True
        except ImportError:
            pass
        
        # Check advanced PDF support
        try:
            from langchain_community.document_loaders import PyPDFLoader
            capabilities["advanced_pdf_support"] = True
        except ImportError:
            pass
        
        return capabilities
    
    @classmethod
    def ensure_directories(cls, agent_id: int) -> tuple[Path, Path]:
        """Ensure agent-specific directories exist and return paths."""
        docs_path = Path(cls.DOCUMENTS_BASE_PATH) / f"agent_{agent_id}"
        vector_path = Path(cls.VECTOR_STORE_PATH) / f"agent_{agent_id}"
        
        docs_path.mkdir(parents=True, exist_ok=True)
        vector_path.mkdir(parents=True, exist_ok=True)
        
        return docs_path, vector_path


# Global configuration instance
config = DocumentProcessingConfig()
