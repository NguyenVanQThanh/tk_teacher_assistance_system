"""
File Name: 2ecce316b47f_add_status_replace_is_deleted.py
Description: add_status_replace_is_deleted
Created At: 2026-07-26 13:13:22.498158
Created By: Tam Khang
Updated At: 2026-07-26 13:13:22.498158
Updated By: Tam Khang

Revision ID: 2ecce316b47f
Revises: 'bbeb46cbf81e'
Create Date: 2026-07-26 13:13:22.498158
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2ecce316b47f'
down_revision: Union[str, Sequence[str], None] = 'bbeb46cbf81e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add status column with default 'ACTIVE'
    op.add_column('classes', sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False))
    op.add_column('subjects', sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False))
    op.add_column('student_class', sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False))
    op.add_column('teacher_subjects', sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False))

    # 2. Migrate existing data based on is_deleted
    op.execute("UPDATE classes SET status = 'DELETED' WHERE is_deleted = true")
    op.execute("UPDATE subjects SET status = 'DELETED' WHERE is_deleted = true")
    op.execute("UPDATE student_class SET status = 'DELETED' WHERE is_deleted = true")
    op.execute("UPDATE teacher_subjects SET status = 'DELETED' WHERE is_deleted = true")

    # 3. Drop is_deleted columns
    op.drop_column('classes', 'is_deleted')
    op.drop_column('subjects', 'is_deleted')
    op.drop_column('student_class', 'is_deleted')
    op.drop_column('teacher_subjects', 'is_deleted')


def downgrade() -> None:
    op.add_column('teacher_subjects', sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('student_class', sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('subjects', sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('classes', sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False))

    op.execute("UPDATE classes SET is_deleted = true WHERE status = 'DELETED'")
    op.execute("UPDATE subjects SET is_deleted = true WHERE status = 'DELETED'")
    op.execute("UPDATE student_class SET is_deleted = true WHERE status = 'DELETED'")
    op.execute("UPDATE teacher_subjects SET is_deleted = true WHERE status = 'DELETED'")

    op.drop_column('teacher_subjects', 'status')
    op.drop_column('student_class', 'status')
    op.drop_column('subjects', 'status')
    op.drop_column('classes', 'status')

