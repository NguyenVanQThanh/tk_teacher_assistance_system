"""add ACAD_SUBJECT_HEAD_ASSIGN permission and grant it to Admin

Revision ID: b2d4f6a8c0e1
Revises: a1c3e5f7b9d2
Create Date: 2026-11-13 14:00:00

File Name: b2d4f6a8c0e1_add_acad_subject_head_assign_permission.py
Description: Seeds the permission that lets an Admin assign the head of a subject department
    and maps it to the Admin role. Idempotent.
Created At: 2026-11-13
Created By: AI Agent
Updated At: 2026-11-13
Updated By: AI Agent
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b2d4f6a8c0e1'
down_revision: Union[str, Sequence[str], None] = 'a1c3e5f7b9d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PERMISSION_CODE = "ACAD_SUBJECT_HEAD_ASSIGN"


def upgrade() -> None:
    op.execute(
        f"""
        INSERT INTO permissions (permission_id, permission_code, name, description, module)
        SELECT gen_random_uuid(), '{PERMISSION_CODE}', 'Assign Subject Head',
               'Allows Admin to assign the head of a subject department', 'academic'
        WHERE NOT EXISTS (SELECT 1 FROM permissions WHERE permission_code = '{PERMISSION_CODE}')
        """
    )
    op.execute(
        f"""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.role_id, p.permission_id
        FROM roles r, permissions p
        WHERE r.name = 'Admin' AND p.permission_code = '{PERMISSION_CODE}'
          AND NOT EXISTS (
              SELECT 1 FROM role_permissions rp
              WHERE rp.role_id = r.role_id AND rp.permission_id = p.permission_id)
        """
    )


def downgrade() -> None:
    op.execute(
        f"DELETE FROM role_permissions WHERE permission_id IN "
        f"(SELECT permission_id FROM permissions WHERE permission_code = '{PERMISSION_CODE}')"
    )
    op.execute(f"DELETE FROM permissions WHERE permission_code = '{PERMISSION_CODE}'")
