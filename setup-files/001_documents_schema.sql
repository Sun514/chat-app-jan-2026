-- Document Storage Schema with Vector Embeddings
-- Run this after enabling pgvector: CREATE EXTENSION IF NOT EXISTS vector;

-- Main documents table (stores file metadata)
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- File info
    filename VARCHAR(500) NOT NULL,
    file_type VARCHAR(20) NOT NULL,
    file_size INTEGER NOT NULL,
    file_hash VARCHAR(64) NOT NULL,  -- SHA-256
    s3_key VARCHAR(1000),            -- S3 storage location
    
    -- Extracted metadata
    title VARCHAR(500),
    author VARCHAR(255),
    subject TEXT,
    page_count INTEGER,
    word_count INTEGER,
    slide_count INTEGER,
    sheet_count INTEGER,
    
    -- Associations
    investigation_id UUID REFERENCES investigations(id) ON DELETE SET NULL,
    uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Full text for fallback search
    full_text TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Deduplication
    CONSTRAINT documents_file_hash_unique UNIQUE (file_hash, investigation_id)
);

-- Document chunks table (stores text chunks with embeddings)
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    
    -- Chunk info
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    source VARCHAR(100),           -- e.g., "page_1", "slide_3", "sheet_Sales"
    heading VARCHAR(500),          -- Parent heading/section
    page_number INTEGER,
    
    -- Vector embedding (384 dimensions for all-MiniLM-L6-v2)
    embedding vector(384),
    
    -- Metadata
    char_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT document_chunks_unique UNIQUE (document_id, chunk_index)
);

-- Tables extracted from documents
CREATE TABLE IF NOT EXISTS document_tables (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    
    -- Table location
    source VARCHAR(100),           -- e.g., "page_2", "sheet_Data"
    table_index INTEGER NOT NULL,
    
    -- Table data (stored as JSONB for flexibility)
    headers JSONB,                 -- First row / column names
    rows JSONB NOT NULL,           -- All rows including headers
    row_count INTEGER,
    column_count INTEGER,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Links extracted from documents
CREATE TABLE IF NOT EXISTS document_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    
    url TEXT NOT NULL,
    source VARCHAR(100),           -- Where in doc the link was found
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for fast querying
CREATE INDEX IF NOT EXISTS idx_documents_investigation 
    ON documents(investigation_id);

CREATE INDEX IF NOT EXISTS idx_documents_file_type 
    ON documents(file_type);

CREATE INDEX IF NOT EXISTS idx_documents_created_at 
    ON documents(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_documents_file_hash 
    ON documents(file_hash);

CREATE INDEX IF NOT EXISTS idx_document_chunks_document 
    ON document_chunks(document_id);

-- Vector similarity index (IVFFlat for fast approximate search)
-- Adjust lists parameter based on data size: sqrt(row_count) is a good starting point
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding 
    ON document_chunks 
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Full-text search index on documents
CREATE INDEX IF NOT EXISTS idx_documents_fulltext 
    ON documents 
    USING gin(to_tsvector('english', COALESCE(full_text, '')));

-- Full-text search index on chunks
CREATE INDEX IF NOT EXISTS idx_document_chunks_fulltext 
    ON document_chunks 
    USING gin(to_tsvector('english', content));


-- ============================================================================
-- Functions for document search
-- ============================================================================

-- Semantic similarity search across document chunks
CREATE OR REPLACE FUNCTION search_document_chunks(
    query_embedding vector(384),
    similarity_threshold FLOAT DEFAULT 0.5,
    limit_count INTEGER DEFAULT 20,
    investigation_filter UUID DEFAULT NULL
)
RETURNS TABLE (
    chunk_id UUID,
    document_id UUID,
    filename VARCHAR(500),
    file_type VARCHAR(20),
    content TEXT,
    source VARCHAR(100),
    heading VARCHAR(500),
    page_number INTEGER,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        dc.id as chunk_id,
        dc.document_id,
        d.filename,
        d.file_type,
        dc.content,
        dc.source,
        dc.heading,
        dc.page_number,
        (1 - (dc.embedding <=> query_embedding))::FLOAT as similarity
    FROM document_chunks dc
    JOIN documents d ON dc.document_id = d.id
    WHERE 
        (1 - (dc.embedding <=> query_embedding)) > similarity_threshold
        AND (investigation_filter IS NULL OR d.investigation_id = investigation_filter)
    ORDER BY dc.embedding <=> query_embedding
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;


-- Hybrid search: combines semantic + full-text search
CREATE OR REPLACE FUNCTION search_documents_hybrid(
    query_embedding vector(384),
    search_text TEXT,
    semantic_weight FLOAT DEFAULT 0.7,
    limit_count INTEGER DEFAULT 20,
    investigation_filter UUID DEFAULT NULL
)
RETURNS TABLE (
    chunk_id UUID,
    document_id UUID,
    filename VARCHAR(500),
    content TEXT,
    source VARCHAR(100),
    semantic_score FLOAT,
    text_score FLOAT,
    combined_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    WITH semantic_results AS (
        SELECT 
            dc.id,
            dc.document_id,
            dc.content,
            dc.source,
            (1 - (dc.embedding <=> query_embedding))::FLOAT as sem_score
        FROM document_chunks dc
        JOIN documents d ON dc.document_id = d.id
        WHERE investigation_filter IS NULL OR d.investigation_id = investigation_filter
    ),
    text_results AS (
        SELECT 
            dc.id,
            ts_rank(to_tsvector('english', dc.content), plainto_tsquery('english', search_text))::FLOAT as txt_score
        FROM document_chunks dc
        JOIN documents d ON dc.document_id = d.id
        WHERE 
            to_tsvector('english', dc.content) @@ plainto_tsquery('english', search_text)
            AND (investigation_filter IS NULL OR d.investigation_id = investigation_filter)
    )
    SELECT 
        sr.id as chunk_id,
        sr.document_id,
        d.filename,
        sr.content,
        sr.source,
        sr.sem_score as semantic_score,
        COALESCE(tr.txt_score, 0) as text_score,
        (sr.sem_score * semantic_weight + COALESCE(tr.txt_score, 0) * (1 - semantic_weight))::FLOAT as combined_score
    FROM semantic_results sr
    JOIN documents d ON sr.document_id = d.id
    LEFT JOIN text_results tr ON sr.id = tr.id
    ORDER BY combined_score DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;


-- Get document with all chunks (for context building)
CREATE OR REPLACE FUNCTION get_document_context(
    doc_id UUID
)
RETURNS TABLE (
    document_id UUID,
    filename VARCHAR(500),
    file_type VARCHAR(20),
    title VARCHAR(500),
    chunk_index INTEGER,
    content TEXT,
    source VARCHAR(100),
    heading VARCHAR(500),
    page_number INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.id as document_id,
        d.filename,
        d.file_type,
        d.title,
        dc.chunk_index,
        dc.content,
        dc.source,
        dc.heading,
        dc.page_number
    FROM documents d
    JOIN document_chunks dc ON d.id = dc.document_id
    WHERE d.id = doc_id
    ORDER BY dc.chunk_index;
END;
$$ LANGUAGE plpgsql;


-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_documents_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_documents_timestamp();
