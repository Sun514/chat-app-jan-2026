# api/services/documents/base.py
"""
Base classes and data models for document parsing.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, BinaryIO, Union
import hashlib


class FileType(str, Enum):
    """Supported file types for parsing."""
    # Microsoft Office
    DOCX = "docx"
    DOC = "doc"
    PPTX = "pptx"
    PPT = "ppt"
    XLSX = "xlsx"
    XLS = "xls"
    
    # Text formats
    TXT = "txt"
    MD = "md"
    CSV = "csv"
    JSON = "json"
    XML = "xml"
    HTML = "html"
    
    # PDF
    PDF = "pdf"
    
    # Email
    EML = "eml"
    MSG = "msg"
    PST = "pst"
    
    # Images (for OCR)
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    TIFF = "tiff"
    
    # Other
    RTF = "rtf"
    ODT = "odt"
    ODS = "ods"
    ODP = "odp"
    
    UNKNOWN = "unknown"


@dataclass
class DocumentMetadata:
    """Metadata extracted from a document."""
    filename: str
    file_type: FileType
    file_size: int
    file_hash: str  # SHA-256
    
    # Common metadata
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    
    # Office-specific
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    slide_count: Optional[int] = None
    sheet_count: Optional[int] = None
    
    # Custom metadata
    custom: dict = field(default_factory=dict)


@dataclass
class TextChunk:
    """A chunk of text from a document with source information."""
    content: str
    source: str  # e.g., "page_1", "slide_3", "sheet_Sales", "paragraph_5"
    chunk_index: int
    
    # Optional metadata for the chunk
    heading: Optional[str] = None  # Parent heading/section
    page_number: Optional[int] = None
    
    def __len__(self) -> int:
        return len(self.content)


@dataclass
class DocumentContent:
    """Extracted content from a document."""
    # Full text (concatenated)
    full_text: str
    
    # Chunked text for embeddings
    chunks: list[TextChunk] = field(default_factory=list)
    
    # Tables extracted (as list of dicts or markdown)
    tables: list[dict] = field(default_factory=list)
    
    # Images extracted (paths to temp files or base64)
    images: list[dict] = field(default_factory=list)
    
    # Links/URLs found
    links: list[str] = field(default_factory=list)


@dataclass
class ParserResult:
    """Complete result from parsing a document."""
    success: bool
    metadata: Optional[DocumentMetadata] = None
    content: Optional[DocumentContent] = None
    error: Optional[str] = None
    warnings: list[str] = field(default_factory=list)
    processing_time_ms: float = 0.0
    
    @property
    def text(self) -> str:
        """Convenience property for full text."""
        return self.content.full_text if self.content else ""


class BaseParser(ABC):
    """Abstract base class for document parsers."""
    
    # File types this parser handles
    supported_types: list[FileType] = []
    
    # Chunk settings
    default_chunk_size: int = 1000
    default_chunk_overlap: int = 200
    
    @abstractmethod
    async def parse(
        self,
        file_path: Union[str, Path],
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> ParserResult:
        """
        Parse a document and extract content.
        
        Args:
            file_path: Path to the file
            chunk_size: Max characters per chunk (for embeddings)
            chunk_overlap: Overlap between chunks
            
        Returns:
            ParserResult with metadata and content
        """
        pass
    
    @abstractmethod
    async def parse_bytes(
        self,
        file_data: BinaryIO,
        filename: str,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> ParserResult:
        """
        Parse a document from bytes.
        
        Args:
            file_data: File-like object with document bytes
            filename: Original filename (for type detection)
            chunk_size: Max characters per chunk
            chunk_overlap: Overlap between chunks
            
        Returns:
            ParserResult with metadata and content
        """
        pass
    
    def can_parse(self, file_type: FileType) -> bool:
        """Check if this parser can handle the given file type."""
        return file_type in self.supported_types
    
    @staticmethod
    def compute_file_hash(data: bytes) -> str:
        """Compute SHA-256 hash of file content."""
        return hashlib.sha256(data).hexdigest()
    
    @staticmethod
    def detect_file_type(filename: str) -> FileType:
        """Detect file type from filename extension."""
        ext = Path(filename).suffix.lower().lstrip(".")
        try:
            return FileType(ext)
        except ValueError:
            return FileType.UNKNOWN
    
    def chunk_text(
        self,
        text: str,
        source_prefix: str = "chunk",
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> list[TextChunk]:
        """
        Split text into chunks for embedding.
        
        Uses sentence-aware splitting when possible.
        """
        chunk_size = chunk_size or self.default_chunk_size
        chunk_overlap = chunk_overlap or self.default_chunk_overlap
        
        if not text or not text.strip():
            return []
        
        # Simple sentence-aware chunking
        chunks = []
        sentences = self._split_sentences(text)
        
        current_chunk = ""
        chunk_idx = 0
        
        for sentence in sentences:
            # If adding this sentence exceeds chunk size, save current and start new
            if current_chunk and len(current_chunk) + len(sentence) > chunk_size:
                chunks.append(TextChunk(
                    content=current_chunk.strip(),
                    source=f"{source_prefix}_{chunk_idx}",
                    chunk_index=chunk_idx,
                ))
                chunk_idx += 1
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap(current_chunk, chunk_overlap)
                current_chunk = overlap_text + sentence
            else:
                current_chunk += sentence
        
        # Don't forget the last chunk
        if current_chunk.strip():
            chunks.append(TextChunk(
                content=current_chunk.strip(),
                source=f"{source_prefix}_{chunk_idx}",
                chunk_index=chunk_idx,
            ))
        
        return chunks
    
    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences (simple implementation)."""
        import re
        # Split on sentence boundaries, keeping the delimiter
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s + " " for s in sentences if s.strip()]
    
    def _get_overlap(self, text: str, overlap_size: int) -> str:
        """Get the last N characters for overlap."""
        if len(text) <= overlap_size:
            return text
        # Try to break at word boundary
        overlap = text[-overlap_size:]
        space_idx = overlap.find(" ")
        if space_idx > 0:
            return overlap[space_idx + 1:]
        return overlap
