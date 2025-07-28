"""
Advanced Content Processing Service for AI Agent Platform.
Provides content cleaning, encoding handling, and configurable chunking.
"""

import re
import logging
import unicodedata
from typing import List, Dict, Any, Optional, Tuple
import html

# Try to import ftfy, but handle gracefully if not available
try:
    import ftfy
    FTFY_AVAILABLE = True
except ImportError:
    FTFY_AVAILABLE = False

from src.config.document_processing import config

logger = logging.getLogger(__name__)


class ContentProcessingError(Exception):
    """Custom exception for content processing errors."""
    pass


class ContentProcessor:
    """Advanced content processor with cleaning and chunking capabilities."""
    
    def __init__(self):
        self.chunk_size = config.CHUNK_SIZE
        self.chunk_overlap = config.CHUNK_OVERLAP
        self.enable_cleaning = config.ENABLE_CONTENT_CLEANING
        self.enable_encoding_cleanup = config.ENABLE_ENCODING_CLEANUP
        
        logger.info(f"Content processor initialized:")
        logger.info(f"  Chunk size: {self.chunk_size}")
        logger.info(f"  Chunk overlap: {self.chunk_overlap}")
        logger.info(f"  Content cleaning: {self.enable_cleaning}")
        logger.info(f"  Encoding cleanup: {self.enable_encoding_cleanup}")
    
    def process_content(
        self, 
        content: str, 
        content_type: str = "text/plain",
        custom_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process content with cleaning, encoding fixes, and chunking.
        
        Args:
            content: Raw content string
            content_type: MIME content type
            custom_config: Optional custom processing configuration
            
        Returns:
            Processing result with cleaned content and chunks
        """
        try:
            logger.info(f"Processing content: {len(content)} characters, type: {content_type}")
            
            # Apply custom configuration if provided
            chunk_size = custom_config.get("chunk_size", self.chunk_size) if custom_config else self.chunk_size
            chunk_overlap = custom_config.get("chunk_overlap", self.chunk_overlap) if custom_config else self.chunk_overlap
            enable_cleaning = custom_config.get("enable_cleaning", self.enable_cleaning) if custom_config else self.enable_cleaning
            enable_encoding_cleanup = custom_config.get("enable_encoding_cleanup", self.enable_encoding_cleanup) if custom_config else self.enable_encoding_cleanup
            
            # Step 1: Encoding cleanup
            if enable_encoding_cleanup:
                content = self._fix_encoding_issues(content)
                logger.debug("✅ Encoding issues fixed")
            
            # Step 2: Content cleaning
            if enable_cleaning:
                content = self._clean_content(content, content_type)
                logger.debug("✅ Content cleaned")
            
            # Step 3: Content validation
            validation_result = self._validate_content(content)
            if not validation_result["valid"]:
                raise ContentProcessingError(f"Content validation failed: {validation_result['errors']}")
            
            # Step 4: Chunking
            chunks = self._create_chunks(content, chunk_size, chunk_overlap)
            logger.info(f"✅ Content processed: {len(chunks)} chunks created")
            
            return {
                "success": True,
                "original_length": len(content),
                "cleaned_content": content,
                "chunks": chunks,
                "chunk_count": len(chunks),
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
                "validation": validation_result,
                "processing_stats": {
                    "encoding_cleanup": enable_encoding_cleanup,
                    "content_cleaning": enable_cleaning,
                    "content_type": content_type
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Content processing failed: {e}")
            raise ContentProcessingError(f"Content processing failed: {str(e)}")
    
    def _fix_encoding_issues(self, content: str) -> str:
        """Fix common encoding issues in text content."""
        try:
            # Use ftfy to fix encoding issues if available
            if FTFY_AVAILABLE:
                content = ftfy.fix_text(content)
            else:
                logger.debug("ftfy not available, using basic encoding fixes")
                # Basic encoding fixes
                content = self._basic_encoding_fixes(content)
            
            # Remove or replace problematic Unicode characters
            content = self._clean_unicode_characters(content)
            
            # Normalize Unicode
            content = unicodedata.normalize('NFKC', content)
            
            return content
            
        except Exception as e:
            logger.warning(f"Encoding fix failed: {e}")
            return content
    
    def _basic_encoding_fixes(self, content: str) -> str:
        """Apply basic encoding fixes without ftfy."""
        # Common encoding issues
        fixes = {
            'â€™': "'",  # Smart apostrophe
            'â€œ': '"',  # Smart quote left
            'â€': '"',   # Smart quote right
            'â€"': '—',  # Em dash
            'â€"': '–',  # En dash
            'Â': '',     # Non-breaking space artifacts
            'â€¦': '...',  # Ellipsis
        }
        
        for bad, good in fixes.items():
            content = content.replace(bad, good)
        
        return content
    
    def _clean_unicode_characters(self, content: str) -> str:
        """Clean problematic Unicode characters."""
        # Remove surrogate characters that cause issues
        content = ''.join(char for char in content if ord(char) < 0xD800 or ord(char) > 0xDFFF)
        
        # Remove control characters except common ones (tab, newline, carriage return)
        content = ''.join(char for char in content if 
                         unicodedata.category(char)[0] != 'C' or 
                         char in '\t\n\r')
        
        return content
    
    def _clean_content(self, content: str, content_type: str) -> str:
        """Clean content based on content type."""
        if content_type == "application/pdf":
            return self._clean_pdf_content(content)
        elif content_type in ["text/html", "application/xhtml+xml"]:
            return self._clean_html_content(content)
        elif content_type == "text/markdown":
            return self._clean_markdown_content(content)
        else:
            return self._clean_text_content(content)
    
    def _clean_pdf_content(self, content: str) -> str:
        """Clean content extracted from PDF."""
        # Remove excessive whitespace
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)  # Multiple newlines to double
        content = re.sub(r' +', ' ', content)  # Multiple spaces to single
        
        # Fix common PDF extraction issues
        content = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', content)  # Fix hyphenated words split across lines
        content = re.sub(r'([.!?])\s*\n\s*([A-Z])', r'\1 \2', content)  # Fix sentence breaks
        
        # Remove page numbers and headers/footers (basic patterns)
        content = re.sub(r'\n\s*\d+\s*\n', '\n', content)  # Standalone page numbers
        content = re.sub(r'\n\s*Page \d+.*?\n', '\n', content)  # "Page X" patterns
        
        return content.strip()
    
    def _clean_html_content(self, content: str) -> str:
        """Clean HTML content."""
        # Decode HTML entities
        content = html.unescape(content)
        
        # Remove HTML tags (basic cleaning)
        content = re.sub(r'<[^>]+>', '', content)
        
        # Clean up whitespace
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        content = re.sub(r' +', ' ', content)
        
        return content.strip()
    
    def _clean_markdown_content(self, content: str) -> str:
        """Clean Markdown content."""
        # Remove excessive whitespace while preserving markdown structure
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        
        # Clean up spaces but preserve code blocks
        lines = content.split('\n')
        cleaned_lines = []
        in_code_block = False
        
        for line in lines:
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                cleaned_lines.append(line)
            elif in_code_block:
                cleaned_lines.append(line)  # Preserve code block formatting
            else:
                cleaned_lines.append(re.sub(r' +', ' ', line))  # Clean spaces in regular text
        
        return '\n'.join(cleaned_lines).strip()
    
    def _clean_text_content(self, content: str) -> str:
        """Clean plain text content."""
        # Remove excessive whitespace
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        content = re.sub(r' +', ' ', content)
        
        # Remove trailing whitespace from lines
        lines = [line.rstrip() for line in content.split('\n')]
        content = '\n'.join(lines)
        
        return content.strip()
    
    def _validate_content(self, content: str) -> Dict[str, Any]:
        """Validate processed content."""
        validation = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "stats": {
                "length": len(content),
                "lines": len(content.split('\n')),
                "words": len(content.split()),
                "characters": len(content)
            }
        }
        
        # Check minimum length
        if len(content.strip()) < 10:
            validation["errors"].append("Content too short (minimum 10 characters)")
            validation["valid"] = False
        
        # Check maximum length (reasonable limit)
        max_length = 10 * 1024 * 1024  # 10MB
        if len(content) > max_length:
            validation["warnings"].append(f"Content very large ({len(content)} characters)")
        
        # Check for suspicious patterns
        if len(content.split()) < 5:
            validation["warnings"].append("Very few words detected")
        
        # Check character distribution
        printable_chars = sum(1 for c in content if c.isprintable() or c.isspace())
        if printable_chars / len(content) < 0.8:
            validation["warnings"].append("High ratio of non-printable characters")
        
        return validation
    
    def _create_chunks(
        self, 
        content: str, 
        chunk_size: int, 
        chunk_overlap: int
    ) -> List[Dict[str, Any]]:
        """Create text chunks with overlap."""
        if not content.strip():
            return []
        
        # Try to use LangChain's text splitter if available
        try:
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=["\n\n", "\n", ". ", " ", ""],
                keep_separator=True
            )
            
            chunks = text_splitter.split_text(content)
            
            # Create chunk objects with metadata
            chunk_objects = []
            for i, chunk_text in enumerate(chunks):
                chunk_objects.append({
                    "index": i,
                    "text": chunk_text,
                    "length": len(chunk_text),
                    "word_count": len(chunk_text.split()),
                    "start_char": content.find(chunk_text) if i == 0 else None,  # Only for first chunk
                    "metadata": {
                        "chunk_method": "langchain_recursive",
                        "chunk_size": chunk_size,
                        "chunk_overlap": chunk_overlap
                    }
                })
            
            return chunk_objects
            
        except ImportError:
            logger.warning("LangChain not available, using basic chunking")
            return self._basic_chunking(content, chunk_size, chunk_overlap)
    
    def _basic_chunking(
        self, 
        content: str, 
        chunk_size: int, 
        chunk_overlap: int
    ) -> List[Dict[str, Any]]:
        """Basic text chunking without LangChain."""
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(content):
            end = start + chunk_size
            
            # If this isn't the last chunk, try to break at a sentence or word boundary
            if end < len(content):
                # Look for sentence boundary within the last 100 characters
                sentence_end = content.rfind('. ', start, end)
                if sentence_end > start + chunk_size - 100:
                    end = sentence_end + 2
                else:
                    # Look for word boundary
                    word_end = content.rfind(' ', start, end)
                    if word_end > start + chunk_size - 50:
                        end = word_end
            
            chunk_text = content[start:end].strip()
            
            if chunk_text:
                chunks.append({
                    "index": chunk_index,
                    "text": chunk_text,
                    "length": len(chunk_text),
                    "word_count": len(chunk_text.split()),
                    "start_char": start,
                    "end_char": end,
                    "metadata": {
                        "chunk_method": "basic",
                        "chunk_size": chunk_size,
                        "chunk_overlap": chunk_overlap
                    }
                })
                chunk_index += 1
            
            # Move start position with overlap
            start = max(start + 1, end - chunk_overlap)
        
        return chunks
    
    def get_processing_capabilities(self) -> Dict[str, Any]:
        """Get content processing capabilities."""
        capabilities = {
            "chunking_methods": ["basic"],
            "content_types": ["text/plain", "application/pdf", "text/markdown", "text/html"],
            "encoding_fixes": self.enable_encoding_cleanup,
            "content_cleaning": self.enable_cleaning,
            "default_chunk_size": self.chunk_size,
            "default_chunk_overlap": self.chunk_overlap,
            "libraries": {
                "ftfy": False,
                "langchain": False
            }
        }
        
        # Check for ftfy
        capabilities["libraries"]["ftfy"] = FTFY_AVAILABLE
        
        # Check for LangChain
        try:
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            capabilities["libraries"]["langchain"] = True
            capabilities["chunking_methods"].append("langchain_recursive")
        except ImportError:
            pass
        
        return capabilities


# Global content processor instance
content_processor = ContentProcessor()
