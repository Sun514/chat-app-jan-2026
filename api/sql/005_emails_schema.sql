-- Emails table
CREATE TABLE IF NOT EXISTS emails (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    investigation_id UUID REFERENCES investigations(id) ON DELETE SET NULL,

    -- Email headers
    message_id VARCHAR(500),
    subject TEXT,
    sender VARCHAR(500),
    recipients JSONB,
    cc JSONB,
    bcc JSONB,

    -- Content
    body_text TEXT,
    body_html TEXT,

    -- Dates
    sent_at TIMESTAMP WITH TIME ZONE,
    received_at TIMESTAMP WITH TIME ZONE,

    -- Source
    source_file VARCHAR(500),
    folder_path VARCHAR(500),

    -- Metadata
    has_attachments BOOLEAN DEFAULT false,
    attachment_count INTEGER DEFAULT 0,
    is_spam BOOLEAN DEFAULT false,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Email embeddings
CREATE TABLE IF NOT EXISTS email_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email_id UUID NOT NULL REFERENCES emails(id) ON DELETE CASCADE,

    content_embedding vector(384),
    subject_embedding vector(384),

    embedding_model VARCHAR(100) DEFAULT 'all-MiniLM-L6-v2',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT email_embeddings_unique UNIQUE (email_id)
);

-- Email attachments
CREATE TABLE IF NOT EXISTS email_attachments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email_id UUID NOT NULL REFERENCES emails(id) ON DELETE CASCADE,

    filename VARCHAR(500) NOT NULL,
    content_type VARCHAR(100),
    file_size INTEGER,
    s3_key VARCHAR(1000),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_emails_investigation ON emails(investigation_id);
CREATE INDEX IF NOT EXISTS idx_emails_sender ON emails(sender);
CREATE INDEX IF NOT EXISTS idx_emails_sent_at ON emails(sent_at DESC);
CREATE INDEX IF NOT EXISTS idx_emails_subject_trgm ON emails USING gin(subject gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_email_embeddings_content 
    ON email_embeddings 
    USING ivfflat (content_embedding vector_cosine_ops)
    WITH (lists = 100);

-- Email search function
CREATE OR REPLACE FUNCTION search_emails_by_content(
    query_embedding vector(384),
    similarity_threshold FLOAT DEFAULT 0.5,
    limit_count INTEGER DEFAULT 20,
    investigation_filter UUID DEFAULT NULL
)
RETURNS TABLE (
    email_id UUID,
    subject TEXT,
    sender VARCHAR(500),
    body_preview TEXT,
    sent_at TIMESTAMP WITH TIME ZONE,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.id as email_id,
        e.subject,
        e.sender,
        LEFT(e.body_text, 500) as body_preview,
        e.sent_at,
        (1 - (ee.content_embedding <=> query_embedding))::FLOAT as similarity
    FROM email_embeddings ee
    JOIN emails e ON ee.email_id = e.id
    WHERE 
        (1 - (ee.content_embedding <=> query_embedding)) > similarity_threshold
        AND (investigation_filter IS NULL OR e.investigation_id = investigation_filter)
    ORDER BY ee.content_embedding <=> query_embedding
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;
