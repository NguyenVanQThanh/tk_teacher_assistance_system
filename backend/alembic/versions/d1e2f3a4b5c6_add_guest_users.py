"""add guest users and personal assignments without class

Revision ID: d1e2f3a4b5c6
Revises: c7a1d3e5f9b2
Create Date: 2026-11-15
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, Sequence[str], None] = 'c7a1d3e5f9b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('is_guest', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('users', sa.Column('guest_key_hash', sa.String(length=64), nullable=True))
    op.add_column('users', sa.Column('guest_ip', sa.String(length=45), nullable=True))
    op.create_unique_constraint('uq_users_guest_key_hash', 'users', ['guest_key_hash'])
    op.create_index('ix_users_guest_ip', 'users', ['guest_ip'])

    op.alter_column('class_assignments', 'class_id', existing_type=sa.UUID(), nullable=True)
    op.create_check_constraint(
        'chk_assignment_class_or_owner',
        'class_assignments',
        'class_id IS NOT NULL OR owner_student_id IS NOT NULL',
    )


def downgrade() -> None:
    # Personal assignments have no class; NOT NULL cannot hold them and hard delete is not allowed here.
    orphans = op.get_bind().execute(
        sa.text("SELECT count(*) FROM class_assignments WHERE class_id IS NULL")).scalar()
    if orphans:
        raise RuntimeError(
            f"Cannot downgrade: {orphans} personal assignment(s) have no class. Resolve them manually first.")
    op.drop_constraint('chk_assignment_class_or_owner', 'class_assignments', type_='check')
    op.alter_column('class_assignments', 'class_id', existing_type=sa.UUID(), nullable=False)
    op.drop_index('ix_users_guest_ip', table_name='users')
    op.drop_constraint('uq_users_guest_key_hash', 'users', type_='unique')
    op.drop_column('users', 'guest_ip')
    op.drop_column('users', 'guest_key_hash')
    op.drop_column('users', 'is_guest')
