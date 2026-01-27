# api/services/documents/registry.py
"""
Parser registry for managing document parsers.
"""

import logging
from typing import Optional

from .base import BaseParser, FileType
from .parsers import (
    DocxParser,
    PptxParser,
    XlsxParser,
    TextParser,
    PdfParser,
    EmlParser,
)

logger = logging.getLogger(__name__)


class ParserRegistry:
    """
    Registry for document parsers.
    Maps file types to their appropriate parsers.
    """
    
    def __init__(self):
        self._parsers: dict[FileType, BaseParser] = {}
        self._register_default_parsers()
    
    def _register_default_parsers(self):
        """Register all built-in parsers."""
        parsers = [
            DocxParser(),
            PptxParser(),
            XlsxParser(),
            TextParser(),
            PdfParser(),
            EmlParser(),
        ]
        
        for parser in parsers:
            for file_type in parser.supported_types:
                self.register(file_type, parser)
    
    def register(self, file_type: FileType, parser: BaseParser):
        """
        Register a parser for a file type.
        
        Args:
            file_type: The file type to register
            parser: The parser instance to use
        """
        self._parsers[file_type] = parser
        logger.debug(f"Registered parser {parser.__class__.__name__} for {file_type.value}")
    
    def get_parser(self, file_type: FileType) -> Optional[BaseParser]:
        """
        Get the parser for a file type.
        
        Args:
            file_type: The file type to get parser for
            
        Returns:
            Parser instance or None if not supported
        """
        return self._parsers.get(file_type)
    
    def get_parser_for_file(self, filename: str) -> Optional[BaseParser]:
        """
        Get the parser for a file based on its extension.
        
        Args:
            filename: Name of the file
            
        Returns:
            Parser instance or None if not supported
        """
        file_type = BaseParser.detect_file_type(filename)
        return self.get_parser(file_type)
    
    def is_supported(self, file_type: FileType) -> bool:
        """Check if a file type is supported."""
        return file_type in self._parsers
    
    def is_file_supported(self, filename: str) -> bool:
        """Check if a file is supported based on extension."""
        file_type = BaseParser.detect_file_type(filename)
        return self.is_supported(file_type)
    
    def supported_types(self) -> list[FileType]:
        """Get list of all supported file types."""
        return list(self._parsers.keys())
    
    def supported_extensions(self) -> list[str]:
        """Get list of all supported file extensions."""
        return [ft.value for ft in self._parsers.keys()]


# Global registry instance
_registry: Optional[ParserRegistry] = None


def get_registry() -> ParserRegistry:
    """Get the global parser registry instance."""
    global _registry
    if _registry is None:
        _registry = ParserRegistry()
    return _registry
