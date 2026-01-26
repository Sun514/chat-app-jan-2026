# api/services/documents/context_builder.py
"""
Context Builder - Retrieves and formats document context for LLM chat.

Integrates with your existing /chat endpoint to provide relevant document
context based on user queries.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from uuid import UUID

logger = logging.getLogger(__name__)


class ContextSourceType(str, Enum):
    """Types of context sources."""
    DOCUMENT = "document"       # Full document by ID
    EMAIL = "email"             # Email by ID
    SEARCH = "search"           # Semantic search results
    HYBRID = "hybrid"           # Hybrid search results


@dataclass
class ContextChunk:
    """A chunk of context with source information."""
    content: str
    source_type: ContextSourceType
    source_id: str
    source_name: str
    relevance_score: Optional[float] = None
    metadata: Optional[dict] = None


@dataclass
class BuiltContext:
    """Complete context ready for LLM."""
    chunks: list[ContextChunk]
    total_tokens_estimate: int
    sources_used: list[dict]
    
    def to_text(self, max_chars: Optional[int] = None) -> str:
        """Format context as text for LLM prompt."""
        parts = []
        current_chars = 0
        
        for chunk in self.chunks:
            header = f"[Source: {chunk.source_name}]"
            if chunk.relevance_score:
                header += f" (relevance: {chunk.relevance_score:.2f})"
            
            chunk_text = f"{header}\n{chunk.content}\n"
            
            if max_chars and current_chars + len(chunk_text) > max_chars:
                break
            
            parts.append(chunk_text)
            current_chars += len(chunk_text)
        
        return "\n---\n".join(parts)


class DocumentContextBuilder:
    """
    Builds context from documents for LLM chat.
    
    Supports multiple retrieval strategies:
    - Direct document retrieval by ID
    - Semantic search for relevant chunks
    - Hybrid search (semantic + keyword)
    - Combined context from multiple sources
    
    Usage:
        builder = DocumentContextBuilder(db_pool)
        
        # Build context from search
        context = await builder.build_from_search(
            query="What are the quarterly revenue figures?",
            max_chunks=10,
            investigation_id="abc-123"
        )
        
        # Use in chat
        llm_prompt = f'''
        Context:
        {context.to_text()}
        
        User Question: {user_message}
        '''
    """
    
    def __init__(
        self,
        db_pool,
        embedding_service=None,
        default_max_chunks: int = 10,
        default_similarity_threshold: float = 0.5,
    ):
        """
        Initialize context builder.
        
        Args:
            db_pool: asyncpg connection pool
            embedding_service: Embedding service (lazy loads if None)
            default_max_chunks: Default max context chunks
            default_similarity_threshold: Default similarity threshold
        """
        self.db_pool = db_pool
        self._embedding_service = embedding_service
        self.default_max_chunks = default_max_chunks
        self.default_similarity_threshold = default_similarity_threshold
    
    @property
    def embedding_service(self):
        """Lazy load embedding service."""
        if self._embedding_service is None:
            from api.services.embeddings.embedding_service import get_embedding_service
            self._embedding_service = get_embedding_service()
        return self._embedding_service
    
    async def build_from_search(
        self,
        query: str,
        max_chunks: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        investigation_id: Optional[str] = None,
        include_emails: bool = False,
    ) -> BuiltContext:
        """
        Build context by searching for relevant chunks.
        
        Args:
            query: User's question/query
            max_chunks: Maximum chunks to include
            similarity_threshold: Minimum similarity score
            investigation_id: Filter by investigation
            include_emails: Also search email database
            
        Returns:
            BuiltContext ready for LLM
        """
        max_chunks = max_chunks or self.default_max_chunks
        similarity_threshold = similarity_threshold or self.default_similarity_threshold
        
        # Generate query embedding
        query_embedding = await self.embedding_service.embed(query)
        
        chunks = []
        sources = []
        
        # Search documents
        async with self.db_pool.acquire() as conn:
            doc_results = await conn.fetch(
                """
                SELECT * FROM search_document_chunks($1, $2, $3, $4)
                """,
                query_embedding,
                similarity_threshold,
                max_chunks,
                UUID(investigation_id) if investigation_id else None,
            )
            
            for row in doc_results:
                chunks.append(ContextChunk(
                    content=row['content'],
                    source_type=ContextSourceType.DOCUMENT,
                    source_id=str(row['document_id']),
                    source_name=f"{row['filename']} ({row['source'] or 'chunk'})",
                    relevance_score=row['similarity'],
                    metadata={
                        "file_type": row['file_type'],
                        "heading": row['heading'],
                        "page_number": row['page_number'],
                    },
                ))
                
                # Track unique sources
                doc_id = str(row['document_id'])
                if not any(s['id'] == doc_id for s in sources):
                    sources.append({
                        "id": doc_id,
                        "type": "document",
                        "name": row['filename'],
                    })
        
        # Optionally search emails
        if include_emails:
            email_chunks = await self._search_emails(
                query_embedding,
                similarity_threshold,
                max_chunks // 2,  # Split budget with documents
                investigation_id,
            )
            chunks.extend(email_chunks)
        
        # Sort by relevance
        chunks.sort(key=lambda c: c.relevance_score or 0, reverse=True)
        
        # Limit total chunks
        chunks = chunks[:max_chunks]
        
        # Estimate tokens (rough: ~4 chars per token)
        total_chars = sum(len(c.content) for c in chunks)
        token_estimate = total_chars // 4
        
        return BuiltContext(
            chunks=chunks,
            total_tokens_estimate=token_estimate,
            sources_used=sources,
        )
    
    async def build_from_document_ids(
        self,
        document_ids: list[str],
        max_chunks_per_doc: int = 20,
    ) -> BuiltContext:
        """
        Build context from specific document IDs.
        
        Args:
            document_ids: List of document UUIDs
            max_chunks_per_doc: Max chunks per document
            
        Returns:
            BuiltContext with document contents
        """
        chunks = []
        sources = []
        
        async with self.db_pool.acquire() as conn:
            for doc_id in document_ids:
                rows = await conn.fetch(
                    """
                    SELECT 
                        d.filename, d.file_type,
                        dc.content, dc.source, dc.heading, dc.page_number
                    FROM documents d
                    JOIN document_chunks dc ON d.id = dc.document_id
                    WHERE d.id = $1
                    ORDER BY dc.chunk_index
                    LIMIT $2
                    """,
                    UUID(doc_id),
                    max_chunks_per_doc,
                )
                
                if rows:
                    sources.append({
                        "id": doc_id,
                        "type": "document",
                        "name": rows[0]['filename'],
                    })
                    
                    for row in rows:
                        chunks.append(ContextChunk(
                            content=row['content'],
                            source_type=ContextSourceType.DOCUMENT,
                            source_id=doc_id,
                            source_name=f"{row['filename']} ({row['source'] or 'chunk'})",
                            metadata={
                                "file_type": row['file_type'],
                                "heading": row['heading'],
                                "page_number": row['page_number'],
                            },
                        ))
        
        total_chars = sum(len(c.content) for c in chunks)
        
        return BuiltContext(
            chunks=chunks,
            total_tokens_estimate=total_chars // 4,
            sources_used=sources,
        )
    
    async def build_hybrid(
        self,
        query: str,
        max_chunks: Optional[int] = None,
        semantic_weight: float = 0.7,
        investigation_id: Optional[str] = None,
    ) -> BuiltContext:
        """
        Build context using hybrid search (semantic + keyword).
        
        Best for queries that benefit from both understanding
        and exact keyword matching.
        
        Args:
            query: Search query
            max_chunks: Maximum chunks
            semantic_weight: Balance between semantic/keyword (0-1)
            investigation_id: Filter by investigation
            
        Returns:
            BuiltContext with ranked results
        """
        max_chunks = max_chunks or self.default_max_chunks
        query_embedding = await self.embedding_service.embed(query)
        
        chunks = []
        sources = []
        
        async with self.db_pool.acquire() as conn:
            results = await conn.fetch(
                """
                SELECT * FROM search_documents_hybrid($1, $2, $3, $4, $5)
                """,
                query_embedding,
                query,
                semantic_weight,
                max_chunks,
                UUID(investigation_id) if investigation_id else None,
            )
            
            for row in results:
                chunks.append(ContextChunk(
                    content=row['content'],
                    source_type=ContextSourceType.HYBRID,
                    source_id=str(row['document_id']),
                    source_name=f"{row['filename']} ({row['source'] or 'chunk'})",
                    relevance_score=row['combined_score'],
                    metadata={
                        "semantic_score": row['semantic_score'],
                        "text_score": row['text_score'],
                    },
                ))
                
                doc_id = str(row['document_id'])
                if not any(s['id'] == doc_id for s in sources):
                    sources.append({
                        "id": doc_id,
                        "type": "document",
                        "name": row['filename'],
                    })
        
        total_chars = sum(len(c.content) for c in chunks)
        
        return BuiltContext(
            chunks=chunks,
            total_tokens_estimate=total_chars // 4,
            sources_used=sources,
        )
    
    async def _search_emails(
        self,
        query_embedding: list[float],
        threshold: float,
        limit: int,
        investigation_id: Optional[str],
    ) -> list[ContextChunk]:
        """Search emails for relevant content."""
        chunks = []
        
        try:
            async with self.db_pool.acquire() as conn:
                # Assuming you have an email_embeddings table
                rows = await conn.fetch(
                    """
                    SELECT 
                        e.id,
                        e.subject,
                        e.sender,
                        e.body_text,
                        (1 - (ee.content_embedding <=> $1))::FLOAT as similarity
                    FROM email_embeddings ee
                    JOIN emails e ON ee.email_id = e.id
                    WHERE 
                        (1 - (ee.content_embedding <=> $1)) > $2
                        AND ($4::UUID IS NULL OR e.investigation_id = $4)
                    ORDER BY ee.content_embedding <=> $1
                    LIMIT $3
                    """,
                    query_embedding,
                    threshold,
                    limit,
                    UUID(investigation_id) if investigation_id else None,
                )
                
                for row in rows:
                    chunks.append(ContextChunk(
                        content=f"Subject: {row['subject']}\nFrom: {row['sender']}\n\n{row['body_text']}",
                        source_type=ContextSourceType.EMAIL,
                        source_id=str(row['id']),
                        source_name=f"Email: {row['subject'][:50]}",
                        relevance_score=row['similarity'],
                    ))
        except Exception as e:
            logger.warning(f"Email search failed: {e}")
        
        return chunks


async def build_chat_context(
    db_pool,
    query: str,
    document_ids: Optional[list[str]] = None,
    email_ids: Optional[list[str]] = None,
    investigation_id: Optional[str] = None,
    max_context_items: int = 10,
    search_threshold: float = 0.5,
) -> dict:
    """
    Convenience function to build context for chat endpoint.
    
    Matches the pattern from your existing /chat endpoint.
    
    Args:
        db_pool: Database connection pool
        query: User's question
        document_ids: Specific documents to include
        email_ids: Specific emails to include  
        investigation_id: Filter search to investigation
        max_context_items: Maximum context chunks
        search_threshold: Similarity threshold for search
        
    Returns:
        Dict with formatted context and metadata
    """
    builder = DocumentContextBuilder(db_pool)
    
    context_parts = []
    all_sources = []
    
    # Add specific documents
    if document_ids:
        doc_context = await builder.build_from_document_ids(
            document_ids,
            max_chunks_per_doc=max_context_items // len(document_ids),
        )
        context_parts.append(doc_context)
        all_sources.extend(doc_context.sources_used)
    
    # Search for additional relevant content
    search_limit = max_context_items - sum(len(c.chunks) for c in context_parts)
    if search_limit > 0:
        search_context = await builder.build_from_search(
            query=query,
            max_chunks=search_limit,
            similarity_threshold=search_threshold,
            investigation_id=investigation_id,
            include_emails=True,
        )
        context_parts.append(search_context)
        all_sources.extend(search_context.sources_used)
    
    # Combine all context
    all_chunks = []
    for ctx in context_parts:
        all_chunks.extend(ctx.chunks)
    
    # Format for LLM
    formatted_context = "\n\n---\n\n".join([
        f"[{chunk.source_name}]\n{chunk.content}"
        for chunk in all_chunks
    ])
    
    return {
        "context": formatted_context,
        "sources": all_sources,
        "chunk_count": len(all_chunks),
        "token_estimate": sum(c.total_tokens_estimate for c in context_parts),
    }
