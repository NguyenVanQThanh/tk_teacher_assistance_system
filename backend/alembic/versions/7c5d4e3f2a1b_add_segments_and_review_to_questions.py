"""
File Name: 7c5d4e3f2a1b_add_segments_and_review_to_questions.py
Description: Add segments, confidence_score, and needs_review columns to questions table
Created At: 2026-08-16
Created By: Tam Khang
Updated At: 2026-08-16
Updated By: Tam Khang

Revision ID: 7c5d4e3f2a1b
Revises: 6b4c3d2e1f0a
Create Date: 2026-08-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c5d4e3f2a1b'
down_revision: Union[str, Sequence[str], None] = '6b4c3d2e1f0a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('questions', sa.Column('segments', sa.JSON(), nullable=True))
    op.add_column('questions', sa.Column('confidence_score', sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column('questions', sa.Column('needs_review', sa.Boolean(), server_default='false', nullable=False))


def downgrade() -> None:
    op.drop_column('questions', 'needs_review')
    op.drop_column('questions', 'confidence_score')
    op.drop_column('questions', 'segments')
