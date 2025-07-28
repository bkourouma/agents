# Document Ingestion Pipeline

## 📋 Overview

This document provides a comprehensive guide to the document ingestion pipeline in the Chat360 platform, covering the complete flow from file upload to storage in the knowledge base system.

## 🔄 Pipeline Flow

```
File Upload → Validation → Text Extraction → Content Processing → Embedding Generation → Vector Storage → Database Storage → Response
```

## 1. 📤 File Upload Endpoints

### Visitor Chat System
**Endpoint:** `POST /visitor-docs/{tenant_id}/`

```python
@router.post("/", response_model=DocumentUploadResponse)
async def upload_visitor_doc(
    tenant_id: int,
    file: UploadFile = File(...),
    current_tenant: int = Depends(get_current_tenant),
):
    """
    Upload a PDF for a given tenant.
    - Only PDF allowed. 
    - Saves file under visitor_docs/tenant_{tenant_id}/, then ingests into Chroma.
    """
```

### Chat Assistant System
**Endpoint:** `POST /api/chat-assistant/documents/upload`

```python
@router.post("/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(...),
    category: str = Form(None),
    tags: str = Form(None),
    language: str = Form("fr")
):
    """Upload and process a document for the knowledge base."""
```

### Legacy System
**Endpoint:** `POST /api/documents/`

```python
@router.post("/", response_model=DocumentRead)
async def upload_document(
    tenant_id: int = Form(...),
    title: str = Form(...),
    description: str = Form(""),
    uploaded_by: str = Form(...),
    file: UploadFile = File(...)
):
```

## 2. 🔍 File Validation

### Content Type Validation

```python
@staticmethod
def validate_upload_file(uploaded_file: UploadFile) -> None:
    """Validate uploaded file before processing"""
    # Check file extension
    if not uploaded_file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier manquant")
    
    file_ext = Path(uploaded_file.filename).suffix.lower()
    if file_ext not in VisitorChatConfig.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Extension non autorisée. Seuls {', '.join(VisitorChatConfig.ALLOWED_EXTENSIONS)} sont acceptés."
        )
```

### Supported File Types

- **PDF**: Primary format for document ingestion
- **DOCX**: Microsoft Word documents
- **TXT**: Plain text files
- **Markdown**: Markdown formatted files

### Dynamic File Type Support

```python
# Dynamic file type validation based on available libraries
allowed_types = ['text/plain', 'text/markdown']

if PDF_SUPPORT:
    allowed_types.append('application/pdf')

if DOCX_SUPPORT:
    allowed_types.extend([
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ])
```

## 3. 💾 File Storage

### Tenant-Isolated Storage Structure

```
📁 Project Root
├── 📁 visitor_docs/
│   └── 📁 tenant_{tenant_id}/
│       └── 📄 {uuid}_{filename}.pdf
├── 📁 visitor_chroma/
│   └── 📁 tenant_{tenant_id}/
│       └── 🗂️ visitor_collection/
└── 📄 chatbot.sqlite
    └── 🗃️ chat_documents table
```

### File Naming Convention

```python
@staticmethod
def save_uploaded_file(tenant_id: int, uploaded_file: UploadFile) -> str:
    """
    Save the incoming UploadFile under visitor_docs/tenant_{tenant_id}/
    with a unique prefix to avoid filename collisions.
    """
    # Validate first
    DocumentService.validate_upload_file(uploaded_file)
    
    docs_path, _ = DocumentService.ensure_tenant_dirs(tenant_id)

    # Prefix with a random UUID to avoid filename collisions
    unique_filename = f"{uuid.uuid4().hex}_{uploaded_file.filename}"
    dest_path = os.path.join(docs_path, unique_filename)
```

## 4. 📄 Text Extraction

### Multi-Method PDF Processing

The system uses multiple fallback methods for robust PDF text extraction:

1. **PyPDFLoader** (Primary)
2. **UnstructuredPDFLoader** (Fallback 1)
3. **PyMuPDFLoader** (Fallback 2)
4. **Manual pypdf extraction** (Fallback 3)
5. **Plain text reading** (Last resort)

```python
def load_pdf_with_fallback(file_path: str):
    # Method 1: Try PyPDFLoader first
    try:
        from langchain_community.document_loaders import PyPDFLoader
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        return pages
    except Exception as e:
        print(f"[ERROR] PyPDFLoader failed: {e}")
    
    # Additional fallback methods...
```

### Content Type-Specific Extraction

