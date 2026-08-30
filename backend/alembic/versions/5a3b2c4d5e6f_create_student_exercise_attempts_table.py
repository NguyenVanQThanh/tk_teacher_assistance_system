# File Name: 5a3b2c4d5e6f_create_student_exercise_attempts_table.py
# Description: Create student_exercise_attempts table for student submission tracking and grading.
# Created At: 2026-08-05
# Created By: Tam Khang
# Updated At: 2026-08-05
# Updated By: Tam Khang

"""create student_exercise_attempts table

Revision ID: 5a3b2c4d5e6f
Revises: 4a2b3c4d5e6f
Create Date: 2026-08-05
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '5a3b2c4d5e6f'
down_revision: Union[str, Sequence[str], None] = '4a2b3c4d5e6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'student_exercise_attempts',
        sa.Column('attempt_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('assignment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('class_assignments.assignment_id', ondelete='CASCADE'), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_time_seconds', sa.Integer(), nullable=True),
        sa.Column('score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('detailed_results', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_finished', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('student_exercise_attempts')
