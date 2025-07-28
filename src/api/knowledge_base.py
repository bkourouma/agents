"""
Knowledge Base API endpoints for the AI Agent Platform.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
import io
import PyPDF2
from datetime import datetime

from src.core.database import get_db
from src.api.users import get_current_user_from_token
from src.models.user import User
from src.models.agent import Agent
from src.agents.service import AgentService
from src.tools.knowledge_base import (
    KnowledgeBaseTool,
    KnowledgeBaseDocumentCreate,
    KnowledgeBaseDocumentResponse,
    KnowledgeBaseSearchRequest,
    KnowledgeBaseSearchResult
)
from src.services.file_validation import file_validator
from src.services.text_extraction import text_extractor
from src.services.file_storage import file_storage
from src.services.content_processing import content_processor
from src.config.document_processing import config

router = APIRouter(prefix="/agents/{agent_id}/knowledge-base", tags=["knowledge-base"])


def extract_text_from_pdf(pdf_content: bytes) -> str:
    """Extract text content from PDF bytes."""
    try:
        pdf_file = io.BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        text_content = []
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text_content.append(page.extract_text())

        return "\n".join(text_content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to extract text from PDF: {str(e)}"
        )


async def get_agent_with_permission(
    agent_id: int,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db)
) -> Agent:
    """Get agent and verify user has permission to access it."""
    agent = await AgentService.get_agent(db, agent_id, current_user)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found or access denied"
        )
    return agent


@router.get("/upload-capabilities")
async def get_upload_capabilities(
    agent_id: int,
    agent: Agent = Depends(get_agent_with_permission)
):
    """Get file upload capabilities and validation rules."""
    return {
        "validation_rules": file_validator.get_validation_summary(),
        "text_extraction": text_extractor.get_extraction_capabilities(),
        "content_processing": content_processor.get_processing_capabilities(),
        "processing_config": {
            "chunk_size": config.CHUNK_SIZE,
            "chunk_overlap": config.CHUNK_OVERLAP,
            "max_file_size_mb": config.MAX_FILE_SIZE_MB,
            "embedding_model": config.EMBEDDING_MODEL,
            "content_cleaning": config.ENABLE_CONTENT_CLEANING,
            "encoding_cleanup": config.ENABLE_ENCODING_CLEANUP
        }
    }


@router.get("/storage-stats")
async def get_storage_stats(
    agent_id: int,
    agent: Agent = Depends(get_agent_with_permission)
):
    """Get storage statistics for the agent."""
    try:
        stats = file_storage.get_storage_stats(agent_id)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get storage stats: {str(e)}"
        )


@router.post("/documents", response_model=KnowledgeBaseDocumentResponse)
async def add_document(
    agent_id: int,
    document: KnowledgeBaseDocumentCreate,
    agent: Agent = Depends(get_agent_with_permission),
    db: AsyncSession = Depends(get_db)
):
    """Add a document to the agent's knowledge base."""
    # Check if agent has knowledge_base tool enabled
    if not agent.tools_config or "knowledge_base" not in agent.tools_config.get("enabled_tools", []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Knowledge base tool is not enabled for this agent"
        )
    
    # Use enhanced knowledge base manager with tenant support
    from src.tools.knowledge_base import get_enhanced_knowledge_base_manager
    kb_manager = get_enhanced_knowledge_base_manager(agent_id, str(agent.tenant_id))
    try:
        db_document = await kb_manager.add_document(
            db=db,
            title=document.title,
            content=document.content,
            content_type=document.content_type,
            metadata=document.metadata,
            tenant_id=str(agent.tenant_id)
        )
        if db_document:
            return KnowledgeBaseDocumentResponse.model_validate(db_document)
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add document to knowledge base"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/documents/upload", response_model=KnowledgeBaseDocumentResponse)
async def upload_document(
    agent_id: int,
    file: UploadFile = File(..., description="File to upload"),
    title: str = Form(None, description="Optional title for the document"),
    agent: Agent = Depends(get_agent_with_permission),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a file to the agent's knowledge base.

    Supports text files (.txt, .md, .csv) and PDF files (.pdf).
    """
    print(f"🚀 Starting upload for agent {agent_id}")
    print(f"📄 File details:")
    print(f"   Filename: {file.filename}")
    print(f"   Content type: {file.content_type}")
    print(f"   Title: {title}")

    # Enhanced file validation
    validation_result = file_validator.validate_and_raise(file)
    print(f"✅ File validation passed:")
    print(f"   Detected type: {validation_result.get('detected_type')}")
    print(f"   File extension: {validation_result.get('file_extension')}")
    print(f"   Estimated size: {validation_result.get('estimated_size', 'unknown')} bytes")

    if validation_result.get("warnings"):
        for warning in validation_result["warnings"]:
            print(f"⚠️ Warning: {warning}")

    # Check if agent has knowledge_base tool enabled
    if not agent.tools_config or "knowledge_base" not in agent.tools_config.get("enabled_tools", []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Knowledge base tool is not enabled for this agent"
        )

    try:
        # Read file content
        content = await file.read()
        print(f"   Content size: {len(content)} bytes")

        if len(content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )

        # Enhanced text extraction using multi-method approach
        file_content_type = validation_result.get('detected_type') or file.content_type or "text/plain"

        print(f"📄 Processing file: {file.filename}")
        print(f"📄 Content type: {file_content_type}")
        print(f"📄 File size: {len(content)} bytes")

        try:
            content_str = text_extractor.extract_text_from_file(
                content=content,
                content_type=file_content_type,
                filename=file.filename
            )
            print(f"✅ Text extraction successful, extracted {len(content_str)} characters")

            # Use the detected content type for storage
            if validation_result.get('file_extension') == '.pdf':
                file_content_type = "application/pdf"
            elif validation_result.get('file_extension') in ['.docx', '.doc']:
                file_content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

        except Exception as e:
            print(f"❌ Text extraction failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to extract text from file: {str(e)}"
            )

        # Use basic knowledge base tool with tenant support
        kb_tool = KnowledgeBaseTool(agent_id, str(agent.tenant_id))

        # Validate extracted content
        if not content_str.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No text content could be extracted from the file"
            )

        # Process content with advanced content processing
        print(f"🔧 Processing content with advanced content processor...")
        try:
            processing_result = content_processor.process_content(
                content=content_str,
                content_type=file_content_type,
                custom_config=None  # Use default configuration
            )

            # Use processed content
            processed_content = processing_result["cleaned_content"]
            content_chunks = processing_result["chunks"]

            print(f"✅ Content processed successfully:")
            print(f"  Original length: {processing_result['original_length']} chars")
            print(f"  Processed length: {len(processed_content)} chars")
            print(f"  Chunks created: {processing_result['chunk_count']}")

        except Exception as e:
            print(f"⚠️ Content processing failed (using raw content): {e}")
            processed_content = content_str
            content_chunks = []
            processing_result = None

        # Store file using enhanced file storage
        print(f"💾 Storing file using enhanced storage system...")
        try:
            # Generate content hash for the original file content
            import hashlib
            content_hash = hashlib.sha256(content).hexdigest()

            # Store the original file
            storage_result = file_storage.store_document_file(
                agent_id=agent_id,
                file_content=content,
                original_filename=file.filename,
                content_hash=content_hash,
                metadata={
                    "content_type": file_content_type,
                    "extracted_text_length": len(content_str),
                    "processed_text_length": len(processed_content),
                    "upload_timestamp": datetime.now().isoformat(),
                    "validation_result": validation_result,
                    "processing_result": processing_result
                }
            )
            print(f"✅ File stored successfully: {storage_result['unique_filename']}")

        except Exception as e:
            print(f"⚠️ File storage failed (continuing with database-only storage): {e}")
            storage_result = None

        # Create document with processed content
        document_create = KnowledgeBaseDocumentCreate(
            title=title or file.filename,
            content=processed_content,  # Use processed content instead of raw
            content_type=file_content_type,
            file_path=storage_result['relative_path'] if storage_result else None,
            metadata={
                "original_filename": file.filename,
                "file_size": len(content),
                "content_hash": content_hash,
                "storage_info": storage_result,
                "processing_info": {
                    "original_length": len(content_str),
                    "processed_length": len(processed_content),
                    "chunks_created": len(content_chunks),
                    "processing_result": processing_result
                }
            } if storage_result else {
                "original_filename": file.filename,
                "processing_info": {
                    "original_length": len(content_str),
                    "processed_length": len(processed_content),
                    "chunks_created": len(content_chunks),
                    "processing_result": processing_result
                }
            }
        )

        print(f"📝 Creating document with title: {document_create.title}")

        # Add document to knowledge base with tenant support
        document = await kb_tool.add_document(db, document_create, str(agent.tenant_id))

        print(f"✅ Document created successfully with ID: {document.id}")

        return KnowledgeBaseDocumentResponse.model_validate(document)

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Upload error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )
#
#     kb_tool = KnowledgeBaseTool(agent_id)
#     try:
#         db_document = await kb_tool.add_document(db, document)
#         return KnowledgeBaseDocumentResponse.from_orm(db_document)
#     except ValueError as e:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=str(e)
#         )


@router.post("/search", response_model=List[KnowledgeBaseSearchResult])
async def search_knowledge_base(
    agent_id: int,
    search_request: KnowledgeBaseSearchRequest,
    agent: Agent = Depends(get_agent_with_permission),
    db: AsyncSession = Depends(get_db)
):
    """Search the agent's knowledge base."""
    # Check if agent has knowledge_base tool enabled
    if not agent.tools_config or "knowledge_base" not in agent.tools_config.get("enabled_tools", []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Knowledge base tool is not enabled for this agent"
        )
    
    # Use enhanced knowledge base manager with tenant support
    from src.tools.knowledge_base import get_enhanced_knowledge_base_manager
    kb_manager = get_enhanced_knowledge_base_manager(agent_id, str(agent.tenant_id))
    results = await kb_manager.search_documents(db, search_request, str(agent.tenant_id))
    return results


@router.get("/documents", response_model=List[KnowledgeBaseDocumentResponse])
async def list_documents(
    agent_id: int,
    limit: int = 50,
    agent: Agent = Depends(get_agent_with_permission),
    db: AsyncSession = Depends(get_db)
):
    """List all documents in the agent's knowledge base."""
    # Check if agent has knowledge_base tool enabled
    if not agent.tools_config or "knowledge_base" not in agent.tools_config.get("enabled_tools", []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Knowledge base tool is not enabled for this agent"
        )
    
    # Use enhanced knowledge base manager
    from src.tools.knowledge_base import get_enhanced_knowledge_base_manager
    kb_manager = get_enhanced_knowledge_base_manager(agent_id)
    documents = await kb_manager.list_documents(db, limit)
    return [KnowledgeBaseDocumentResponse.model_validate(doc) for doc in documents]


@router.get("/documents/{document_id}", response_model=KnowledgeBaseDocumentResponse)
async def get_document(
    agent_id: int,
    document_id: int,
    agent: Agent = Depends(get_agent_with_permission),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific document from the agent's knowledge base."""
    # Check if agent has knowledge_base tool enabled
    if not agent.tools_config or "knowledge_base" not in agent.tools_config.get("enabled_tools", []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Knowledge base tool is not enabled for this agent"
        )
    
    kb_tool = KnowledgeBaseTool(agent_id)
    document = await kb_tool.get_document(db, document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return KnowledgeBaseDocumentResponse.model_validate(document)


@router.delete("/documents/{document_id}")
async def delete_document(
    agent_id: int,
    document_id: int,
    agent: Agent = Depends(get_agent_with_permission),
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db)
):
    """Delete a document from the agent's knowledge base."""
    # Check if agent has knowledge_base tool enabled
    if not agent.tools_config or "knowledge_base" not in agent.tools_config.get("enabled_tools", []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Knowledge base tool is not enabled for this agent"
        )

    # Only allow deletion if user owns the agent
    if agent.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the agent owner can delete documents"
        )

    kb_tool = KnowledgeBaseTool(agent_id)
    success = await kb_tool.delete_document(db, document_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    return {"message": "Document deleted successfully"}
