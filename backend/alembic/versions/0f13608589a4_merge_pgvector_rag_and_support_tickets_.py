"""
File Name: 0f13608589a4_merge_pgvector_rag_and_support_tickets_.py
Description: merge pgvector rag and support tickets heads
Created At: 2026-11-11
Created By: AI Agent
Updated At: 2026-11-11
Updated By: AI Agent

Revision ID: 0f13608589a4
Revises: ('b7e1f2a3c4d5', 'e8f1a2b3c4d5')
Create Date: 2026-11-11 16:38:14.864076
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0f13608589a4'
down_revision: Union[str, Sequence[str], None] = ('b7e1f2a3c4d5', 'e8f1a2b3c4d5')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
