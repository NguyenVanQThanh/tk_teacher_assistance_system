"""
File Name: b1d3e5f7a9c2_add_answers_released_at_to_class_assignments.py
Description: add nullable answers_released_at to class_assignments so teachers can reveal exam
             answers/results to students (NULL = hidden).
Created At: 2026-11-13
Created By: AI Agent

Revision ID: b1d3e5f7a9c2
Revises: a9c2d4e6f8a1c
Create Date: 2026-11-13 10:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b1d3e5f7a9c2'
down_revision: Union[str, Sequence[str], None] = 'a9c2d4e6f8a1c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('class_assignments', sa.Column('answers_released_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('class_assignments', 'answers_released_at')
