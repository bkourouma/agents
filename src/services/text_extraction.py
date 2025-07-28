"""
Enhanced Text Extraction Service for AI Agent Platform.
Provides robust text extraction with multiple fallback methods.
"""

import io
import logging
from typing import List, Optional, Dict, Any, Union
from pathlib import Path
import tempfile
import os

from src.config.document_processing import config

logger = logging.getLogger(__name__)


class TextExtractionError(Exception):
    """Custom exception for text extraction errors."""
    pass


class TextExtractor:
    """Enhanced text extractor with multiple fallback methods."""
    
    def __init__(self):
        self.capabilities = self._check_capabilities()
        logger.info(f"Text extraction capabilities: {self.capabilities}")
    
    def _check_capabilities(self) -> Dict[str, bool]:
        """Check available text extraction libraries."""
        capabilities = {
            "pypdf2": False,
            "langchain_pypdf": False,
            "unstructured": False,
            "pymupdf": False,
            "python_docx": False
        }
        
        # Check PyPDF2
        try:
            import PyPDF2
            capabilities["pypdf2"] = True
        except ImportError:
            pass
        
        # Check LangChain PyPDF
        try:
            from langchain_community.document_loaders import PyPDFLoader
            capabilities["langchain_pypdf"] = True
        except ImportError:
            pass
        
        # Check Unstructured
        try:
            from langchain_community.document_loaders import UnstructuredPDFLoader
            capabilities["unstructured"] = True
        except ImportError:
            pass
        
        # Check PyMuPDF
        try:
            import fitz  # PyMuPDF
            capabilities["pymupdf"] = True
        except ImportError:
            pass
        
        # Check python-docx
        try:
            import docx
            capabilities["python_docx"] = True
        except ImportError:
            pass
        
        return capabilities
    
    def extract_text_from_file(
        self, 
        content: bytes, 
        content_type: str, 
        filename: str
    ) -> str:
        """
        Extract text from file content with appropriate method.
        
        Args:
            content: File content as bytes
            content_type: MIME content type
            filename: Original filename
            
        Returns:
            Extracted text content
        """
        logger.info(f"Extracting text from {filename} (type: {content_type})")
        
        try:
            if content_type == 'application/pdf' or filename.lower().endswith('.pdf'):
                return self._extract_pdf_text(content, filename)
            elif content_type in [
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            ] or filename.lower().endswith(('.docx', '.doc')):
                return self._extract_docx_text(content, filename)
            elif content_type in ['text/plain', 'text/markdown', 'text/csv']:
                return self._extract_text_content(content)
            else:
                # Try as text first, then PDF
                try:
                    return self._extract_text_content(content)
                except UnicodeDecodeError:
                    logger.warning(f"Failed to decode as text, trying PDF extraction for {filename}")
                    return self._extract_pdf_text(content, filename)
        
        except Exception as e:
            logger.error(f"Text extraction failed for {filename}: {e}")
            raise TextExtractionError(f"Failed to extract text from {filename}: {str(e)}")
    
    def _extract_text_content(self, content: bytes) -> str:
        """Extract text from plain text files."""
        try:
            # Try UTF-8 first
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                # Try UTF-8 with error handling
                text = content.decode('utf-8', errors='ignore')
                logger.warning("Used UTF-8 with error handling for text extraction")
            except Exception:
                try:
                    # Try latin-1 as fallback
                    text = content.decode('latin-1')
                    logger.warning("Used latin-1 encoding for text extraction")
                except Exception as e:
                    raise TextExtractionError(f"Failed to decode text content: {str(e)}")
        
        return self._clean_text_content(text)
    
    def _extract_pdf_text(self, content: bytes, filename: str) -> str:
        """Extract text from PDF using multiple fallback methods."""
        extraction_methods = []
        
        # Method 1: LangChain PyPDFLoader (if available)
        if self.capabilities["langchain_pypdf"]:
            extraction_methods.append(("PyPDFLoader", self._extract_with_langchain_pypdf))
        
        # Method 2: Unstructured (if available)
        if self.capabilities["unstructured"]:
            extraction_methods.append(("UnstructuredPDFLoader", self._extract_with_unstructured))
        
        # Method 3: PyMuPDF (if available)
        if self.capabilities["pymupdf"]:
            extraction_methods.append(("PyMuPDFLoader", self._extract_with_pymupdf))
        
        # Method 4: PyPDF2 (fallback)
        if self.capabilities["pypdf2"]:
            extraction_methods.append(("PyPDF2", self._extract_with_pypdf2))
        
        # Method 5: Plain text reading (last resort)
        extraction_methods.append(("PlainText", self._extract_as_text))
        
        last_error = None
        for method_name, method_func in extraction_methods:
            try:
                logger.info(f"Trying PDF extraction method: {method_name}")
                text = method_func(content, filename)
                
                if text and text.strip():
                    logger.info(f"✅ PDF extraction successful with {method_name}: {len(text)} characters")
                    return self._clean_text_content(text)
                else:
                    logger.warning(f"⚠️ {method_name} returned empty content")
                    
            except Exception as e:
                logger.warning(f"❌ {method_name} failed: {str(e)}")
                last_error = e
                continue
        
        # If all methods failed
        if last_error:
            raise TextExtractionError(f"All PDF extraction methods failed. Last error: {str(last_error)}")
        else:
            raise TextExtractionError("All PDF extraction methods returned empty content")
    
    def _extract_with_langchain_pypdf(self, content: bytes, filename: str) -> str:
        """Extract using LangChain PyPDFLoader."""
        from langchain_community.document_loaders import PyPDFLoader
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            loader = PyPDFLoader(temp_path)
            documents = loader.load()
            
            if not documents:
                raise TextExtractionError("No documents loaded from PDF")
            
            # Combine all pages
            text_content = []
            for doc in documents:
                if doc.page_content:
                    text_content.append(doc.page_content)
            
            return "\n\n".join(text_content)
        
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_path)
            except Exception:
                pass
    
    def _extract_with_unstructured(self, content: bytes, filename: str) -> str:
        """Extract using UnstructuredPDFLoader."""
        from langchain_community.document_loaders import UnstructuredPDFLoader
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            loader = UnstructuredPDFLoader(temp_path)
            documents = loader.load()
            
            if not documents:
                raise TextExtractionError("No documents loaded from PDF")
            
            # Combine all content
            text_content = []
            for doc in documents:
                if doc.page_content:
                    text_content.append(doc.page_content)
            
            return "\n\n".join(text_content)
        
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_path)
            except Exception:
                pass
    
    def _extract_with_pymupdf(self, content: bytes, filename: str) -> str:
        """Extract using PyMuPDF."""
        import fitz  # PyMuPDF
        
        # Open PDF from bytes
        pdf_document = fitz.open(stream=content, filetype="pdf")
        
        try:
            text_content = []
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                text = page.get_text()
                if text:
                    text_content.append(text)
            
            return "\n\n".join(text_content)
        
        finally:
            pdf_document.close()
    
    def _extract_with_pypdf2(self, content: bytes, filename: str) -> str:
        """Extract using PyPDF2."""
        import PyPDF2
        
        pdf_file = io.BytesIO(content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text_content = []
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text = page.extract_text()
            if text:
                text_content.append(text)
        
        return "\n\n".join(text_content)
    
    def _extract_as_text(self, content: bytes, filename: str) -> str:
        """Last resort: try to extract as plain text."""
        return self._extract_text_content(content)
    
    def _extract_docx_text(self, content: bytes, filename: str) -> str:
        """Extract text from DOCX files."""
        if not self.capabilities["python_docx"]:
            raise TextExtractionError("DOCX processing not available (python-docx not installed)")
        
        import docx
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            doc = docx.Document(temp_path)
            
            text_content = []
            for paragraph in doc.paragraphs:
                if paragraph.text:
                    text_content.append(paragraph.text)
            
            return "\n".join(text_content)
        
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_path)
            except Exception:
                pass
    
    def _clean_text_content(self, text: str) -> str:
        """Clean extracted text content."""
        if not config.ENABLE_CONTENT_CLEANING:
            return text
        
        # Remove surrogate characters that cause encoding issues
        if config.ENABLE_ENCODING_CLEANUP:
            text = ''.join(char for char in text if ord(char) < 0xD800 or ord(char) > 0xDFFF)
        
        # Basic cleaning
        text = text.strip()
        
        # Remove excessive whitespace
        import re
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Multiple newlines to double
        text = re.sub(r' +', ' ', text)  # Multiple spaces to single
        
        return text
    
    def get_extraction_capabilities(self) -> Dict[str, Any]:
        """Get extraction capabilities summary."""
        return {
            "capabilities": self.capabilities,
            "supported_formats": self._get_supported_formats(),
            "pdf_methods": self._get_pdf_methods(),
            "content_cleaning": config.ENABLE_CONTENT_CLEANING,
            "encoding_cleanup": config.ENABLE_ENCODING_CLEANUP
        }
    
    def _get_supported_formats(self) -> List[str]:
        """Get list of supported file formats."""
        formats = ["txt", "md", "csv", "json"]
        
        if any(self.capabilities[method] for method in ["pypdf2", "langchain_pypdf", "unstructured", "pymupdf"]):
            formats.append("pdf")
        
        if self.capabilities["python_docx"]:
            formats.extend(["docx", "doc"])
        
        return formats
    
    def _get_pdf_methods(self) -> List[str]:
        """Get available PDF extraction methods."""
        methods = []
        
        if self.capabilities["langchain_pypdf"]:
            methods.append("PyPDFLoader")
        if self.capabilities["unstructured"]:
            methods.append("UnstructuredPDFLoader")
        if self.capabilities["pymupdf"]:
            methods.append("PyMuPDFLoader")
        if self.capabilities["pypdf2"]:
            methods.append("PyPDF2")
        
        methods.append("PlainText")  # Always available as fallback
        
        return methods


# Global extractor instance
text_extractor = TextExtractor()
