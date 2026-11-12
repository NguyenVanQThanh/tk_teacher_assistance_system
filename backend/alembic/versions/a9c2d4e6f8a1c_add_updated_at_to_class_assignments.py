"""
File Name: a9c2d4e6f8a1c_add_updated_at_to_class_assignments.py
Description: add updated_at to class_assignments so ORM updates (incl. soft delete/restore of
             assignments) are visible to the data-version sync endpoint (/api/v1/sync/version).
Created At: 2026-11-12
Created By: AI Agent

Revision ID: a9c2d4e6f8a1c
Revises: '9c2d4e6f8a1b'
Create Date: 2026-11-12 23:45:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9c2d4e6f8a1c'
down_revision: Union[str, Sequence[str], None] = '9c2d4e6f8a1b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'class_assignments',
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_column('class_assignments', 'updated_at')
