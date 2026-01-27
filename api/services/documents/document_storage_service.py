# api/services/documents/document_storage_service.py
"""
Document Storage Service - Stores parsed documents with vector embeddings in PostgreSQL.
"""

import logging
from datetime import datetime
from typing import BinaryIO, Optional
from uuid import UUID
import json

from .base import DocumentContent, DocumentMetadata, ParserResult, TextChunk
from .parser_service import DocumentParserService

logger = logging.getLogger(__name__)


class DocumentStorageService:
    """
    Service for storing parsed documents in PostgreSQL with vector embeddings.
    
    Integrates:
    - Document parsing (extract text from various file types)
    - Embedding generation (convert text chunks to 384-dim vectors)
    - PostgreSQL storage (with pgvector for similarity search)
    - Optional S3 storage for original files
    
    Usage:
        storage = DocumentStorageService(db_pool)
        
        # Store a document
        doc_id = await storage.store_document(
            file_data,
            "report.docx",
            investigation_id="abc-123",
            user_id="user-456"
        )
        
        # Search documents
        results = await storage.search_similar(
            "quarterly revenue performance",
            limit=10
        )
    """
    
    def __init__(
        self,
        db_pool,
        embedding_service=None,
        s3_service=None,
        parser_service: Optional[DocumentParserService] = None,
    ):
        """
        Initialize document storage service.
        
        Args:
            db_pool: asyncpg connection pool
            embedding_service: Service for generating embeddings (lazy loads if None)
            s3_service: Optional S3 service for storing original files
            parser_service: Document parser service (creates default if None)
        """
        self.db_pool = db_pool
        self._embedding_service = embedding_service
        self.s3_service = s3_service
        self.parser_service = parser_service or DocumentParserService()
    
    @property
    def embedding_service(self):
        """Lazy load embedding service."""
        if self._embedding_service is None:
            from api.services.embeddings.embedding_service import get_embedding_service
            self._embedding_service = get_embedding_service()
        return self._embedding_service
    
    async def store_document(
        self,
        file_data: BinaryIO,
        filename: str,
        investigation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        store_original: bool = True,
    ) -> Optional[str]:
        """
        Parse and store a document with embeddings.
        
        Args:
            file_data: File-like object with document bytes
            filename: Original filename
            investigation_id: Optional investigation to associate with
            user_id: User who uploaded the document
            chunk_size: Max characters per chunk
            chunk_overlap: Overlap between chunks
            store_original: Whether to store original file in S3
            
        Returns:
            Document ID (UUID string) or None if failed
        """
        # Read file bytes
        file_bytes = file_data.read()
        file_data.seek(0)  # Reset for potential re-read
        
        # Parse the document
        from io import BytesIO
        result = await self.parser_service.parse_upload(
            BytesIO(file_bytes),
            filename,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        
        if not result.success:
            logger.error(f"Failed to parse document {filename}: {result.error}")
            return None
        
        if not result.content.chunks:
            logger.error(f"No chunks extracted from document {filename}")
            return None
        
        # Check for duplicate by file hash
        existing = await self._check_duplicate(
            result.metadata.file_hash,
            investigation_id
        )
        if existing:
            logger.info(f"Replacing existing document: {existing}")
            deleted = await self.delete_document(existing)
            if not deleted:
                logger.error(f"Failed to delete existing document: {existing}")
                return None
        
        # Store original file in S3 if configured
        s3_key = None
        if store_original and self.s3_service:
            try:
                folder = f"documents/{investigation_id}" if investigation_id else "documents"
                s3_key = await self.s3_service.upload_file(
                    BytesIO(file_bytes),
                    filename,
                    folder=folder,
                )
            except Exception as e:
                logger.warning(f"Failed to upload to S3: {e}")
        
        # Generate embeddings for all chunks
        chunk_texts = [c.content for c in result.content.chunks]
        embeddings = await self.embedding_service.embed_batch(chunk_texts)
        
        # Store in database
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                # Insert document
                doc_id = await self._insert_document(
                    conn,
                    result.metadata,
                    result.content.full_text,
                    s3_key,
                    investigation_id,
                    user_id,
                )
                
                # Insert chunks with embeddings
                await self._insert_chunks(
                    conn,
                    doc_id,
                    result.content.chunks,
                    embeddings,
                )
                
                # Insert tables
                if result.content.tables:
                    await self._insert_tables(
                        conn,
                        doc_id,
                        result.content.tables,
                    )
                
                # Insert links
                if result.content.links:
                    await self._insert_links(
                        conn,
                        doc_id,
                        result.content.links,
                    )
        
        logger.info(f"Stored document {filename} with {len(result.content.chunks)} chunks")
        return str(doc_id)
    
    async def _check_duplicate(
        self,
        file_hash: str,
        investigation_id: Optional[str],
    ) -> Optional[str]:
        """Check if document already exists by hash."""
        async with self.db_pool.acquire() as conn:
            if investigation_id:
                row = await conn.fetchrow(
                    """
                    SELECT id FROM documents 
                    WHERE file_hash = $1 AND investigation_id = $2
                    """,
                    file_hash,
                    UUID(investigation_id),
                )
            else:
                row = await conn.fetchrow(
                    """
                    SELECT id FROM documents 
                    WHERE file_hash = $1 AND investigation_id IS NULL
                    """,
                    file_hash,
                )
            return str(row['id']) if row else None
    
    async def _insert_document(
        self,
        conn,
        metadata: DocumentMetadata,
        full_text: str,
        s3_key: Optional[str],
        investigation_id: Optional[str],
        user_id: Optional[str],
    ) -> UUID:
        """Insert document record."""
        row = await conn.fetchrow(
            """
            INSERT INTO documents (
                filename, file_type, file_size, file_hash, s3_key,
                title, author, subject, page_count, word_count,
                slide_count, sheet_count, investigation_id, uploaded_by,
                full_text
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15
            )
            RETURNING id
            """,
            metadata.filename,
            metadata.file_type.value,
            metadata.file_size,
            metadata.file_hash,
            s3_key,
            metadata.title,
            metadata.author,
            metadata.subject,
            metadata.page_count,
            metadata.word_count,
            metadata.slide_count,
            metadata.sheet_count,
            UUID(investigation_id) if investigation_id else None,
            UUID(user_id) if user_id else None,
            full_text,
        )
        return row['id']
    
    async def _insert_chunks(
        self,
        conn,
        doc_id: UUID,
        chunks: list[TextChunk],
        embeddings: list[list[float]],
    ):
        """Insert document chunks with embeddings."""
        if not chunks:
            return
        
        # Use COPY for bulk insert (faster)
        records = [
            (
                doc_id,
                chunk.chunk_index,
                chunk.content,
                chunk.source,
                chunk.heading,
                chunk.page_number,
                embeddings[i],  # pgvector handles list -> vector conversion
                len(chunk.content),
            )
            for i, chunk in enumerate(chunks)
        ]
        
        await conn.executemany(
            """
            INSERT INTO document_chunks (
                document_id, chunk_index, content, source, heading,
                page_number, embedding, char_count
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            records,
        )
    
    async def _insert_tables(self, conn, doc_id: UUID, tables: list[dict]):
        """Insert extracted tables."""
        for i, table in enumerate(tables):
            source = table.get('page') or table.get('slide') or table.get('sheet') or table.get('index')
            rows = table.get('rows', [])
            headers = rows[0] if rows else None
            
            await conn.execute(
                """
                INSERT INTO document_tables (
                    document_id, source, table_index, headers, rows,
                    row_count, column_count
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                doc_id,
                str(source) if source else f"table_{i}",
                i,
                json.dumps(headers) if headers else None,
                json.dumps(rows),
                len(rows),
                len(rows[0]) if rows else 0,
            )
    
    async def _insert_links(self, conn, doc_id: UUID, links: list[str]):
        """Insert extracted links."""
        unique_links = list(set(links))
        for url in unique_links:
            await conn.execute(
                """
                INSERT INTO document_links (document_id, url)
                VALUES ($1, $2)
                ON CONFLICT DO NOTHING
                """,
                doc_id,
                url,
            )
    
    async def search_similar(
        self,
        query: str,
        limit: int = 20,
        similarity_threshold: float = 0.5,
        investigation_id: Optional[str] = None,
    ) -> list[dict]:
        """
        Search for document chunks similar to the query.
        
        Args:
            query: Search query text
            limit: Maximum results to return
            similarity_threshold: Minimum similarity score (0-1)
            investigation_id: Filter by investigation
            
        Returns:
            List of matching chunks with similarity scores
        """
        # Generate query embedding
        query_embedding = await self.embedding_service.embed(query)
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM search_document_chunks($1, $2, $3, $4)
                """,
                query_embedding,
                similarity_threshold,
                limit,
                UUID(investigation_id) if investigation_id else None,
            )
        
        return [dict(row) for row in rows]
    
    async def search_hybrid(
        self,
        query: str,
        limit: int = 20,
        semantic_weight: float = 0.7,
        investigation_id: Optional[str] = None,
    ) -> list[dict]:
        """
        Hybrid search combining semantic similarity and full-text search.
        
        Args:
            query: Search query text
            limit: Maximum results to return
            semantic_weight: Weight for semantic vs text search (0-1)
            investigation_id: Filter by investigation
            
        Returns:
            List of matching chunks with combined scores
        """
        query_embedding = await self.embedding_service.embed(query)
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM search_documents_hybrid($1, $2, $3, $4, $5)
                """,
                query_embedding,
                query,
                semantic_weight,
                limit,
                UUID(investigation_id) if investigation_id else None,
            )
        
        return [dict(row) for row in rows]
    
    async def get_document(self, document_id: str) -> Optional[dict]:
        """Get document metadata by ID."""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    id, filename, file_type, file_size, title, author,
                    page_count, word_count, slide_count, sheet_count,
                    investigation_id, created_at
                FROM documents
                WHERE id = $1
                """,
                UUID(document_id),
            )
            return dict(row) if row else None
    
    async def get_document_chunks(self, document_id: str) -> list[dict]:
        """Get all chunks for a document."""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    id, chunk_index, content, source, heading,
                    page_number, char_count
                FROM document_chunks
                WHERE document_id = $1
                ORDER BY chunk_index
                """,
                UUID(document_id),
            )
            return [dict(row) for row in rows]
    
    async def get_document_context(self, document_id: str) -> list[dict]:
        """Get document with all chunks for context building."""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM get_document_context($1)
                """,
                UUID(document_id),
            )
            return [dict(row) for row in rows]
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete a document and all related data."""
        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                """
                DELETE FROM documents WHERE id = $1
                """,
                UUID(document_id),
            )
            return result == "DELETE 1"
    
    async def list_documents(
        self,
        investigation_id: Optional[str] = None,
        file_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """List documents with optional filters."""
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT 
                    id, filename, file_type, file_size, title,
                    page_count, word_count, created_at
                FROM documents
                WHERE 1=1
            """
            params = []
            param_idx = 1
            
            if investigation_id:
                query += f" AND investigation_id = ${param_idx}"
                params.append(UUID(investigation_id))
                param_idx += 1
            
            if file_type:
                query += f" AND file_type = ${param_idx}"
                params.append(file_type)
                param_idx += 1
            
            query += f" ORDER BY created_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
            params.extend([limit, offset])
            
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
