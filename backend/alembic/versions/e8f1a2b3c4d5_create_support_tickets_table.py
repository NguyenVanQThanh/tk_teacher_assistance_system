"""create support_tickets table

Revision ID: e8f1a2b3c4d5
Revises: 'c4d8e2f1a3b9'
Create Date: 2026-11-10
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e8f1a2b3c4d5'
down_revision: Union[str, Sequence[str], None] = 'c4d8e2f1a3b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('support_tickets',
    sa.Column('ticket_id', sa.UUID(), nullable=False),
    sa.Column('full_name', sa.String(length=100), nullable=True),
    sa.Column('phone', sa.String(length=20), nullable=False),
    sa.Column('request_type', sa.String(length=30), nullable=False),
    sa.Column('message', sa.Text(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.CheckConstraint("request_type IN ('forgot_password', 'new_account')", name='chk_support_ticket_request_type'),
    sa.CheckConstraint("status IN ('PENDING', 'PROCESSED', 'DELETED')", name='chk_support_ticket_status'),
    sa.PrimaryKeyConstraint('ticket_id')
    )


def downgrade() -> None:
    op.drop_table('support_tickets')
