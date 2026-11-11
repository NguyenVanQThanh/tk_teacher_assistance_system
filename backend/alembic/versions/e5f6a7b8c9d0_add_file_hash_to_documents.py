"""
File Name: e5f6a7b8c9d0_add_file_hash_to_documents.py
Description: Add file_hash (SHA-256) to documents to reject duplicate uploads.
Created At: 2026-11-11
Created By: AI Agent
Updated At: 2026-11-11
Updated By: AI Agent

Revision ID: e5f6a7b8c9d0
Revises: c4d8e2f1a3b9
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'c4d8e2f1a3b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('documents', sa.Column('file_hash', sa.String(length=64), nullable=True))
    op.create_index('ix_documents_file_hash', 'documents', ['file_hash'])


def downgrade() -> None:
    op.drop_index('ix_documents_file_hash', table_name='documents')
    op.drop_column('documents', 'file_hash')
