-- Add the 'embedding' vector column to the document_chunks table.
-- This column was missing, causing PGRST204 errors on insert.
-- Uses text-embedding-3-small (1536 dimensions) to match the rest of the project.

-- 1. Ensure the pgvector extension is enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Add the embedding column
ALTER TABLE document_chunks
ADD COLUMN IF NOT EXISTS embedding VECTOR(1536);

-- 3. Create an index for fast similarity search
CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx ON document_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
