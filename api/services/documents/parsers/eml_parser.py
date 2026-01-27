# api/services/documents/parsers/eml_parser.py
"""
Parser for EML email files (.eml).
"""

import email
import logging
import re
from datetime import datetime
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr, parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import BinaryIO, Optional, Union
import time

from ..base import (
    BaseParser, DocumentContent, DocumentMetadata,
    FileType, ParserResult, TextChunk
)

logger = logging.getLogger(__name__)


class HTMLTextExtractor(HTMLParser):
    """Extract text from HTML content."""
    
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.skip_tags = {"script", "style", "head", "noscript"}
        self.current_skip = False
    
    def handle_starttag(self, tag, attrs):
        if tag in self.skip_tags:
            self.current_skip = True
        if tag in {"p", "div", "br", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr", "td"}:
            self.text_parts.append("\n")
    
    def handle_endtag(self, tag):
        if tag in self.skip_tags:
            self.current_skip = False
    
    def handle_data(self, data):
        if not self.current_skip:
            text = data.strip()
            if text:
                self.text_parts.append(text + " ")
    
    def get_text(self) -> str:
        text = "".join(self.text_parts)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text.strip()


class EmlParser(BaseParser):
    """Parser for EML email files."""
    
    supported_types = [FileType.EML]
    
    async def parse(
        self,
        file_path: Union[str, Path],
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> ParserResult:
        """Parse an EML file from file path."""
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
            logger.error(f"Error parsing EML file {file_path}: {e}")
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
        """Parse an EML file from bytes."""
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
            logger.error(f"Error parsing EML bytes: {e}")
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
        """Parse EML content."""
        file_type = FileType.EML
        file_hash = self.compute_file_hash(file_data)
        warnings = []
        
        try:
            # Parse email using Python's email library
            msg = BytesParser(policy=policy.default).parsebytes(file_data)
            
            # Extract headers
            headers = self._extract_headers(msg)
            
            # Extract body
            body_text, body_html = self._extract_body(msg)
            
            # Convert HTML to text if no plain text body
            if not body_text and body_html:
                body_text = self._html_to_text(body_html)
            
            # Extract attachments info
            attachments = self._extract_attachments(msg)
            
            # Build full text representation
            full_text = self._build_full_text(headers, body_text, attachments)
            
            # Create chunks
            chunks = self._create_email_chunks(
                headers, body_text, attachments, chunk_size, chunk_overlap
            )
            
            # Build metadata
            metadata = DocumentMetadata(
                filename=filename,
                file_type=file_type,
                file_size=len(file_data),
                file_hash=file_hash,
                title=headers.get("subject"),
                author=headers.get("from"),
                word_count=len(full_text.split()) if full_text else 0,
                custom={
                    "message_id": headers.get("message_id"),
                    "to": headers.get("to"),
                    "cc": headers.get("cc"),
                    "date": headers.get("date").isoformat() if headers.get("date") else None,
                    "attachment_count": len(attachments),
                    "has_html": bool(body_html),
                },
            )
            
            # Extract links from body
            links = self._extract_links(body_text, body_html)
            
            content = DocumentContent(
                full_text=full_text,
                chunks=chunks,
                links=links,
            )
            
            return ParserResult(
                success=True,
                metadata=metadata,
                content=content,
                warnings=warnings,
            )
            
        except Exception as e:
            logger.error(f"Error parsing EML: {e}")
            return ParserResult(
                success=False,
                error=f"Failed to parse EML: {str(e)}",
            )
    
    def _extract_headers(self, msg: email.message.EmailMessage) -> dict:
        """Extract email headers."""
        headers = {}
        
        # Subject
        headers["subject"] = msg.get("Subject", "")
        
        # From
        from_header = msg.get("From", "")
        if from_header:
            name, addr = parseaddr(from_header)
            headers["from"] = f"{name} <{addr}>" if name else addr
            headers["from_name"] = name
            headers["from_email"] = addr
        
        # To
        to_header = msg.get("To", "")
        if to_header:
            headers["to"] = to_header
            headers["to_list"] = self._parse_address_list(to_header)
        
        # CC
        cc_header = msg.get("Cc", "")
        if cc_header:
            headers["cc"] = cc_header
            headers["cc_list"] = self._parse_address_list(cc_header)
        
        # BCC
        bcc_header = msg.get("Bcc", "")
        if bcc_header:
            headers["bcc"] = bcc_header
        
        # Date
        date_header = msg.get("Date", "")
        if date_header:
            try:
                headers["date"] = parsedate_to_datetime(date_header)
            except Exception:
                headers["date"] = None
                headers["date_raw"] = date_header
        
        # Message-ID
        headers["message_id"] = msg.get("Message-ID", "")
        
        # Reply-To
        headers["reply_to"] = msg.get("Reply-To", "")
        
        # In-Reply-To (for threading)
        headers["in_reply_to"] = msg.get("In-Reply-To", "")
        
        # References (for threading)
        headers["references"] = msg.get("References", "")
        
        return headers
    
    def _parse_address_list(self, header_value: str) -> list[dict]:
        """Parse a comma-separated list of email addresses."""
        addresses = []
        # Split on comma but handle quoted names
        parts = re.split(r',\s*(?=(?:[^"]*"[^"]*")*[^"]*$)', header_value)
        
        for part in parts:
            part = part.strip()
            if part:
                name, addr = parseaddr(part)
                addresses.append({
                    "name": name,
                    "email": addr,
                    "full": f"{name} <{addr}>" if name else addr,
                })
        
        return addresses
    
    def _extract_body(self, msg: email.message.EmailMessage) -> tuple[str, str]:
        """Extract plain text and HTML body from email."""
        body_text = ""
        body_html = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                # Skip attachments
                if "attachment" in content_disposition:
                    continue
                
                if content_type == "text/plain":
                    try:
                        payload = part.get_payload(decode=True)
                        charset = part.get_content_charset() or "utf-8"
                        body_text += payload.decode(charset, errors="replace")
                    except Exception as e:
                        logger.warning(f"Failed to decode text/plain part: {e}")
                
                elif content_type == "text/html":
                    try:
                        payload = part.get_payload(decode=True)
                        charset = part.get_content_charset() or "utf-8"
                        body_html += payload.decode(charset, errors="replace")
                    except Exception as e:
                        logger.warning(f"Failed to decode text/html part: {e}")
        else:
            # Single part message
            content_type = msg.get_content_type()
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or "utf-8"
                    decoded = payload.decode(charset, errors="replace")
                    
                    if content_type == "text/plain":
                        body_text = decoded
                    elif content_type == "text/html":
                        body_html = decoded
            except Exception as e:
                logger.warning(f"Failed to decode single-part message: {e}")
        
        return body_text.strip(), body_html.strip()
    
    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text."""
        try:
            extractor = HTMLTextExtractor()
            extractor.feed(html)
            return extractor.get_text()
        except Exception as e:
            logger.warning(f"HTML to text conversion failed: {e}")
            # Fallback: strip tags
            text = re.sub(r'<[^>]+>', ' ', html)
            text = re.sub(r'\s+', ' ', text)
            return text.strip()
    
    def _extract_attachments(self, msg: email.message.EmailMessage) -> list[dict]:
        """Extract attachment information (not content)."""
        attachments = []
        
        if msg.is_multipart():
            for part in msg.walk():
                content_disposition = str(part.get("Content-Disposition", ""))
                
                if "attachment" in content_disposition or part.get_filename():
                    filename = part.get_filename()
                    if filename:
                        content_type = part.get_content_type()
                        payload = part.get_payload(decode=True)
                        size = len(payload) if payload else 0
                        
                        attachments.append({
                            "filename": filename,
                            "content_type": content_type,
                            "size": size,
                        })
        
        return attachments
    
    def _build_full_text(
        self,
        headers: dict,
        body_text: str,
        attachments: list[dict],
    ) -> str:
        """Build full text representation of email."""
        parts = []
        
        # Headers section
        parts.append("=== EMAIL HEADERS ===")
        if headers.get("from"):
            parts.append(f"From: {headers['from']}")
        if headers.get("to"):
            parts.append(f"To: {headers['to']}")
        if headers.get("cc"):
            parts.append(f"CC: {headers['cc']}")
        if headers.get("date"):
            date_str = headers["date"].strftime("%Y-%m-%d %H:%M:%S") if isinstance(headers["date"], datetime) else str(headers.get("date_raw", ""))
            parts.append(f"Date: {date_str}")
        if headers.get("subject"):
            parts.append(f"Subject: {headers['subject']}")
        
        parts.append("")
        
        # Body section
        parts.append("=== EMAIL BODY ===")
        if body_text:
            parts.append(body_text)
        else:
            parts.append("[No text content]")
        
        # Attachments section
        if attachments:
            parts.append("")
            parts.append("=== ATTACHMENTS ===")
            for att in attachments:
                size_kb = att["size"] / 1024
                parts.append(f"- {att['filename']} ({att['content_type']}, {size_kb:.1f} KB)")
        
        return "\n".join(parts)
    
    def _create_email_chunks(
        self,
        headers: dict,
        body_text: str,
        attachments: list[dict],
        chunk_size: Optional[int],
        chunk_overlap: Optional[int],
    ) -> list[TextChunk]:
        """Create chunks for email content."""
        chunks = []
        chunk_idx = 0
        
        # Create header chunk
        header_parts = []
        if headers.get("subject"):
            header_parts.append(f"Subject: {headers['subject']}")
        if headers.get("from"):
            header_parts.append(f"From: {headers['from']}")
        if headers.get("to"):
            header_parts.append(f"To: {headers['to']}")
        if headers.get("date"):
            date_str = headers["date"].strftime("%Y-%m-%d %H:%M:%S") if isinstance(headers["date"], datetime) else str(headers.get("date_raw", ""))
            header_parts.append(f"Date: {date_str}")
        
        if header_parts:
            chunks.append(TextChunk(
                content="\n".join(header_parts),
                source="email_headers",
                chunk_index=chunk_idx,
                heading="Email Headers",
            ))
            chunk_idx += 1
        
        # Create body chunks
        if body_text:
            body_chunks = self.chunk_text(
                body_text,
                source_prefix="email_body",
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            
            for bc in body_chunks:
                bc.chunk_index = chunk_idx
                bc.heading = headers.get("subject")
                chunks.append(bc)
                chunk_idx += 1
        
        # Create attachment summary chunk if there are attachments
        if attachments:
            att_text = "Attachments:\n" + "\n".join([
                f"- {att['filename']} ({att['content_type']})"
                for att in attachments
            ])
            chunks.append(TextChunk(
                content=att_text,
                source="email_attachments",
                chunk_index=chunk_idx,
                heading="Attachments",
            ))
        
        return chunks
    
    def _extract_links(self, body_text: str, body_html: str) -> list[str]:
        """Extract URLs from email body."""
        links = set()
        
        # Extract from plain text
        if body_text:
            url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
            links.update(re.findall(url_pattern, body_text))
        
        # Extract from HTML href attributes
        if body_html:
            href_pattern = r'href=["\']([^"\']+)["\']'
            for match in re.findall(href_pattern, body_html, re.IGNORECASE):
                if match.startswith(("http://", "https://")):
                    links.add(match)
        
        return list(links)
