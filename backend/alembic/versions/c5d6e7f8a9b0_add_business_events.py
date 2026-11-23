"""
File Name: c5d6e7f8a9b0_add_business_events.py
Description: create business_events (AI generation / OCR outcomes) for all-time monitoring totals.
Created At: 2026-11-24
Created By: AI Agent

Revision ID: c5d6e7f8a9b0
Revises: b3c4d5e6f7a8
Create Date: 2026-11-24 10:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'c5d6e7f8a9b0'
down_revision: Union[str, Sequence[str], None] = 'b3c4d5e6f7a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'business_events',
        sa.Column('event_id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('kind', sa.String(length=32), nullable=False),
        sa.Column('ok', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_business_events_kind_created_at', 'business_events', ['kind', 'created_at'])


def downgrade() -> None:
    op.drop_index('ix_business_events_kind_created_at', table_name='business_events')
    op.drop_table('business_events')