```python
async def extract_text_from_file(content: bytes, content_type: str, filename: str) -> str:
    """Extract text content from various file types."""
    
    if content_type == 'application/pdf':
        return extract_pdf_text(content)
    elif content_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
        return extract_docx_text(content)
    elif content_type == 'text/plain':
        return content.decode('utf-8')
    elif content_type == 'text/markdown':
        return content.decode('utf-8')
    else:
        raise ValueError(f"Type de fichier non supporté: {content_type}")
```

## 5. ✂️ Content Processing & Chunking

### Text Chunking Strategy

```python
@staticmethod
def ingest_pdf(tenant_id: int, file_path: str) -> None:
    """
    1. Load the PDF via PyPDFLoader.
    2. Split it into smaller "chunks".
    3. Embed those chunks and add to a Chroma collection
    """
    # 1) Load PDF
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    
    if not docs:
        raise HTTPException(status_code=400, detail="Le PDF semble être vide ou corrompu")

    # 2) Split into blocks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=VisitorChatConfig.CHUNK_SIZE,  # Default: 1000
        chunk_overlap=VisitorChatConfig.CHUNK_OVERLAP  # Default: 200
    )
    chunks = splitter.split_documents(docs)
    
    if not chunks:
        raise HTTPException(status_code=400, detail="Aucun contenu extractible du PDF")
```

### Configuration Parameters

- **CHUNK_SIZE**: 1000 characters (configurable via environment)
- **CHUNK_OVERLAP**: 200 characters (configurable via environment)
- **OPENAI_MODEL**: gpt-3.5-turbo (configurable via environment)
- **OPENAI_TEMPERATURE**: 0.0 (configurable via environment)

## 6. 🧠 Embedding Generation

### OpenAI Embeddings (Primary Method)

```python
# 3) Embed + index
_, chroma_path = DocumentService.ensure_tenant_dirs(tenant_id)
embeddings = OpenAIEmbeddings()
collection = Chroma(
    collection_name="visitor_collection",
    embedding_function=embeddings,
    persist_directory=chroma_path,
)

# Add all chunks to the tenant's "visitor_collection"
collection.add_documents(chunks)
collection.persist()
```

### Alternative Embedding Models

```python
# Generate embedding if model is available
if embedding_model:
    try:
        embedding = embedding_model.encode(extracted_text)
        document.embedding_vector = embedding.tolist()
        logger.info(f"Generated embedding for document {document.id}")
    except Exception as e:
        logger.warning(f"Failed to generate embedding: {e}")
```

### Supported Embedding Models

- **OpenAI Embeddings** (Primary)
- **Sentence Transformers** (paraphrase-multilingual-MiniLM-L12-v2)
- **TF-IDF** (Fallback)

## 7. 🗄️ Database Storage

### Document Metadata Schema

