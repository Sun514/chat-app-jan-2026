# api/services/documents/parsers/pdf_parser.py
"""
Parser for PDF documents.
Uses pdfplumber for text extraction, with pymupdf as fallback.
"""

import logging
import tempfile
from pathlib import Path
from typing import BinaryIO, Optional, Union
import time

from ..base import (
    BaseParser, DocumentContent, DocumentMetadata,
    FileType, ParserResult, TextChunk
)

logger = logging.getLogger(__name__)


class PdfParser(BaseParser):
    """Parser for PDF documents."""
    
    supported_types = [FileType.PDF]
    
    async def parse(
        self,
        file_path: Union[str, Path],
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> ParserResult:
        """Parse a PDF from file path."""
        start_time = time.time()
        file_path = Path(file_path)
        
        try:
            with open(file_path, "rb") as f:
                file_data = f.read()
            
            result = await self._parse_content(
                file_data,
                file_path.name,
                chunk_size,
                chunk_overlap,
            )
            result.processing_time_ms = (time.time() - start_time) * 1000
            return result
            
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {e}")
            return ParserResult(
                success=False,
                error=str(e),
                processing_time_ms=(time.time() - start_time) * 1000,
            )
    
    async def parse_bytes(
        self,
        file_data: BinaryIO,
        filename: str,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> ParserResult:
        """Parse a PDF from bytes."""
        start_time = time.time()
        
        try:
            data = file_data.read()
            result = await self._parse_content(
                data,
                filename,
                chunk_size,
                chunk_overlap,
            )
            result.processing_time_ms = (time.time() - start_time) * 1000
            return result
            
        except Exception as e:
            logger.error(f"Error parsing PDF bytes: {e}")
            return ParserResult(
                success=False,
                error=str(e),
                processing_time_ms=(time.time() - start_time) * 1000,
            )
    
    async def _parse_content(
        self,
        file_data: bytes,
        filename: str,
        chunk_size: Optional[int],
        chunk_overlap: Optional[int],
    ) -> ParserResult:
        """Parse PDF content."""
        file_type = FileType.PDF
        file_hash = self.compute_file_hash(file_data)
        warnings = []
        
        # Write to temp file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(file_data)
            tmp_path = Path(tmp.name)
        
        try:
            # Try pdfplumber first (best for tables)
            pages_text, chunks, tables = await self._extract_with_pdfplumber(
                tmp_path, chunk_size, chunk_overlap
            )
            
            if not pages_text:
                # Fallback to pymupdf
                pages_text, chunks, tables = await self._extract_with_pymupdf(
                    tmp_path, chunk_size, chunk_overlap
                )
                if not pages_text:
                    warnings.append("Could not extract text from PDF")
            
            # Extract metadata
            metadata = await self._extract_metadata(
                tmp_path, file_data, filename, file_hash
            )
            
            # Extract links
            links = await self._extract_links(tmp_path)
            
            content = DocumentContent(
                full_text=pages_text,
                chunks=chunks,
                tables=tables,
                links=links,
            )
            
            return ParserResult(
                success=True,
                metadata=metadata,
                content=content,
                warnings=warnings,
            )
            
        finally:
            tmp_path.unlink(missing_ok=True)
    
    async def _extract_with_pdfplumber(
        self,
        file_path: Path,
        chunk_size: Optional[int],
        chunk_overlap: Optional[int],
    ) -> tuple[str, list[TextChunk], list[dict]]:
        """Extract content using pdfplumber."""
        try:
            import pdfplumber
        except ImportError:
            logger.warning("pdfplumber not installed")
            return "", [], []
        
        try:
            all_text = []
            chunks = []
            tables = []
            
            with pdfplumber.open(str(file_path)) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    # Extract text
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        all_text.append(f"[Page {page_num}]\n{page_text}")
                        
                        chunks.append(TextChunk(
                            content=page_text,
                            source=f"page_{page_num}",
                            chunk_index=page_num - 1,
                            page_number=page_num,
                        ))
                    
                    # Extract tables
                    page_tables = page.extract_tables()
                    for i, table in enumerate(page_tables):
                        if table:
                            tables.append({
                                "page": page_num,
                                "index": i,
                                "rows": table,
                            })
            
            full_text = "\n\n".join(all_text)
            
            # Re-chunk if needed
            if chunk_size:
                chunks = self.chunk_text(full_text, "chunk", chunk_size, chunk_overlap)
            
            return full_text, chunks, tables
            
        except Exception as e:
            logger.error(f"pdfplumber error: {e}")
            return "", [], []
    
    async def _extract_with_pymupdf(
        self,
        file_path: Path,
        chunk_size: Optional[int],
        chunk_overlap: Optional[int],
    ) -> tuple[str, list[TextChunk], list[dict]]:
        """Extract content using pymupdf (fitz)."""
        try:
            import fitz  # pymupdf
        except ImportError:
            logger.warning("pymupdf not installed")
            return "", [], []
        
        try:
            all_text = []
            chunks = []
            
            doc = fitz.open(str(file_path))
            
            for page_num, page in enumerate(doc, 1):
                page_text = page.get_text()
                if page_text.strip():
                    all_text.append(f"[Page {page_num}]\n{page_text}")
                    
                    chunks.append(TextChunk(
                        content=page_text,
                        source=f"page_{page_num}",
                        chunk_index=page_num - 1,
                        page_number=page_num,
                    ))
            
            doc.close()
            
            full_text = "\n\n".join(all_text)
            
            if chunk_size:
                chunks = self.chunk_text(full_text, "chunk", chunk_size, chunk_overlap)
            
            return full_text, chunks, []  # pymupdf doesn't extract tables well
            
        except Exception as e:
            logger.error(f"pymupdf error: {e}")
            return "", [], []
    
    async def _extract_metadata(
        self,
        file_path: Path,
        file_data: bytes,
        filename: str,
        file_hash: str,
    ) -> DocumentMetadata:
        """Extract PDF metadata."""
        metadata = DocumentMetadata(
            filename=filename,
            file_type=FileType.PDF,
            file_size=len(file_data),
            file_hash=file_hash,
        )
        
        # Try pdfplumber
        try:
            import pdfplumber
            with pdfplumber.open(str(file_path)) as pdf:
                metadata.page_count = len(pdf.pages)
                
                info = pdf.metadata
                if info:
                    metadata.title = info.get("Title")
                    metadata.author = info.get("Author")
                    metadata.subject = info.get("Subject")
                    # Parse dates if present
                    if "CreationDate" in info:
                        metadata.created_at = self._parse_pdf_date(info["CreationDate"])
                    if "ModDate" in info:
                        metadata.modified_at = self._parse_pdf_date(info["ModDate"])
            return metadata
        except Exception:
            pass
        
        # Try pymupdf as fallback
        try:
            import fitz
            doc = fitz.open(str(file_path))
            metadata.page_count = doc.page_count
            
            info = doc.metadata
            if info:
                metadata.title = info.get("title")
                metadata.author = info.get("author")
                metadata.subject = info.get("subject")
            
            doc.close()
        except Exception as e:
            logger.warning(f"Could not extract PDF metadata: {e}")
        
        return metadata
    
    async def _extract_links(self, file_path: Path) -> list[str]:
        """Extract links/URLs from PDF."""
        links = []
        
        try:
            import fitz
            doc = fitz.open(str(file_path))
            
            for page in doc:
                for link in page.get_links():
                    if link.get("uri"):
                        links.append(link["uri"])
            
            doc.close()
        except Exception:
            pass
        
        return list(set(links))  # Dedupe
    
    def _parse_pdf_date(self, date_str: str):
        """Parse PDF date string (D:YYYYMMDDHHmmSS format)."""
        if not date_str:
            return None
        
        try:
            from datetime import datetime
            # Remove 'D:' prefix and timezone
            date_str = date_str.replace("D:", "")[:14]
            return datetime.strptime(date_str, "%Y%m%d%H%M%S")
        except Exception:
            return None
