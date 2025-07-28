"""
Semantic search implementation using sentence transformers for knowledge base.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import json
import hashlib
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)


class SemanticSearchEngine:
    """Semantic search engine using sentence transformers."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the semantic search engine.
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model."""
        try:
            logger.info(f"Loading sentence transformer model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model {self.model_name}: {e}")
            # Fallback to a smaller model if the default fails
            try:
                logger.info("Trying fallback model: paraphrase-MiniLM-L3-v2")
                self.model = SentenceTransformer("paraphrase-MiniLM-L3-v2")
                self.model_name = "paraphrase-MiniLM-L3-v2"
                logger.info("Fallback model loaded successfully")
            except Exception as e2:
                logger.error(f"Failed to load fallback model: {e2}")
                raise RuntimeError(f"Could not load any sentence transformer model: {e2}")
    
    def encode_text(self, text: str) -> np.ndarray:
        """
        Encode text into a vector embedding.
        
        Args:
            text: Text to encode
            
        Returns:
            Vector embedding as numpy array
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")
        
        try:
            # Clean and preprocess text
            cleaned_text = self._preprocess_text(text)
            embedding = self.model.encode(cleaned_text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            logger.error(f"Failed to encode text: {e}")
            # Return zero vector as fallback
            return np.zeros(self.model.get_sentence_embedding_dimension())
    
    def encode_texts(self, texts: List[str]) -> np.ndarray:
        """
        Encode multiple texts into vector embeddings.
        
        Args:
            texts: List of texts to encode
            
        Returns:
            Matrix of embeddings
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")
        
        try:
            # Clean and preprocess texts
            cleaned_texts = [self._preprocess_text(text) for text in texts]
            embeddings = self.model.encode(cleaned_texts, convert_to_numpy=True)
            return embeddings
        except Exception as e:
            logger.error(f"Failed to encode texts: {e}")
            # Return zero matrix as fallback
            return np.zeros((len(texts), self.model.get_sentence_embedding_dimension()))
    
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text for better embedding quality.
        
        Args:
            text: Raw text
            
        Returns:
            Preprocessed text
        """
        # Basic preprocessing
        text = text.strip()
        
        # Handle special characters and normalize
        text = text.replace('é', 'e').replace('è', 'e').replace('à', 'a')
        text = text.replace('ç', 'c').replace('ù', 'u').replace('ô', 'o')
        
        # Normalize common variations
        text = text.replace('TrésorMoney', 'TresorMoney')
        text = text.replace('Trésor', 'Tresor')
        
        return text
    
    def search_similar(
        self, 
        query: str, 
        document_embeddings: np.ndarray, 
        documents: List[Dict[str, Any]], 
        top_k: int = 5,
        min_similarity: float = 0.1
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Search for similar documents using semantic similarity.
        
        Args:
            query: Search query
            document_embeddings: Precomputed document embeddings
            documents: List of document metadata
            top_k: Number of top results to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of (document, similarity_score) tuples
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")
        
        try:
            # Encode the query
            query_embedding = self.encode_text(query)
            
            # Calculate similarities
            similarities = cosine_similarity(
                query_embedding.reshape(1, -1), 
                document_embeddings
            )[0]
            
            # Get top results above threshold
            results = []
            for i, similarity in enumerate(similarities):
                if similarity >= min_similarity and i < len(documents):
                    results.append((documents[i], float(similarity)))
            
            # Sort by similarity and return top k
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Failed to search similar documents: {e}")
            return []
    
    def create_document_chunks(
        self, 
        content: str, 
        chunk_size: int = 500, 
        overlap: int = 50
    ) -> List[str]:
        """
        Split document content into overlapping chunks for better search.
        
        Args:
            content: Document content
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks
            
        Returns:
            List of text chunks
        """
        if len(content) <= chunk_size:
            return [content]
        
        chunks = []
        start = 0
        
        while start < len(content):
            end = min(start + chunk_size, len(content))
            
            # Try to break at sentence or word boundary
            if end < len(content):
                # Look for sentence boundary
                last_period = content.rfind('.', start, end)
                last_newline = content.rfind('\n', start, end)
                boundary = max(last_period, last_newline)
                
                if boundary > start + chunk_size // 2:
                    end = boundary + 1
                else:
                    # Look for word boundary
                    last_space = content.rfind(' ', start, end)
                    if last_space > start + chunk_size // 2:
                        end = last_space
            
            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            if start >= len(content):
                break
        
        return chunks


# Global instance
_semantic_search_engine = None


def get_semantic_search_engine() -> SemanticSearchEngine:
    """Get or create the global semantic search engine instance."""
    global _semantic_search_engine
    if _semantic_search_engine is None:
        _semantic_search_engine = SemanticSearchEngine()
    return _semantic_search_engine