```sql
CREATE TABLE IF NOT EXISTS chat_documents (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    document_type TEXT,
    embedding_vector TEXT, -- JSON string of float array
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

### Document Repository Operations

```python
def create_document(self, document: ChatDocument) -> ChatDocument:
    """Create a new chat document"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO chat_documents (
                id, tenant_id, title, content, document_type, 
                embedding_vector, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            document.id,
            document.tenant_id,
            document.title,
            document.content,
            document.document_type,
            json.dumps(document.embedding_vector),
            document.created_at.isoformat(),
            document.updated_at.isoformat()
        ))
        conn.commit()
        return document
    finally:
        conn.close()
```

## 8. 🔄 Error Handling & Cleanup

### Automatic Cleanup on Failure

```python
except Exception as e:
    # Clean up the file if ingestion fails
    if os.path.exists(file_path):
        os.remove(file_path)
    raise HTTPException(status_code=500, detail=f"Erreur lors de l'indexation: {str(e)}")
```

### Content Encoding Cleanup

```python
# Clean pages content to handle encoding issues
cleaned_pages = []
for i, page in enumerate(pages):
    try:
        # Clean the content by removing problematic characters
        cleaned_content = page.page_content.encode('utf-8', errors='ignore').decode('utf-8')
        # Remove surrogate characters that cause encoding issues
        cleaned_content = ''.join(char for char in cleaned_content if ord(char) < 0xD800 or ord(char) > 0xDFFF)
        page.page_content = cleaned_content
        cleaned_pages.append(page)
    except Exception as e:
        print(f"[WARNING] Error processing page {i+1}: {e}")
        # Skip problematic pages
        continue

## 9. 🔄 Refresh & Reingestion

### Document Refresh Process

The system supports complete document refresh and reingestion:

```python
# Delete the entire tenant's Chroma directory to rebuild from scratch
try:
    collection = Chroma(
        collection_name="visitor_collection",
        embedding_function=OpenAIEmbeddings(),
        persist_directory=chroma_path,
    )
    collection.delete_collection()
except:
    # If delete_collection fails, try to remove the directory manually
    if os.path.exists(chroma_path):
        shutil.rmtree(chroma_path)
        os.makedirs(chroma_path, exist_ok=True)

# Re-ingest any leftover PDFs
remaining_files = [f for f in os.listdir(docs_path) if os.path.isfile(os.path.join(docs_path, f))]

if remaining_files:
    for f in remaining_files:
        file_path = os.path.join(docs_path, f)
        try:
            loader = PyPDFLoader(file_path)
            docs = loader.load()
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=VisitorChatConfig.CHUNK_SIZE,
                chunk_overlap=VisitorChatConfig.CHUNK_OVERLAP
            )
            chunks = splitter.split_documents(docs)

            # Re-add them to a fresh index
            collection = Chroma(
                collection_name="visitor_collection",
                embedding_function=OpenAIEmbeddings(),
                persist_directory=chroma_path,
            )
            collection.add_documents(chunks)
        except Exception as e:
            print(f"Warning: Failed to re-index {f}: {str(e)}")
```

### Embedding Refresh

```python
@require_tenant_context
def refresh_all_embeddings(self) -> Dict[str, Any]:
    """
    Refresh embeddings for all documents (regenerate even if they exist)
    """
    tenant_id = TenantContext.get_tenant_id()
    documents = self.document_repository.get_documents_by_tenant(tenant_id)

    processed_count = 0
    errors = []

    for document in documents:
        try:
            if document.content:
                # Generate new embedding
                embedding = self.generate_embedding(document.content)

                # Update document
                success = self.document_repository.update_document_embedding(
                    tenant_id, document.id, embedding
                )

                if success:
                    processed_count += 1
                else:
                    errors.append(f"Échec de mise à jour pour {document.title}")
            else:
                errors.append(f"Document {document.title} n'a pas de contenu")

        except Exception as e:
            errors.append(f"Erreur pour {document.title}: {str(e)}")

    return {
        "success": True,
        "message": f"{processed_count} embeddings régénérés avec succès.",
        "processed_count": processed_count,
        "errors": errors if errors else None
    }
```

## 10. 🏗️ Architecture Summary

### Key Components

1. **File Upload Handlers**
   - Visitor Chat System (`/visitor-docs/{tenant_id}/`)
   - Chat Assistant System (`/api/chat-assistant/documents/upload`)
   - Legacy System (`/api/documents/`)

2. **Validation Layer**
   - File type validation
   - Content validation
   - Size limits
   - Encoding checks

3. **Text Extraction Engine**
   - Multi-method PDF processing
   - Content type-specific extractors
   - Fallback mechanisms
   - Encoding cleanup

4. **Processing Pipeline**
   - Text chunking with overlap
   - Content cleaning
   - Metadata extraction

5. **Embedding Generation**
   - OpenAI Embeddings (primary)
   - Sentence Transformers (fallback)
   - TF-IDF (basic fallback)

6. **Storage Systems**
   - **Vector Storage**: ChromaDB for semantic search
   - **Metadata Storage**: SQLite for document metadata
   - **File Storage**: Tenant-isolated filesystem

### Security Features

- **Multi-tenant isolation**: Complete separation per tenant
- **Access control**: Tenant-based authentication
- **File validation**: Strict content type checking
- **Path sanitization**: UUID-based filename generation
- **Error isolation**: Tenant-specific error handling

### Performance Optimizations

- **Chunking strategy**: Optimized chunk size and overlap
- **Batch processing**: Multiple documents in single operations
- **Lazy loading**: On-demand embedding generation
- **Caching**: Persistent vector storage
- **Fallback methods**: Multiple PDF processing options

## 11. 📊 Monitoring & Metrics

### Document Processing Metrics

```python
def get_embedding_stats(self) -> Dict[str, Any]:
    """Get embedding statistics for monitoring"""
    try:
        tenant_id = TenantContext.get_tenant_id()
        documents = self.document_repository.get_documents_by_tenant(tenant_id)

        total_docs = len(documents)
        docs_with_embeddings = sum(1 for doc in documents if doc.has_embedding())
        docs_without_embeddings = total_docs - docs_with_embeddings

        return {
            "total_documents": total_docs,
            "documents_with_embeddings": docs_with_embeddings,
            "documents_without_embeddings": docs_without_embeddings,
            "embedding_coverage": (docs_with_embeddings / total_docs * 100) if total_docs > 0 else 0,
            "embedding_dimension": self.embedding_dimension,
            "model_type": "sentence-transformers" if self.embedding_model != "tfidf" else "tfidf"
        }
    except Exception:
        return {
            "total_documents": 0,
            "documents_with_embeddings": 0,
            "documents_without_embeddings": 0,
            "embedding_coverage": 0,
            "embedding_dimension": self.embedding_dimension,
            "model_type": "unknown"
        }
```

### Health Checks

- Document processing success rate
- Embedding generation status
- Vector database connectivity
- File storage availability
- Processing time metrics

## 12. 🔧 Configuration

### Environment Variables

```bash
# Document Processing
VISITOR_CHUNK_SIZE=1000
VISITOR_CHUNK_OVERLAP=200
VISITOR_RATE_LIMIT=10

# OpenAI Configuration
OPENAI_API_KEY=your_openai_key
VISITOR_OPENAI_MODEL=gpt-3.5-turbo
VISITOR_OPENAI_TEMPERATURE=0.0

# Storage Paths
CHROMA_DB_DIR=chroma_db_data
SQLITE_PATH=./sqlite_data/chatbot.sqlite

# File Limits
MAX_FILE_SIZE_MB=10
ALLOWED_EXTENSIONS=.pdf,.docx,.txt,.md
```

### Configuration Class

```python
class VisitorChatConfig:
    # File upload limits
    MAX_FILE_SIZE_MB: int = int(os.getenv("VISITOR_MAX_FILE_SIZE_MB", "10"))
    ALLOWED_EXTENSIONS: List[str] = [".pdf"]

    # Document processing
    CHUNK_SIZE: int = int(os.getenv("VISITOR_CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("VISITOR_CHUNK_OVERLAP", "200"))

    # OpenAI settings
    OPENAI_MODEL: str = os.getenv("VISITOR_OPENAI_MODEL", "gpt-3.5-turbo")
    OPENAI_TEMPERATURE: float = float(os.getenv("VISITOR_OPENAI_TEMPERATURE", "0.0"))

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("VISITOR_RATE_LIMIT", "10"))
```

## 13. 🚀 Integration Guide

### For External Applications

#### 1. Document Upload

```bash
curl -X POST "http://localhost:8000/visitor-docs/{tenant_id}/" \
  -H "Authorization: Bearer {token}" \
  -F "file=@document.pdf"
```

#### 2. Chat with Documents

```bash
curl -X POST "http://localhost:8000/visitor-chat/{tenant_id}/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -d '{
    "session_id": "unique_session_id",
    "question": "What is the company policy on vacation?"
  }'
```

#### 3. Response Format

```json
{
  "answer": "Based on the documents...",
  "sources": ["document1.pdf", "document2.pdf"],
  "time_taken": 1.23,
  "has_context": true
}
```

### Integration Steps

1. **Set up authentication** with tenant-based access
2. **Configure environment variables** for your setup
3. **Install required dependencies** from requirements.txt
4. **Initialize tenant directories** for document storage
5. **Upload documents** via the upload API
6. **Implement chat interface** using the chat API
7. **Handle responses** and display sources to users

## 14. 🔍 Troubleshooting

### Common Issues

1. **PDF Processing Failures**
   - Check file corruption
   - Verify PDF format compatibility
   - Review encoding issues

2. **Embedding Generation Errors**
   - Validate OpenAI API key
   - Check network connectivity
   - Monitor rate limits

3. **Storage Issues**
   - Verify directory permissions
   - Check disk space
   - Validate ChromaDB installation

4. **Performance Problems**
   - Optimize chunk size
   - Review embedding model choice
   - Monitor memory usage

### Debug Commands

```bash
# Test PDF processing
python test_pdf_processing.py

# Validate embeddings
python test_embeddings.py

# Check storage connectivity
python test_storage.py

# Monitor processing pipeline
python monitor_pipeline.py
```

## 15. 📚 Dependencies

### Core Requirements

```txt
fastapi>=0.100.0,<0.112.0
langchain>=0.1.0,<0.2.0
langchain-openai>=0.0.5,<0.2.0
langchain-chroma>=0.1.0,<0.2.0
chromadb>=0.4.0,<0.5.0
pypdf>=3.0.0,<4.0.0
openai>=1.0.0,<2.0.0
sentence-transformers>=2.2.2
python-dotenv>=0.20.0,<1.1.0
```

### Optional Dependencies

```txt
PyPDF2>=3.0.0          # Alternative PDF processing
python-docx>=0.8.11    # DOCX support
unstructured>=0.10.0   # Advanced document processing
pymupdf>=1.23.0        # Alternative PDF processing
```

---

## 📝 Conclusion

This document ingestion pipeline provides a robust, scalable solution for processing documents in a multi-tenant environment. The system handles various file formats, provides multiple fallback mechanisms, and ensures data isolation between tenants while maintaining high performance and reliability.

For questions or support, please refer to the main project documentation or contact the development team.
```
