# api/services/documents/parsers/text_parser.py
"""
Parser for text-based files (.txt, .md, .html, .json, .xml, .rtf).
"""

import html
import json
import logging
import re
import subprocess
import tempfile
from pathlib import Path
from typing import BinaryIO, Optional, Union
from xml.etree import ElementTree
import time

from ..base import (
    BaseParser, DocumentContent, DocumentMetadata,
    FileType, ParserResult, TextChunk
)

logger = logging.getLogger(__name__)


class TextParser(BaseParser):
    """Parser for text-based files."""
    
    supported_types = [
        FileType.TXT, FileType.MD, FileType.HTML,
        FileType.JSON, FileType.XML, FileType.RTF
    ]
    
    async def parse(
        self,
        file_path: Union[str, Path],
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> ParserResult:
        """Parse a text file from file path."""
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
            logger.error(f"Error parsing text file {file_path}: {e}")
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
        """Parse a text file from bytes."""
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
            logger.error(f"Error parsing text file bytes: {e}")
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
        """Parse text content based on file type."""
        file_type = self.detect_file_type(filename)
        file_hash = self.compute_file_hash(file_data)
        
        # Decode text
        text = self._decode_text(file_data)
        if text is None:
            return ParserResult(
                success=False,
                error="Could not decode file (tried utf-8, latin-1, cp1252)",
            )
        
        # Extract based on file type
        if file_type == FileType.HTML:
            full_text, links = self._extract_html(text)
        elif file_type == FileType.JSON:
            full_text = self._extract_json(text)
            links = []
        elif file_type == FileType.XML:
            full_text = self._extract_xml(text)
            links = []
        elif file_type == FileType.RTF:
            full_text = await self._extract_rtf(file_data)
            links = []
        elif file_type == FileType.MD:
            full_text, links = self._extract_markdown(text)
        else:  # Plain text
            full_text = text.strip()
            links = []
        
        # Create chunks
        chunks = self.chunk_text(full_text, "text", chunk_size, chunk_overlap)
        
        # Build metadata
        metadata = DocumentMetadata(
            filename=filename,
            file_type=file_type,
            file_size=len(file_data),
            file_hash=file_hash,
            word_count=len(full_text.split()),
        )
        
        content = DocumentContent(
            full_text=full_text,
            chunks=chunks,
            links=links,
        )
        
        return ParserResult(
            success=True,
            metadata=metadata,
            content=content,
        )
    
    def _decode_text(self, data: bytes) -> Optional[str]:
        """Try to decode bytes with multiple encodings."""
        for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
            try:
                return data.decode(encoding)
            except UnicodeDecodeError:
                continue
        return None
    
    def _extract_html(self, html_content: str) -> tuple[str, list[str]]:
        """Extract text and links from HTML."""
        from html.parser import HTMLParser
        
        class TextExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.text_parts = []
                self.links = []
                self.skip_tags = {"script", "style", "noscript", "head"}
                self.current_skip = False
            
            def handle_starttag(self, tag, attrs):
                if tag in self.skip_tags:
                    self.current_skip = True
                if tag == "a":
                    for name, value in attrs:
                        if name == "href" and value:
                            self.links.append(value)
                # Add newlines for block elements
                if tag in {"p", "div", "br", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr"}:
                    self.text_parts.append("\n")
            
            def handle_endtag(self, tag):
                if tag in self.skip_tags:
                    self.current_skip = False
            
            def handle_data(self, data):
                if not self.current_skip:
                    text = data.strip()
                    if text:
                        self.text_parts.append(text)
        
        try:
            extractor = TextExtractor()
            extractor.feed(html_content)
            text = " ".join(extractor.text_parts)
            # Clean up multiple spaces/newlines
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'\n\s*\n', '\n\n', text)
            return text.strip(), extractor.links
        except Exception as e:
            logger.warning(f"HTML parsing error: {e}")
            # Fallback: strip all tags
            text = re.sub(r'<[^>]+>', ' ', html_content)
            text = html.unescape(text)
            return text.strip(), []
    
    def _extract_json(self, json_content: str) -> str:
        """Extract text from JSON, flattening nested structures."""
        try:
            data = json.loads(json_content)
            text_parts = self._flatten_json(data)
            return "\n".join(text_parts)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parsing error: {e}")
            return json_content
    
    def _flatten_json(self, obj, prefix: str = "") -> list[str]:
        """Recursively flatten JSON to key-value pairs."""
        parts = []
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_prefix = f"{prefix}.{key}" if prefix else key
                if isinstance(value, (dict, list)):
                    parts.extend(self._flatten_json(value, new_prefix))
                else:
                    parts.append(f"{new_prefix}: {value}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                new_prefix = f"{prefix}[{i}]"
                if isinstance(item, (dict, list)):
                    parts.extend(self._flatten_json(item, new_prefix))
                else:
                    parts.append(f"{new_prefix}: {item}")
        else:
            parts.append(f"{prefix}: {obj}" if prefix else str(obj))
        
        return parts
    
    def _extract_xml(self, xml_content: str) -> str:
        """Extract text from XML elements."""
        try:
            # Remove XML declaration if present
            xml_content = re.sub(r'<\?xml[^?]*\?>', '', xml_content)
            root = ElementTree.fromstring(f"<root>{xml_content}</root>")
            
            text_parts = []
            for elem in root.iter():
                if elem.text and elem.text.strip():
                    tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                    text_parts.append(f"{tag_name}: {elem.text.strip()}")
                if elem.tail and elem.tail.strip():
                    text_parts.append(elem.tail.strip())
            
            return "\n".join(text_parts)
        except ElementTree.ParseError as e:
            logger.warning(f"XML parsing error: {e}")
            # Fallback: strip tags
            text = re.sub(r'<[^>]+>', ' ', xml_content)
            return text.strip()
    
    def _extract_markdown(self, md_content: str) -> tuple[str, list[str]]:
        """Extract text and links from Markdown."""
        # Extract links
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        links = [match[1] for match in re.findall(link_pattern, md_content)]
        
        # Remove markdown syntax for cleaner text
        text = md_content
        
        # Remove code blocks
        text = re.sub(r'```[\s\S]*?```', '', text)
        text = re.sub(r'`[^`]+`', '', text)
        
        # Convert headers to plain text
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        
        # Remove link syntax but keep text
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        
        # Remove bold/italic
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)
        text = re.sub(r'_([^_]+)_', r'\1', text)
        
        # Remove horizontal rules
        text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
        
        return text.strip(), links
    
    async def _extract_rtf(self, file_data: bytes) -> str:
        """Extract text from RTF using pandoc or unrtf."""
        with tempfile.NamedTemporaryFile(suffix=".rtf", delete=False) as tmp:
            tmp.write(file_data)
            tmp_path = Path(tmp.name)
        
        try:
            # Try pandoc first
            try:
                result = subprocess.run(
                    ["pandoc", "-t", "plain", str(tmp_path)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0 and result.stdout:
                    return result.stdout.strip()
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
            
            # Fallback to unrtf
            try:
                result = subprocess.run(
                    ["unrtf", "--text", str(tmp_path)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0 and result.stdout:
                    # Clean unrtf output
                    text = result.stdout
                    # Remove header comments
                    text = re.sub(r'^-{10,}.*?-{10,}', '', text, flags=re.DOTALL)
                    return text.strip()
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
            
            # Last resort: strip RTF codes manually
            text = file_data.decode("latin-1", errors="ignore")
            text = re.sub(r'\\[a-z]+\d*\s?', '', text)
            text = re.sub(r'[{}]', '', text)
            return text.strip()
            
        finally:
            tmp_path.unlink(missing_ok=True)
