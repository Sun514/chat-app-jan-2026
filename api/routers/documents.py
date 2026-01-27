# api/routers/documents.py
"""
FastAPI router for document upload, storage, and semantic search.
"""

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


# ============================================================================
# Response Models
# ============================================================================

class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    title: Optional[str] = None
    author: Optional[str] = None
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    slide_count: Optional[int] = None
    sheet_count: Optional[int] = None
    investigation_id: Optional[str] = None
    created_at: str


class DocumentUploadResult(BaseModel):
    success: bool
    document_id: Optional[str] = None
    filename: str
    chunk_count: int = 0
    message: str


class DocumentUploadBatchResponse(BaseModel):
    success: bool
    results: list[DocumentUploadResult]
    total: int
    succeeded: int
    failed: int


class ChunkSearchResult(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    file_type: str
    content: str
    source: Optional[str] = None
    heading: Optional[str] = None
    page_number: Optional[int] = None
    similarity: float


class SearchResponse(BaseModel):
    query: str
    results: list[ChunkSearchResult]
    total_results: int


class HybridSearchResult(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    content: str
    source: Optional[str] = None
    semantic_score: float
    text_score: float
    combined_score: float


class DocumentChunkResponse(BaseModel):
    id: str
    chunk_index: int
    content: str
    source: Optional[str] = None
    heading: Optional[str] = None
    page_number: Optional[int] = None
    char_count: int


class SupportedTypesResponse(BaseModel):
    extensions: list[str]
    count: int


# ============================================================================
# Dependencies
# ============================================================================

async def get_document_storage():
    """
    Dependency to get document storage service.
    
    In your actual app, wire this up to your database pool:
    
    from api.core.database import get_pool
    from api.services.documents import DocumentStorageService
    
    pool = await get_pool()
    return DocumentStorageService(pool)
    """
    # Import here to avoid circular imports
    from api.core.database import get_pool
    from api.services.documents.document_storage_service import DocumentStorageService
    
    pool = await get_pool()
    return DocumentStorageService(pool)


async def get_parser_service():
    """Get document parser service."""
    from api.services.documents import DocumentParserService
    return DocumentParserService()


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/supported-types", response_model=SupportedTypesResponse)
async def get_supported_types(
    parser = Depends(get_parser_service),
):
    """Get list of supported file types for upload."""
    extensions = parser.get_supported_extensions()
    return SupportedTypesResponse(
        extensions=extensions,
        count=len(extensions),
    )


@router.post("/upload", response_model=DocumentUploadBatchResponse)
async def upload_document(
    files: list[UploadFile] = File(...),
    investigation_id: Optional[str] = Form(default=None),
    chunk_size: int = Form(default=1000, ge=100, le=10000),
    chunk_overlap: int = Form(default=200, ge=0, le=1000),
    storage = Depends(get_document_storage),
    parser = Depends(get_parser_service),
):
    """
    Upload and process a document.
    
    The document will be:
    1. Parsed to extract text content
    2. Split into chunks for semantic search
    3. Converted to vector embeddings (384-dim)
    4. Stored in PostgreSQL with pgvector
    
    Supported formats: .docx, .doc, .pptx, .ppt, .xlsx, .xls, .csv,
                       .pdf, .txt, .md, .html, .json, .xml, .rtf, .eml
    
    Args:
        files: Document files to upload
        investigation_id: Optional investigation to associate document with
        chunk_size: Maximum characters per text chunk (affects search granularity)
        chunk_overlap: Character overlap between chunks (maintains context)
        
    Returns:
        Processing results for all documents
    """
    results: list[DocumentUploadResult] = []
    supported = ", ".join(parser.get_supported_extensions())

    for file in files:
        filename = file.filename or "unknown"

        if not parser.is_supported(filename):
            results.append(DocumentUploadResult(
                success=False,
                filename=filename,
                chunk_count=0,
                message=f"Unsupported file type. Supported: {supported}",
            ))
            continue

        try:
            doc_id = await storage.store_document(
                file.file,
                filename,
                investigation_id=investigation_id,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )

            if doc_id:
                chunks = await storage.get_document_chunks(doc_id)
                results.append(DocumentUploadResult(
                    success=True,
                    document_id=doc_id,
                    filename=filename,
                    chunk_count=len(chunks),
                    message=f"Document processed successfully with {len(chunks)} chunks",
                ))
            else:
                results.append(DocumentUploadResult(
                    success=False,
                    filename=filename,
                    chunk_count=0,
                    message="Failed to process document",
                ))
        except Exception as e:
            logger.error(f"Error uploading document {filename}: {e}")
            results.append(DocumentUploadResult(
                success=False,
                filename=filename,
                chunk_count=0,
                message=str(e),
            ))

    succeeded = sum(1 for r in results if r.success)
    failed = len(results) - succeeded

    return DocumentUploadBatchResponse(
        success=failed == 0,
        results=results,
        total=len(results),
        succeeded=succeeded,
        failed=failed,
    )


@router.get("/search", response_model=SearchResponse)
async def search_documents(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(default=20, ge=1, le=100),
    threshold: float = Query(default=0.5, ge=0, le=1, description="Minimum similarity"),
    investigation_id: Optional[str] = Query(default=None),
    storage = Depends(get_document_storage),
):
    """
    Semantic search across document chunks.
    
    Finds document chunks that are semantically similar to the query,
    even if they don't contain the exact words.
    
    Args:
        q: Search query text
        limit: Maximum number of results
        threshold: Minimum similarity score (0-1, higher = more similar)
        investigation_id: Filter results to specific investigation
        
    Returns:
        Ranked list of matching document chunks with similarity scores
    """
    try:
        results = await storage.search_similar(
            query=q,
            limit=limit,
            similarity_threshold=threshold,
            investigation_id=investigation_id,
        )
        
        return SearchResponse(
            query=q,
            results=[
                ChunkSearchResult(
                    chunk_id=str(r['chunk_id']),
                    document_id=str(r['document_id']),
                    filename=r['filename'],
                    file_type=r['file_type'],
                    content=r['content'],
                    source=r['source'],
                    heading=r['heading'],
                    page_number=r['page_number'],
                    similarity=r['similarity'],
                )
                for r in results
            ],
            total_results=len(results),
        )
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/search/hybrid", response_model=list[HybridSearchResult])
async def search_documents_hybrid(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=20, ge=1, le=100),
    semantic_weight: float = Query(default=0.7, ge=0, le=1),
    investigation_id: Optional[str] = Query(default=None),
    storage = Depends(get_document_storage),
):
    """
    Hybrid search combining semantic similarity and full-text search.
    
    Best for queries that might benefit from both:
    - Semantic understanding (finds related concepts)
    - Keyword matching (finds exact terms)
    
    Args:
        q: Search query text
        limit: Maximum results
        semantic_weight: Weight for semantic vs text (0.7 = 70% semantic, 30% text)
        investigation_id: Filter by investigation
        
    Returns:
        Results ranked by combined score
    """
    try:
        results = await storage.search_hybrid(
            query=q,
            limit=limit,
            semantic_weight=semantic_weight,
            investigation_id=investigation_id,
        )
        
        return [
            HybridSearchResult(
                chunk_id=str(r['chunk_id']),
                document_id=str(r['document_id']),
                filename=r['filename'],
                content=r['content'],
                source=r['source'],
                semantic_score=r['semantic_score'],
                text_score=r['text_score'],
                combined_score=r['combined_score'],
            )
            for r in results
        ]
        
    except Exception as e:
        logger.error(f"Hybrid search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    storage = Depends(get_document_storage),
):
    """Get document metadata by ID."""
    doc = await storage.get_document(document_id)
    
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    return DocumentResponse(
        id=str(doc['id']),
        filename=doc['filename'],
        file_type=doc['file_type'],
        file_size=doc['file_size'],
        title=doc['title'],
        author=doc['author'],
        page_count=doc['page_count'],
        word_count=doc['word_count'],
        slide_count=doc['slide_count'],
        sheet_count=doc['sheet_count'],
        investigation_id=str(doc['investigation_id']) if doc['investigation_id'] else None,
        created_at=doc['created_at'].isoformat(),
    )


@router.get("/{document_id}/chunks", response_model=list[DocumentChunkResponse])
async def get_document_chunks(
    document_id: str,
    storage = Depends(get_document_storage),
):
    """Get all text chunks for a document."""
    chunks = await storage.get_document_chunks(document_id)
    
    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or has no chunks",
        )
    
    return [
        DocumentChunkResponse(
            id=str(c['id']),
            chunk_index=c['chunk_index'],
            content=c['content'],
            source=c['source'],
            heading=c['heading'],
            page_number=c['page_number'],
            char_count=c['char_count'],
        )
        for c in chunks
    ]


