"""add pgvector RAG tables

File Name: b7e1f2a3c4d5_add_pgvector_rag_tables.py
Description: Enable pgvector; create chunks (SGK store), sgk_docs, document_chunks; add ingest columns to documents.
Created At: 2026-11-11
Created By: AI Agent
Updated At: 2026-11-11
Updated By: AI Agent

Revision ID: b7e1f2a3c4d5
Revises: e5f6a7b8c9d0
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'b7e1f2a3c4d5'
down_revision: Union[str, Sequence[str], None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    # gen_random_uuid() is built in on PG13+.

    # SGK textbook store, identical to RAG_SGK/sql/init.sql. Data loaded by app/scripts/load_sgk_rag.py.
    op.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id text PRIMARY KEY,
            doc_id text NOT NULL,
            page int NOT NULL,
            chuong text,
            bai text,
            modality text NOT NULL,
            content text NOT NULL,
            embedding vector(1024) NOT NULL,
            meta jsonb,
            tsv tsvector,
            created_at timestamptz DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS chunks_tsv_idx ON chunks USING gin(tsv)")
    op.execute("CREATE INDEX IF NOT EXISTS chunks_doc_id_idx ON chunks (doc_id)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw_idx ON chunks "
        "USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)"
    )

    op.execute("""
        CREATE TABLE IF NOT EXISTS sgk_docs (
            doc_id text PRIMARY KEY,
            grade int NOT NULL,
            subject_key text NOT NULL,
            title text NOT NULL,
            status text DEFAULT 'ACTIVE'
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS document_chunks (
            chunk_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            document_id uuid NOT NULL REFERENCES documents(document_id),
            page int,
            modality text NOT NULL,
            content text NOT NULL,
            embedding vector(1024) NOT NULL,
            meta jsonb,
            tsv tsvector,
            status text NOT NULL DEFAULT 'ACTIVE',
            created_at timestamptz DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS document_chunks_document_id_idx ON document_chunks (document_id)")
    op.execute("CREATE INDEX IF NOT EXISTS document_chunks_tsv_idx ON document_chunks USING gin(tsv)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS document_chunks_embedding_hnsw_idx ON document_chunks "
        "USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)"
    )

    op.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS ingest_status text DEFAULT 'PENDING'")
    op.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS ingest_error text")


def downgrade() -> None:
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS ingest_error")
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS ingest_status")
    op.execute("DROP TABLE IF EXISTS document_chunks")
    op.execute("DROP TABLE IF EXISTS sgk_docs")
    op.execute("DROP TABLE IF EXISTS chunks")
    # Extension is left installed on purpose (other objects may depend on it).
