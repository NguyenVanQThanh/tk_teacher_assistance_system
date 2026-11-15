"""make users.phone NOT NULL

Revision ID: c3a5e7b9d1f2
Revises: b2d4f6a8c0e1
Create Date: 2026-11-15 10:00:00

Login is phone-based, so every user must have a phone number. Existing rows with a
NULL phone are NOT backfilled (no fake numbers): the upgrade aborts with a clear
message so an operator can supply real numbers or soft-delete those rows first.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'c3a5e7b9d1f2'
down_revision: Union[str, Sequence[str], None] = 'b2d4f6a8c0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    null_count = conn.execute(sa.text("SELECT count(*) FROM users WHERE phone IS NULL")).scalar()
    if null_count:
        raise RuntimeError(
            f"Cannot make users.phone NOT NULL: {null_count} user(s) have a NULL phone. "
            "Set a real phone for each (UPDATE users SET phone = ... WHERE phone IS NULL) "
            "and re-run the migration."
        )
    op.alter_column('users', 'phone', existing_type=sa.String(length=20), nullable=False)


def downgrade() -> None:
    op.alter_column('users', 'phone', existing_type=sa.String(length=20), nullable=True)
