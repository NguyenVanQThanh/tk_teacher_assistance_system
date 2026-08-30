"""
File Name: 6b4c3d2e1f0a_add_content_markdown_and_latex_to_questions.py
Description: Add content_markdown and content_latex columns to questions table
Created At: 2026-08-16
Created By: Tam Khang
Updated At: 2026-08-16
Updated By: Tam Khang

Revision ID: 6b4c3d2e1f0a
Revises: 275f1ab474b9
Create Date: 2026-08-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6b4c3d2e1f0a'
down_revision: Union[str, Sequence[str], None] = '275f1ab474b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('questions', sa.Column('content_markdown', sa.Text(), nullable=True))
    op.add_column('questions', sa.Column('content_latex', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('questions', 'content_latex')
    op.drop_column('questions', 'content_markdown')
