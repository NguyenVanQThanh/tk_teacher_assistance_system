"""add image_metadata to questions

Revision ID: c4d8e2f1a3b9
Revises: 'a1c7e9d04b52'
Create Date: 2026-11-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4d8e2f1a3b9'
down_revision: Union[str, Sequence[str], None] = 'a1c7e9d04b52'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('questions', sa.Column('image_metadata', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('questions', 'image_metadata')
