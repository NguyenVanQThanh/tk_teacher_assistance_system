# File Name: 4a2b3c4d5e6f_create_class_assignments_table.py
# Description: Create class_assignments table with status column for soft delete.
# Created At: 2026-07-31
# Created By: Tam Khang
# Updated At: 2026-07-31
# Updated By: Tam Khang

"""create class_assignments table

Revision ID: 4a2b3c4d5e6f
Revises: 3a1b2c4d5e6f
Create Date: 2026-07-31
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '4a2b3c4d5e6f'
down_revision: Union[str, Sequence[str], None] = '3a1b2c4d5e6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'class_assignments',
        sa.Column('assignment_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('class_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('classes.class_id', ondelete='CASCADE'), nullable=False),
        sa.Column('exercise_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('exercises.exercise_id', ondelete='CASCADE'), nullable=False),
        sa.Column('assigned_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('due_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
    )


def downgrade() -> None:
    op.drop_table('class_assignments')
