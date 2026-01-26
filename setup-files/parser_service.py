# api/services/documents/parser_service.py
"""
Document Parser Service - Main entry point for document parsing.
"""

import logging
import tempfile
from pathlib import Path
from typing import BinaryIO, Optional, Union
import time

from .base import BaseParser, DocumentContent, FileType, ParserResult
from .registry import get_registry, ParserRegistry

logger = logging.getLogger(__name__)


class DocumentParserService:
    """
    High-level service for parsing documents.
    
    Handles file type detection, parser selection, and provides
    a unified interface for parsing various document types.
    
    Usage:
        service = DocumentParserService()
        
        # Parse from file path
        result = await service.parse_file("/path/to/document.docx")
        
        # Parse from uploaded file
        result = await service.parse_upload(file_data, "document.docx")
        
        # Check supported types
        if service.is_supported("report.pdf"):
            result = await service.parse_file("report.pdf")
    """
    
    def __init__(
        self,
        registry: Optional[ParserRegistry] = None,
        default_chunk_size: int = 1000,
        default_chunk_overlap: int = 200,
    ):
        """
        Initialize the document parser service.
        
        Args:
            registry: Custom parser registry (uses global if not provided)
            default_chunk_size: Default max characters per chunk
            default_chunk_overlap: Default overlap between chunks
        """
        self.registry = registry or get_registry()
        self.default_chunk_size = default_chunk_size
        self.default_chunk_overlap = default_chunk_overlap
    
    async def parse_file(
        self,
        file_path: Union[str, Path],
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> ParserResult:
        """
        Parse a document from a file path.
        
        Args:
            file_path: Path to the document file
            chunk_size: Max characters per chunk (uses default if not provided)
            chunk_overlap: Overlap between chunks (uses default if not provided)
            
        Returns:
            ParserResult with extracted content and metadata
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return ParserResult(
                success=False,
                error=f"File not found: {file_path}",
            )
        
        parser = self.registry.get_parser_for_file(file_path.name)
        if parser is None:
            file_type = BaseParser.detect_file_type(file_path.name)
            return ParserResult(
                success=False,
                error=f"Unsupported file type: {file_type.value}",
            )
        
        chunk_size = chunk_size or self.default_chunk_size
        chunk_overlap = chunk_overlap or self.default_chunk_overlap
        
        return await parser.parse(file_path, chunk_size, chunk_overlap)
    
    async def parse_upload(
        self,
        file_data: BinaryIO,
        filename: str,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> ParserResult:
        """
        Parse a document from uploaded file data.
        
        Args:
            file_data: File-like object with document bytes
            filename: Original filename (for type detection)
            chunk_size: Max characters per chunk
            chunk_overlap: Overlap between chunks
            
        Returns:
            ParserResult with extracted content and metadata
        """
        parser = self.registry.get_parser_for_file(filename)
        if parser is None:
            file_type = BaseParser.detect_file_type(filename)
            return ParserResult(
                success=False,
                error=f"Unsupported file type: {file_type.value}",
            )
        
        chunk_size = chunk_size or self.default_chunk_size
        chunk_overlap = chunk_overlap or self.default_chunk_overlap
        
        return await parser.parse_bytes(file_data, filename, chunk_size, chunk_overlap)
    
    async def parse_bytes(
        self,
        data: bytes,
        filename: str,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> ParserResult:
        """
        Parse a document from raw bytes.
        
        Args:
            data: Raw document bytes
            filename: Original filename (for type detection)
            chunk_size: Max characters per chunk
            chunk_overlap: Overlap between chunks
            
        Returns:
            ParserResult with extracted content and metadata
        """
        from io import BytesIO
        return await self.parse_upload(
            BytesIO(data),
            filename,
            chunk_size,
            chunk_overlap,
        )
    
    def is_supported(self, filename: str) -> bool:
        """Check if a file type is supported for parsing."""
        return self.registry.is_file_supported(filename)
    
    def get_supported_extensions(self) -> list[str]:
        """Get list of supported file extensions."""
        return self.registry.supported_extensions()
    
    def get_file_type(self, filename: str) -> FileType:
        """Detect file type from filename."""
        return BaseParser.detect_file_type(filename)


async def parse_document(
    file_path: Union[str, Path],
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> ParserResult:
    """
    Convenience function to parse a document file.
    
    Args:
        file_path: Path to the document
        chunk_size: Max characters per chunk
        chunk_overlap: Overlap between chunks
        
    Returns:
        ParserResult with extracted content
    """
    service = DocumentParserService()
    return await service.parse_file(file_path, chunk_size, chunk_overlap)


async def parse_upload(
    file_data: BinaryIO,
    filename: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> ParserResult:
    """
    Convenience function to parse an uploaded document.
    
    Args:
        file_data: File-like object with document bytes
        filename: Original filename
        chunk_size: Max characters per chunk
        chunk_overlap: Overlap between chunks
        
    Returns:
        ParserResult with extracted content
    """
    service = DocumentParserService()
    return await service.parse_upload(file_data, filename, chunk_size, chunk_overlap)
