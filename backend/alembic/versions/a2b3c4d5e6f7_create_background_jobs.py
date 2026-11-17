"""create background_jobs queue table

Revision ID: a2b3c4d5e6f7
Revises: d1e2f3a4b5c6
Create Date: 2026-11-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a2b3c4d5e6f7'
down_revision: Union[str, Sequence[str], None] = 'd1e2f3a4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'background_jobs',
        sa.Column('job_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('kind', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='QUEUED'),
        sa.Column('progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('stage', sa.String(50), nullable=True),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('payload', postgresql.JSONB(), nullable=False),
        sa.Column('result', postgresql.JSONB(), nullable=True),
        sa.Column('error', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('QUEUED', 'RUNNING', 'DONE', 'FAILED')", name='chk_background_job_status'),
    )
    op.create_index('ix_background_jobs_status_created', 'background_jobs', ['status', 'created_at'])
    op.create_index('ix_background_jobs_user_created', 'background_jobs', ['user_id', 'created_at'])


def downgrade() -> None:
    op.drop_index('ix_background_jobs_user_created', table_name='background_jobs')
    op.drop_index('ix_background_jobs_status_created', table_name='background_jobs')
    op.drop_table('background_jobs')
