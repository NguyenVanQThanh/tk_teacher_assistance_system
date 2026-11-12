"""
File Name: e7a9c1d3f5b2_add_api_request_metrics.py
Description: create api_request_metrics for the realtime API monitoring module. Rows are written
             by a bounded in-process collector via a periodic bulk insert, then pruned by the
             hourly retention job (MONITORING_RETENTION_DAYS, default 7).
Created At: 2026-11-13
Created By: AI Agent

Revision ID: e7a9c1d3f5b2
Revises: c2e4f6a8b0d1
Create Date: 2026-11-13 04:15:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e7a9c1d3f5b2'
down_revision: Union[str, Sequence[str], None] = 'c2e4f6a8b0d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'api_request_metrics',
        sa.Column('metric_id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('request_id', sa.String(length=64), nullable=False),
        sa.Column('method', sa.String(length=10), nullable=False),
        sa.Column('route', sa.String(length=255), nullable=False),
        sa.Column('path', sa.String(length=512), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('duration_ms', sa.Float(), nullable=False, server_default='0'),
        sa.Column('request_bytes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('response_bytes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('user_ref', sa.String(length=64), nullable=False, server_default='anonymous'),
        sa.Column('ip_ref', sa.String(length=64), nullable=False, server_default='anonymous'),
        sa.Column('is_error', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_api_request_metrics_created_at', 'api_request_metrics', ['created_at'])
    op.create_index('ix_api_request_metrics_route', 'api_request_metrics', ['route'])
    op.create_index('ix_api_request_metrics_status_code', 'api_request_metrics', ['status_code'])


def downgrade() -> None:
    op.drop_index('ix_api_request_metrics_status_code', table_name='api_request_metrics')
    op.drop_index('ix_api_request_metrics_route', table_name='api_request_metrics')
    op.drop_index('ix_api_request_metrics_created_at', table_name='api_request_metrics')
    op.drop_table('api_request_metrics')