@router.get("/{document_id}/context")
async def get_document_for_context(
    document_id: str,
    storage = Depends(get_document_storage),
):
    """
    Get document content formatted for LLM context.
    
    Returns all chunks concatenated with source information,
    suitable for providing as context to the chat endpoint.
    """
    context = await storage.get_document_context(document_id)
    
    if not context:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    # Format for LLM context
    doc_info = context[0]
    formatted_chunks = []
    
    for chunk in context:
        header = f"[{chunk['source']}"
        if chunk['heading']:
            header += f" - {chunk['heading']}"
        header += "]"
        formatted_chunks.append(f"{header}\n{chunk['content']}")
    
    return {
        "document_id": str(doc_info['document_id']),
        "filename": doc_info['filename'],
        "file_type": doc_info['file_type'],
        "title": doc_info['title'],
        "context_text": "\n\n".join(formatted_chunks),
        "chunk_count": len(context),
    }


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    storage = Depends(get_document_storage),
):
    """Delete a document and all its chunks."""
    deleted = await storage.delete_document(document_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    return {"success": True, "message": "Document deleted"}


@router.get("/", response_model=list[DocumentResponse])
async def list_documents(
    investigation_id: Optional[str] = Query(default=None),
    file_type: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    storage = Depends(get_document_storage),
):
    """List documents with optional filters."""
    docs = await storage.list_documents(
        investigation_id=investigation_id,
        file_type=file_type,
        limit=limit,
        offset=offset,
    )
    
    return [
        DocumentResponse(
            id=str(d['id']),
            filename=d['filename'],
            file_type=d['file_type'],
            file_size=d['file_size'],
            title=d['title'],
            page_count=d['page_count'],
            word_count=d['word_count'],
            created_at=d['created_at'].isoformat(),
        )
        for d in docs
    ]
