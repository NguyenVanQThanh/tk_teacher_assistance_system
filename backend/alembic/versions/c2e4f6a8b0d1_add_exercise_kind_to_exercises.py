"""
File Name: c2e4f6a8b0d1_add_exercise_kind_to_exercises.py
Description: add exercises.exercise_kind (PRACTICE | EXAM) to replace guessing "exam" from the
             title. Existing exercises whose title contains "đề thi" are backfilled as EXAM.
Created At: 2026-11-13
Created By: AI Agent

Revision ID: c2e4f6a8b0d1
Revises: b1d3e5f7a9c2
Create Date: 2026-11-13 11:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c2e4f6a8b0d1'
down_revision: Union[str, Sequence[str], None] = 'b1d3e5f7a9c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'exercises',
        sa.Column('exercise_kind', sa.String(length=20), server_default='PRACTICE', nullable=False),
    )
    # Preserve current behaviour for existing data: titles containing "đề thi" were treated as exams.
    op.execute("UPDATE exercises SET exercise_kind = 'EXAM' WHERE LOWER(title) LIKE '%đề thi%'")


def downgrade() -> None:
    op.drop_column('exercises', 'exercise_kind')
