"""
Enhanced File Validation Service for AI Agent Platform.
Provides comprehensive file validation with dynamic type support.
"""

import os
import mimetypes
from typing import Optional, Dict, Any, List
from pathlib import Path
from fastapi import HTTPException, UploadFile

# Try to import magic, but handle gracefully if not available
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False

from src.config.document_processing import config


class FileValidationError(Exception):
    """Custom exception for file validation errors."""
    pass


class FileValidator:
    """Enhanced file validator with dynamic type support."""
    
    def __init__(self):
        self.allowed_extensions = config.get_allowed_extensions()
        self.allowed_content_types = config.get_allowed_content_types()
        self.max_file_size = config.MAX_FILE_SIZE_BYTES
        self.capabilities = config.get_processing_capabilities()
    
    def validate_upload_file(self, uploaded_file: UploadFile) -> Dict[str, Any]:
        """
        Comprehensive file validation.
        
        Returns:
            Dict with validation results and file metadata
        """
        validation_result = {
            "valid": False,
            "filename": uploaded_file.filename,
            "content_type": uploaded_file.content_type,
            "detected_type": None,
            "file_extension": None,
            "estimated_size": None,
            "errors": [],
            "warnings": []
        }
        
        try:
            # 1. Basic filename validation
            self._validate_filename(uploaded_file.filename, validation_result)
            
            # 2. File extension validation
            self._validate_file_extension(uploaded_file.filename, validation_result)
            
            # 3. Content type validation
            self._validate_content_type(uploaded_file.content_type, validation_result)
            
            # 4. File size validation (if possible)
            self._validate_file_size(uploaded_file, validation_result)
            
            # 5. Content detection (if magic is available)
            self._detect_file_content(uploaded_file, validation_result)
            
            # 6. Capability check
            self._check_processing_capability(validation_result)
            
            # Set valid if no errors
            validation_result["valid"] = len(validation_result["errors"]) == 0
            
        except Exception as e:
            validation_result["errors"].append(f"Validation error: {str(e)}")
            validation_result["valid"] = False
        
        return validation_result
    
    def _validate_filename(self, filename: Optional[str], result: Dict[str, Any]) -> None:
        """Validate filename."""
        if not filename:
            result["errors"].append("Filename is required")
            return
        
        if len(filename) > 255:
            result["errors"].append("Filename too long (max 255 characters)")
        
        # Check for dangerous characters
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\0']
        if any(char in filename for char in dangerous_chars):
            result["errors"].append("Filename contains invalid characters")
        
        # Extract extension
        result["file_extension"] = Path(filename).suffix.lower()
    
    def _validate_file_extension(self, filename: Optional[str], result: Dict[str, Any]) -> None:
        """Validate file extension."""
        if not filename:
            return
        
        file_ext = Path(filename).suffix.lower()
        result["file_extension"] = file_ext
        
        if not file_ext:
            result["errors"].append("File must have an extension")
            return
        
        if file_ext not in self.allowed_extensions:
            result["errors"].append(
                f"File extension '{file_ext}' not allowed. "
                f"Supported: {', '.join(self.allowed_extensions)}"
            )
    
    def _validate_content_type(self, content_type: Optional[str], result: Dict[str, Any]) -> None:
        """Validate MIME content type."""
        if not content_type:
            result["warnings"].append("No content type provided")
            return
        
        # Normalize content type (remove charset, etc.)
        normalized_type = content_type.split(';')[0].strip().lower()
        result["detected_type"] = normalized_type
        
        if normalized_type not in self.allowed_content_types:
            result["warnings"].append(
                f"Content type '{normalized_type}' not in allowed list. "
                f"Will validate based on file extension."
            )
    
    def _validate_file_size(self, uploaded_file: UploadFile, result: Dict[str, Any]) -> None:
        """Validate file size if possible."""
        try:
            # Try to get file size without reading entire file
            if hasattr(uploaded_file.file, 'seek') and hasattr(uploaded_file.file, 'tell'):
                current_pos = uploaded_file.file.tell()
                uploaded_file.file.seek(0, 2)  # Seek to end
                file_size = uploaded_file.file.tell()
                uploaded_file.file.seek(current_pos)  # Restore position
                
                result["estimated_size"] = file_size
                
                if file_size > self.max_file_size:
                    result["errors"].append(
                        f"File size ({file_size / 1024 / 1024:.1f} MB) exceeds "
                        f"maximum allowed size ({config.MAX_FILE_SIZE_MB} MB)"
                    )
                elif file_size == 0:
                    result["errors"].append("File is empty")
        except Exception as e:
            result["warnings"].append(f"Could not determine file size: {str(e)}")
    
    def _detect_file_content(self, uploaded_file: UploadFile, result: Dict[str, Any]) -> None:
        """Detect file content using magic numbers if available."""
        if not MAGIC_AVAILABLE:
            result["warnings"].append("Advanced content detection not available (python-magic not installed)")
            return

        try:
            # Read first 2048 bytes for magic detection
            current_pos = uploaded_file.file.tell()
            sample = uploaded_file.file.read(2048)
            uploaded_file.file.seek(current_pos)

            if sample:
                detected_mime = magic.from_buffer(sample, mime=True)
                result["detected_type"] = detected_mime

                # Cross-validate with declared content type
                if uploaded_file.content_type:
                    declared_type = uploaded_file.content_type.split(';')[0].strip().lower()
                    if detected_mime != declared_type:
                        result["warnings"].append(
                            f"Detected content type '{detected_mime}' differs from "
                            f"declared type '{declared_type}'"
                        )
        except Exception as e:
            result["warnings"].append(f"Content detection failed: {str(e)}")
    
    def _check_processing_capability(self, result: Dict[str, Any]) -> None:
        """Check if we can process this file type."""
        file_ext = result.get("file_extension", "").lower()
        
        if file_ext == ".pdf" and not self.capabilities["pdf_support"]:
            result["errors"].append("PDF processing not available (PyPDF2 not installed)")
        
        if file_ext in [".docx", ".doc"] and not self.capabilities["docx_support"]:
            result["errors"].append("DOCX processing not available (python-docx not installed)")
    
    def validate_and_raise(self, uploaded_file: UploadFile) -> Dict[str, Any]:
        """
        Validate file and raise HTTPException if invalid.
        
        Returns:
            Validation result if valid
        """
        result = self.validate_upload_file(uploaded_file)
        
        if not result["valid"]:
            error_msg = "; ".join(result["errors"])
            raise HTTPException(
                status_code=400,
                detail=f"File validation failed: {error_msg}"
            )
        
        return result
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of validation capabilities."""
        return {
            "allowed_extensions": self.allowed_extensions,
            "allowed_content_types": self.allowed_content_types,
            "max_file_size_mb": config.MAX_FILE_SIZE_MB,
            "processing_capabilities": self.capabilities,
            "advanced_detection": self._has_magic_support()
        }
    
    def _has_magic_support(self) -> bool:
        """Check if python-magic is available."""
        return MAGIC_AVAILABLE


# Global validator instance
file_validator = FileValidator()
