# api/routers/documents.py
"""
FastAPI router for document upload and parsing endpoints.
"""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from typing import Optional
import logging

# Import from your document parser service
# Adjust import path based on your project structure
from api.services.documents import DocumentParserService, ParserResult, FileType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

# Initialize parser service
parser_service = DocumentParserService()


# Response Models
class DocumentMetadataResponse(BaseModel):
    filename: str
    file_type: str
    file_size: int
    file_hash: str
    title: Optional[str] = None
    author: Optional[str] = None
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    slide_count: Optional[int] = None
    sheet_count: Optional[int] = None


class TextChunkResponse(BaseModel):
    content: str
    source: str
    chunk_index: int
    heading: Optional[str] = None
    page_number: Optional[int] = None


class DocumentContentResponse(BaseModel):
    full_text: str
    chunks: list[TextChunkResponse]
    tables: list[dict]
    links: list[str]


class ParseResponse(BaseModel):
    success: bool
    metadata: Optional[DocumentMetadataResponse] = None
    content: Optional[DocumentContentResponse] = None
    error: Optional[str] = None
    warnings: list[str] = []
    processing_time_ms: float = 0.0


class SupportedTypesResponse(BaseModel):
    extensions: list[str]
    count: int


# Endpoints
@router.get("/supported-types", response_model=SupportedTypesResponse)
async def get_supported_types():
    """Get list of supported file types for parsing."""
    extensions = parser_service.get_supported_extensions()
    return SupportedTypesResponse(
        extensions=extensions,
        count=len(extensions),
    )


@router.post("/parse", response_model=ParseResponse)
async def parse_document(
    file: UploadFile = File(...),
    chunk_size: int = Form(default=1000, ge=100, le=10000),
    chunk_overlap: int = Form(default=200, ge=0, le=1000),
):
    """
    Parse an uploaded document and extract text content.
    
    Supports: .docx, .doc, .pptx, .ppt, .xlsx, .xls, .csv, .pdf, 
              .txt, .md, .html, .json, .xml, .rtf
    
    Args:
        file: The document file to parse
        chunk_size: Maximum characters per text chunk (for embeddings)
        chunk_overlap: Overlap between chunks for context continuity
        
    Returns:
        Parsed content with metadata and text chunks
    """
    filename = file.filename or "unknown"
    
    # Check if file type is supported
    if not parser_service.is_supported(filename):
        file_type = parser_service.get_file_type(filename)
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file_type.value}. "
                   f"Supported types: {', '.join(parser_service.get_supported_extensions())}",
        )
    
    try:
        # Parse the document
        result = await parser_service.parse_upload(
            file.file,
            filename,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        
        return _convert_result_to_response(result)
        
    except Exception as e:
        logger.error(f"Error parsing document {filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error parsing document: {str(e)}",
        )


@router.post("/parse-and-store")
async def parse_and_store_document(
    file: UploadFile = File(...),
    investigation_id: Optional[str] = Form(default=None),
    chunk_size: int = Form(default=1000),
    chunk_overlap: int = Form(default=200),
    generate_embeddings: bool = Form(default=True),
):
    """
    Parse document, store in database, and optionally generate embeddings.
    
    This endpoint:
    1. Parses the document to extract text
    2. Stores the file in S3
    3. Saves metadata to PostgreSQL
    4. Optionally generates vector embeddings for semantic search
    
    Args:
        file: The document file
        investigation_id: Optional investigation to associate with
        chunk_size: Characters per chunk
        chunk_overlap: Overlap between chunks
        generate_embeddings: Whether to generate vector embeddings
        
    Returns:
        Document ID and processing status
    """
    filename = file.filename or "unknown"
    
    if not parser_service.is_supported(filename):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type",
        )
    
    # Read file data
    file_data = await file.read()
    
    # Parse document
    from io import BytesIO
    result = await parser_service.parse_upload(
        BytesIO(file_data),
        filename,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to parse document: {result.error}",
        )
    
    # TODO: Implement storage integration
    # 1. Upload to S3
    # from api.services.storage import S3Service
    # s3 = S3Service()
    # s3_key = await s3.upload_file(BytesIO(file_data), filename)
    
    # 2. Store metadata in PostgreSQL
    # document_id = await store_document_metadata(result.metadata, s3_key, investigation_id)
    
    # 3. Generate embeddings for chunks
    # if generate_embeddings:
    #     from api.services.embeddings import EmbeddingService
    #     embedding_service = EmbeddingService()
    #     for chunk in result.content.chunks:
    #         embedding = await embedding_service.embed(chunk.content)
    #         await store_chunk_embedding(document_id, chunk, embedding)
    
    return {
        "success": True,
        "message": "Document parsed successfully",
        "metadata": _convert_metadata(result.metadata) if result.metadata else None,
        "chunk_count": len(result.content.chunks) if result.content else 0,
        # "document_id": document_id,  # Uncomment when storage is implemented
    }


def _convert_result_to_response(result: ParserResult) -> ParseResponse:
    """Convert ParserResult to API response."""
    return ParseResponse(
        success=result.success,
        metadata=_convert_metadata(result.metadata) if result.metadata else None,
        content=_convert_content(result.content) if result.content else None,
        error=result.error,
        warnings=result.warnings,
        processing_time_ms=result.processing_time_ms,
    )


def _convert_metadata(metadata) -> DocumentMetadataResponse:
    """Convert DocumentMetadata to response model."""
    return DocumentMetadataResponse(
        filename=metadata.filename,
        file_type=metadata.file_type.value,
        file_size=metadata.file_size,
        file_hash=metadata.file_hash,
        title=metadata.title,
        author=metadata.author,
        page_count=metadata.page_count,
        word_count=metadata.word_count,
        slide_count=metadata.slide_count,
        sheet_count=metadata.sheet_count,
    )


def _convert_content(content) -> DocumentContentResponse:
    """Convert DocumentContent to response model."""
    return DocumentContentResponse(
        full_text=content.full_text,
        chunks=[
            TextChunkResponse(
                content=chunk.content,
                source=chunk.source,
                chunk_index=chunk.chunk_index,
                heading=chunk.heading,
                page_number=chunk.page_number,
            )
            for chunk in content.chunks
        ],
        tables=content.tables,
        links=content.links,
    )
