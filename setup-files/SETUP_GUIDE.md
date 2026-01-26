# Red Pajama - Complete Setup Guide

A FastAPI application for document processing, email analysis, and LLM-powered investigations with vector embeddings for semantic search.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [System Dependencies](#2-system-dependencies)
3. [Project Structure](#3-project-structure)
4. [Database Setup](#4-database-setup)
5. [Python Environment](#5-python-environment)
6. [Configuration](#6-configuration)
7. [Core Application Files](#7-core-application-files)
8. [Running the Application](#8-running-the-application)
9. [Testing the Setup](#9-testing-the-setup)
10. [API Endpoints Reference](#10-api-endpoints-reference)

---

## 1. Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.11+ | Runtime |
| PostgreSQL | 15+ | Database with pgvector |
| Redis | 7+ | Caching (optional) |
| LibreOffice | 7+ | Legacy document conversion |

### Hardware Recommendations

- **RAM**: 8GB minimum (16GB for production)
- **Storage**: 20GB+ for document storage
- **CPU**: 4 cores recommended for embedding generation

---

## 2. System Dependencies

### Ubuntu/Debian

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and build tools
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip
sudo apt install -y build-essential gcc g++ make

# Install PostgreSQL 15+
sudo apt install -y postgresql postgresql-contrib postgresql-server-dev-all

# Install pgvector extension dependencies
sudo apt install -y git

# Install LibreOffice (for .doc, .ppt, .xls conversion)
sudo apt install -y libreoffice-common libreoffice-writer libreoffice-calc libreoffice-impress

# Install Pandoc (document conversion fallback)
sudo apt install -y pandoc

# Install unrtf (RTF support)
sudo apt install -y unrtf

# Install poppler-utils (PDF utilities)
sudo apt install -y poppler-utils
```

### RHEL/CentOS/Rocky Linux

```bash
# Enable EPEL repository
sudo dnf install -y epel-release

# Install Python
sudo dnf install -y python3.11 python3.11-devel python3-pip
sudo dnf install -y gcc gcc-c++ make

# Install PostgreSQL
sudo dnf install -y postgresql-server postgresql-contrib postgresql-devel

# Initialize PostgreSQL
sudo postgresql-setup --initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Install LibreOffice
sudo dnf install -y libreoffice

# Install Pandoc
sudo dnf install -y pandoc
```

### Install pgvector Extension

```bash
# Clone and build pgvector
cd /tmp
git clone --branch v0.6.0 https://github.com/pgvector/pgvector.git
cd pgvector

# Build and install
make
sudo make install

# Verify installation
psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS vector;" template1
```

---

## 3. Project Structure

Create the project directory structure:

```bash
# Create project root
mkdir -p red-pajama
cd red-pajama

# Create directory structure
mkdir -p api/{routers,services,core,utils}
mkdir -p api/services/{documents,embeddings,storage,llm,users,investigations}
mkdir -p api/services/documents/parsers
mkdir -p config/{cerbos/policies,cerbos/schemas}
mkdir -p sql
mkdir -p temp/{uploads,processing,extracted,cache}
mkdir -p tests
mkdir -p scripts

# Create __init__.py files
touch api/__init__.py
touch api/routers/__init__.py
touch api/services/__init__.py
touch api/services/documents/__init__.py
touch api/services/documents/parsers/__init__.py
touch api/services/embeddings/__init__.py
touch api/services/storage/__init__.py
touch api/services/llm/__init__.py
touch api/services/users/__init__.py
touch api/services/investigations/__init__.py
touch api/core/__init__.py
touch api/utils/__init__.py
touch tests/__init__.py
```

### Final Project Structure

```
red-pajama/
├── api/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry
│   ├── config.py                  # Configuration management
│   ├── dependencies.py            # Shared dependencies
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── general.py             # Health, version endpoints
│   │   ├── documents.py           # Document upload/search
│   │   ├── chat.py                # LLM chat endpoints
│   │   ├── users.py
│   │   └── investigations.py
│   │
│   ├── services/
│   │   ├── documents/
│   │   │   ├── __init__.py
│   │   │   ├── base.py            # Base classes, models
│   │   │   ├── parser_service.py  # Main parser service
│   │   │   ├── registry.py        # Parser registry
│   │   │   ├── document_storage_service.py
│   │   │   ├── context_builder.py
│   │   │   └── parsers/
│   │   │       ├── __init__.py
│   │   │       ├── docx_parser.py
│   │   │       ├── pptx_parser.py
│   │   │       ├── xlsx_parser.py
│   │   │       ├── pdf_parser.py
│   │   │       └── text_parser.py
│   │   │
│   │   ├── embeddings/
│   │   │   ├── __init__.py
│   │   │   └── embedding_service.py
│   │   │
│   │   ├── storage/
│   │   │   ├── __init__.py
│   │   │   ├── s3_service.py
│   │   │   └── local_service.py
│   │   │
│   │   └── llm/
│   │       ├── __init__.py
│   │       ├── openai_service.py
│   │       ├── bedrock_service.py
│   │       └── claude_service.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── database.py            # PostgreSQL connection
│   │   └── storage.py             # S3 client
│   │
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
│
├── sql/
│   ├── 001_extensions.sql
│   ├── 002_users_schema.sql
│   ├── 003_investigations_schema.sql
│   ├── 004_documents_schema.sql
│   └── 005_emails_schema.sql
│
├── config/
│   ├── logging.json
│   └── features.json
│
├── temp/                          # Temporary files (gitignored)
│
├── tests/
│   ├── __init__.py
│   ├── test_documents.py
│   └── test_search.py
│
├── scripts/
│   └── init_db.py
│
├── .env.example
├── .gitignore
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## 4. Database Setup

### 4.1 Create Database and User

```bash
# Connect as postgres user
sudo -u postgres psql

# In PostgreSQL shell:
```

```sql
-- Create database user
CREATE USER redpajama WITH PASSWORD 'your_secure_password_here';

-- Create database
CREATE DATABASE redpajama_db OWNER redpajama;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE redpajama_db TO redpajama;

-- Connect to the new database
\c redpajama_db

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Verify extensions
\dx

-- Exit
\q
```

### 4.2 Create SQL Schema Files

**sql/001_extensions.sql**
```sql
-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

**sql/002_users_schema.sql**
```sql
-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    hashed_password VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
```

**sql/003_investigations_schema.sql**
```sql
-- Investigations table
CREATE TABLE IF NOT EXISTS investigations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_investigations_status ON investigations(status);
CREATE INDEX IF NOT EXISTS idx_investigations_created_by ON investigations(created_by);
```

**sql/004_documents_schema.sql**
```sql
-- Documents table (stores file metadata)
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- File info
    filename VARCHAR(500) NOT NULL,
    file_type VARCHAR(20) NOT NULL,
    file_size INTEGER NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    s3_key VARCHAR(1000),
    
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
    
    CONSTRAINT documents_file_hash_unique UNIQUE (file_hash, investigation_id)
);

-- Document chunks table (stores text chunks with embeddings)
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    source VARCHAR(100),
    heading VARCHAR(500),
    page_number INTEGER,
    
    -- Vector embedding (384 dimensions for all-MiniLM-L6-v2)
    embedding vector(384),
    
    char_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT document_chunks_unique UNIQUE (document_id, chunk_index)
);

-- Tables extracted from documents
CREATE TABLE IF NOT EXISTS document_tables (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    
    source VARCHAR(100),
    table_index INTEGER NOT NULL,
    headers JSONB,
    rows JSONB NOT NULL,
    row_count INTEGER,
    column_count INTEGER,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Links extracted from documents
CREATE TABLE IF NOT EXISTS document_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    source VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_documents_investigation ON documents(investigation_id);
CREATE INDEX IF NOT EXISTS idx_documents_file_type ON documents(file_type);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_documents_file_hash ON documents(file_hash);
CREATE INDEX IF NOT EXISTS idx_document_chunks_document ON document_chunks(document_id);

-- Vector similarity index (IVFFlat)
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding 
    ON document_chunks 
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Full-text search indexes
CREATE INDEX IF NOT EXISTS idx_documents_fulltext 
    ON documents 
    USING gin(to_tsvector('english', COALESCE(full_text, '')));

CREATE INDEX IF NOT EXISTS idx_document_chunks_fulltext 
    ON document_chunks 
    USING gin(to_tsvector('english', content));

-- Search function: Semantic similarity search
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

-- Search function: Hybrid search (semantic + full-text)
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

-- Get document context
CREATE OR REPLACE FUNCTION get_document_context(doc_id UUID)
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

-- Timestamp update trigger
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();
```

**sql/005_emails_schema.sql**
```sql
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
```

### 4.3 Run Schema Migration

```bash
# Run all SQL files in order
psql -U redpajama -d redpajama_db -f sql/001_extensions.sql
psql -U redpajama -d redpajama_db -f sql/002_users_schema.sql
psql -U redpajama -d redpajama_db -f sql/003_investigations_schema.sql
psql -U redpajama -d redpajama_db -f sql/004_documents_schema.sql
psql -U redpajama -d redpajama_db -f sql/005_emails_schema.sql

# Or use a script
for f in sql/*.sql; do
    echo "Running $f..."
    psql -U redpajama -d redpajama_db -f "$f"
done
```

---

## 5. Python Environment

### 5.1 Create Virtual Environment

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
# venv\Scripts\activate
```

### 5.2 Create requirements.txt

```txt
# Core Framework
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
pydantic>=2.5.0
pydantic-settings>=2.1.0

# Database
asyncpg>=0.29.0
psycopg2-binary>=2.9.9

# Document Parsing
python-docx>=1.1.0
python-pptx>=0.6.23
openpyxl>=3.1.2
pdfplumber>=0.10.3
PyMuPDF>=1.23.0
pandas>=2.0.0

# Vector Embeddings
sentence-transformers>=2.2.0
numpy>=1.24.0

# LLM Integration
openai>=1.10.0
anthropic>=0.18.0
boto3>=1.34.0          # For AWS Bedrock

# File Storage
boto3>=1.34.0          # For S3

# Security
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6

# Utilities
python-dotenv>=1.0.0
httpx>=0.26.0
aiofiles>=23.2.1

# Testing
pytest>=8.0.0
pytest-asyncio>=0.23.0
httpx>=0.26.0

# Development
black>=24.1.0
isort>=5.13.0
mypy>=1.8.0
```

### 5.3 Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# Verify sentence-transformers (downloads model on first use)
python -c "from sentence_transformers import SentenceTransformer; m = SentenceTransformer('all-MiniLM-L6-v2'); print('Model loaded successfully')"
```

---

## 6. Configuration

### 6.1 Create .env.example

```bash
# Application
APP_NAME=RedPajama
APP_VERSION=1.0.0
DEBUG=false
LOG_LEVEL=INFO

# Server
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=postgresql://redpajama:your_password@localhost:5432/redpajama_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# S3 Storage (optional)
S3_BUCKET=redpajama-documents
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# LLM Services
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Embedding Model
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# Security
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]
```

### 6.2 Create .env (copy and modify)

```bash
cp .env.example .env
# Edit .env with your actual values
nano .env
```

### 6.3 Create .gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
.venv/
ENV/
env/
.eggs/
*.egg-info/
dist/
build/

# Environment
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# Logs
*.log
logs/

# Temporary files
temp/
tmp/
*.tmp

# OS
.DS_Store
Thumbs.db

# Database
*.db
*.sqlite3

# Uploads (local development)
uploads/
```

---

## 7. Core Application Files

### 7.1 api/config.py

```python
"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "RedPajama"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database
    database_url: str
    database_pool_size: int = 20
    database_max_overflow: int = 10
    
    # S3 Storage
    s3_bucket: Optional[str] = None
    s3_region: str = "us-east-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    
    # LLM Services
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # Embedding
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    
    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
```

### 7.2 api/core/database.py

```python
"""PostgreSQL database connection with asyncpg."""

import logging
from contextlib import asynccontextmanager
from typing import Any, Optional

import asyncpg
from asyncpg import Pool

from api.config import settings

logger = logging.getLogger(__name__)

_pool: Optional[Pool] = None


async def init_pool() -> Pool:
    """Initialize the database connection pool."""
    global _pool
    
    if _pool is None:
        logger.info("Creating database connection pool...")
        _pool = await asyncpg.create_pool(
            dsn=settings.database_url,
            min_size=5,
            max_size=settings.database_pool_size,
            max_inactive_connection_lifetime=300,
        )
        logger.info("Database pool created successfully")
    
    return _pool


async def close_pool():
    """Close the database connection pool."""
    global _pool
    
    if _pool:
        logger.info("Closing database connection pool...")
        await _pool.close()
        _pool = None
        logger.info("Database pool closed")


async def get_pool() -> Pool:
    """Get the database connection pool."""
    if _pool is None:
        await init_pool()
    return _pool


@asynccontextmanager
async def get_connection():
    """Get a database connection from the pool."""
    pool = await get_pool()
    async with pool.acquire() as connection:
        yield connection


async def execute(query: str, *args) -> str:
    """Execute a query and return status."""
    async with get_connection() as conn:
        return await conn.execute(query, *args)


async def fetch_one(query: str, *args) -> Optional[dict]:
    """Fetch a single row."""
    async with get_connection() as conn:
        row = await conn.fetchrow(query, *args)
        return dict(row) if row else None


async def fetch_all(query: str, *args) -> list[dict]:
    """Fetch all rows."""
    async with get_connection() as conn:
        rows = await conn.fetch(query, *args)
        return [dict(row) for row in rows]


async def insert_one(table: str, data: dict[str, Any]) -> Any:
    """Insert a single row and return the ID."""
    columns = ", ".join(data.keys())
    placeholders = ", ".join(f"${i+1}" for i in range(len(data)))
    values = list(data.values())
    
    query = f"""
        INSERT INTO {table} ({columns})
        VALUES ({placeholders})
        RETURNING id
    """
    
    async with get_connection() as conn:
        row = await conn.fetchrow(query, *values)
        return row["id"] if row else None
```

### 7.3 api/main.py

```python
"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.core.database import init_pool, close_pool

# Import routers
from api.routers import general, documents, chat

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    await init_pool()
    logger.info("Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    await close_pool()
    logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Document processing and LLM-powered investigations",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(general.router)
app.include_router(documents.router)
app.include_router(chat.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
```

### 7.4 api/routers/general.py

```python
"""General endpoints: health, version, etc."""

from fastapi import APIRouter

from api.config import settings
from api.core.database import get_pool

router = APIRouter(tags=["general"])


@router.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    # Check database connection
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
    }


@router.get("/version")
async def version():
    """Version information."""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
    }
```

---

## 8. Running the Application

### 8.1 Development Mode

```bash
# Activate virtual environment
source venv/bin/activate

# Run with auto-reload
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Or using Python directly
python -m api.main
```

### 8.2 Production Mode

```bash
# Run with multiple workers
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4

# Or using Gunicorn
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### 8.3 Docker (Optional)

**Dockerfile**
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libreoffice-common \
    libreoffice-writer \
    pandoc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml**
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://redpajama:password@db:5432/redpajama_db
    depends_on:
      - db

  db:
    image: pgvector/pgvector:pg16
    environment:
      - POSTGRES_USER=redpajama
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=redpajama_db
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./sql:/docker-entrypoint-initdb.d

volumes:
  pgdata:
```

---

## 9. Testing the Setup

### 9.1 Verify Database Connection

```bash
# Test database connection
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "healthy"
}
```

### 9.2 Test Document Upload

```bash
# Upload a test document
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@test_document.docx" \
  -F "chunk_size=1000"
```

### 9.3 Test Semantic Search

```bash
# Search documents
curl "http://localhost:8000/documents/search?q=quarterly%20revenue&limit=10"
```

### 9.4 Run Unit Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=api --cov-report=html
```

---

## 10. API Endpoints Reference

### Documents

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/documents/supported-types` | List supported file types |
| POST | `/documents/upload` | Upload and process document |
| GET | `/documents/search` | Semantic search |
| GET | `/documents/search/hybrid` | Hybrid search |
| GET | `/documents/{id}` | Get document metadata |
| GET | `/documents/{id}/chunks` | Get document chunks |
| GET | `/documents/{id}/context` | Get formatted context for LLM |
| DELETE | `/documents/{id}` | Delete document |
| GET | `/documents/` | List documents |

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat` | Send message with context |
| POST | `/chat/stream` | Streaming response |

### General

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root/welcome |
| GET | `/health` | Health check |
| GET | `/version` | Version info |

---

## Quick Start Checklist

```bash
# 1. Install system dependencies
sudo apt install postgresql libreoffice pandoc

# 2. Install pgvector
cd /tmp && git clone https://github.com/pgvector/pgvector.git
cd pgvector && make && sudo make install

# 3. Create database
sudo -u postgres createuser redpajama -P
sudo -u postgres createdb redpajama_db -O redpajama
psql -U redpajama -d redpajama_db -c "CREATE EXTENSION vector;"

# 4. Clone project and setup Python
git clone <your-repo> red-pajama && cd red-pajama
python3.11 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 5. Configure environment
cp .env.example .env && nano .env

# 6. Run database migrations
for f in sql/*.sql; do psql -U redpajama -d redpajama_db -f "$f"; done

# 7. Start application
uvicorn api.main:app --reload

# 8. Test
curl http://localhost:8000/health
```

---

## Troubleshooting

### pgvector not found
```bash
# Ensure PostgreSQL dev headers are installed
sudo apt install postgresql-server-dev-all
cd /tmp/pgvector && make clean && make && sudo make install
```

### Embedding model download fails
```bash
# Pre-download the model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

### LibreOffice conversion fails
```bash
# Install full LibreOffice
sudo apt install libreoffice
# Test conversion
soffice --headless --convert-to docx test.doc
```

### Database connection refused
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql
# Check pg_hba.conf allows connections
sudo nano /etc/postgresql/15/main/pg_hba.conf
```

---

## Next Steps

1. **Add Authentication**: Implement JWT-based auth in `api/routers/auth.py`
2. **Add S3 Storage**: Configure `api/services/storage/s3_service.py`
3. **Add LLM Integration**: Set up OpenAI/Claude in `api/services/llm/`
4. **Add Cerbos Authorization**: Configure policies in `config/cerbos/`
5. **Deploy**: Set up CI/CD and production infrastructure

---

*Red Pajama - Document Intelligence Platform*
