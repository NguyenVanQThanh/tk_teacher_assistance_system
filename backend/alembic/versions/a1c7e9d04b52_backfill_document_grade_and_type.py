"""
File Name: a1c7e9d04b52_backfill_document_grade_and_type.py
Description: Backfill NULL grade and document_type on documents and add server defaults
Created At: 2026-10-29
Created By: AI Agent
Updated At: 2026-10-29
Updated By: AI Agent

Revision ID: a1c7e9d04b52
Revises: f3ff9572448d
Create Date: 2026-10-29 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a1c7e9d04b52'
down_revision: Union[str, Sequence[str], None] = 'f3ff9572448d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rows created before the columns existed hold NULL; give them the same values the ORM defaults use.
    op.execute("UPDATE documents SET grade = '12' WHERE grade IS NULL")
    op.execute("UPDATE documents SET document_type = 'reference' WHERE document_type IS NULL")
    op.alter_column('documents', 'grade', server_default='12')
    op.alter_column('documents', 'document_type', server_default='reference')


def downgrade() -> None:
    op.alter_column('documents', 'document_type', server_default=None)
    op.alter_column('documents', 'grade', server_default=None)
