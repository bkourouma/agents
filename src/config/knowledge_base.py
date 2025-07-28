"""
Configuration for Enhanced Knowledge Base System
"""

import os
from typing import Dict, Any


class KnowledgeBaseConfig:
    """Configuration settings for the knowledge base system"""
    
    # Vector Search Settings
    VECTOR_SEARCH_ENABLED: bool = os.getenv("KB_VECTOR_SEARCH_ENABLED", "true").lower() == "true"
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Document Processing
    CHUNK_SIZE: int = int(os.getenv("KB_CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("KB_CHUNK_OVERLAP", "200"))
    MAX_DOCUMENT_SIZE: int = int(os.getenv("KB_MAX_DOCUMENT_SIZE", "10485760"))  # 10MB
    
    # Search Settings
    MAX_SEARCH_RESULTS: int = int(os.getenv("KB_MAX_SEARCH_RESULTS", "5"))
    MIN_RELEVANCE_SCORE: float = float(os.getenv("KB_MIN_RELEVANCE_SCORE", "0.7"))
    
    # Storage Paths
    VECTOR_STORE_PATH: str = os.getenv("KB_VECTOR_STORE_PATH", "./data/vector_store")
    DOCUMENTS_PATH: str = os.getenv("KB_DOCUMENTS_PATH", "./data/agent_docs")
    
    # LLM Settings
    OPENAI_MODEL: str = os.getenv("KB_OPENAI_MODEL", "gpt-3.5-turbo")
    OPENAI_TEMPERATURE: float = float(os.getenv("KB_OPENAI_TEMPERATURE", "0.0"))
    
    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """Get configuration as dictionary"""
        return {
            "vector_search_enabled": cls.VECTOR_SEARCH_ENABLED,
            "chunk_size": cls.CHUNK_SIZE,
            "chunk_overlap": cls.CHUNK_OVERLAP,
            "max_document_size": cls.MAX_DOCUMENT_SIZE,
            "max_search_results": cls.MAX_SEARCH_RESULTS,
            "min_relevance_score": cls.MIN_RELEVANCE_SCORE,
            "vector_store_path": cls.VECTOR_STORE_PATH,
            "documents_path": cls.DOCUMENTS_PATH,
            "openai_model": cls.OPENAI_MODEL,
            "openai_temperature": cls.OPENAI_TEMPERATURE,
            "openai_api_key_configured": bool(cls.OPENAI_API_KEY)
        }
    
    @classmethod
    def validate_config(cls) -> Dict[str, str]:
        """Validate configuration and return any issues"""
        issues = {}
        
        if cls.VECTOR_SEARCH_ENABLED and not cls.OPENAI_API_KEY:
            issues["openai_api_key"] = "OpenAI API key is required for vector search"
        
        if cls.CHUNK_SIZE < 100:
            issues["chunk_size"] = "Chunk size should be at least 100 characters"
        
        if cls.CHUNK_OVERLAP >= cls.CHUNK_SIZE:
            issues["chunk_overlap"] = "Chunk overlap should be less than chunk size"
        
        if cls.MIN_RELEVANCE_SCORE < 0 or cls.MIN_RELEVANCE_SCORE > 1:
            issues["min_relevance_score"] = "Relevance score should be between 0 and 1"
        
        return issues


# Global configuration instance
kb_config = KnowledgeBaseConfig()
