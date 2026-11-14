"""add subjects.head_teacher_id and class_assignments.owner_student_id

Revision ID: a1c3e5f7b9d2
Revises: f4b8c2d6e9a1
Create Date: 2026-11-13 10:00:00

File Name: a1c3e5f7b9d2_add_rbac_head_teacher_and_personal_assignments.py
Description: Adds the head-of-subject column, the personal-assignment owner column
    (with backfill for student-created assignments) and supporting RBAC indexes.
Created At: 2026-11-13
Created By: AI Agent
Updated At: 2026-11-13
Updated By: AI Agent
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1c3e5f7b9d2'
down_revision: Union[str, Sequence[str], None] = 'f4b8c2d6e9a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_INDEXES = (
    ("ix_documents_uploaded_by_status", "documents", ["uploaded_by", "status"]),
    ("ix_documents_subject_uploaded_by", "documents", ["subject_id", "uploaded_by"]),
    ("ix_teacher_subjects_class_subject_status", "teacher_subjects", ["class_id", "subject_id", "status"]),
    ("ix_subjects_head_teacher_id", "subjects", ["head_teacher_id"]),
    ("ix_class_assignments_owner_student_id", "class_assignments", ["owner_student_id"]),
)


def upgrade() -> None:
    op.add_column(
        'subjects',
        sa.Column('head_teacher_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        'fk_subjects_head_teacher_id_users', 'subjects', 'users',
        ['head_teacher_id'], ['user_id'], ondelete='SET NULL',
    )
    op.add_column(
        'class_assignments',
        sa.Column('owner_student_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        'fk_class_assignments_owner_student_id_users', 'class_assignments', 'users',
        ['owner_student_id'], ['user_id'], ondelete='SET NULL',
    )

    # Backfill: assignments created by a Student are personal to that student.
    op.execute(
        """
        UPDATE class_assignments
        SET owner_student_id = assigned_by
        WHERE assigned_by IN (
            SELECT u.user_id FROM users u JOIN roles r ON r.role_id = u.role_id
            WHERE lower(r.name) = 'student'
        )
        """
    )

    for name, table, columns in _INDEXES:
        op.create_index(name, table, columns, unique=False, if_not_exists=True)

    # The chunks table is created by the SGK loader, so it may not exist yet.
    if sa.inspect(op.get_bind()).has_table('chunks'):
        op.create_index('ix_chunks_doc_id_chuong', 'chunks', ['doc_id', 'chuong'], unique=False, if_not_exists=True)


def downgrade() -> None:
    op.drop_index('ix_chunks_doc_id_chuong', table_name='chunks', if_exists=True)
    for name, table, _columns in reversed(_INDEXES):
        op.drop_index(name, table_name=table, if_exists=True)
    op.drop_constraint('fk_class_assignments_owner_student_id_users', 'class_assignments', type_='foreignkey')
    op.drop_column('class_assignments', 'owner_student_id')
    op.drop_constraint('fk_subjects_head_teacher_id_users', 'subjects', type_='foreignkey')
    op.drop_column('subjects', 'head_teacher_id')
