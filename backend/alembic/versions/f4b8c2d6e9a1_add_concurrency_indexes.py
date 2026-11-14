"""add concurrency indexes for the 30-user workload

Revision ID: f4b8c2d6e9a1
Revises: e7a9c1d3f5b2
Create Date: 2026-11-13 04:30:00

These indexes back the hot list/filter/detail queries used by the teacher and
student flows (exercise bank, assignment feed, taking paper, attempts). They are
additive only: no table/column changes, and ``IF NOT EXISTS`` keeps the migration
safe on databases where an equivalent index was created manually.

Note: ``users.phone`` already has a unique constraint in the model, which
creates an index on PostgreSQL. ``ix_users_phone`` is kept as an explicit,
predictable name for deployments where that constraint/index was dropped.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f4b8c2d6e9a1'
down_revision: Union[str, Sequence[str], None] = 'e7a9c1d3f5b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_INDEXES = (
    ("ix_questions_exercise_status", "questions", ["exercise_id", "status"]),
    ("ix_answer_options_question_id", "answer_options", ["question_id"]),
    (
        "ix_attempts_student_assignment_finished",
        "student_exercise_attempts",
        ["student_id", "assignment_id", "is_finished"],
    ),
    ("ix_class_assignments_class_status", "class_assignments", ["class_id", "status"]),
    ("ix_class_assignments_exercise_status", "class_assignments", ["exercise_id", "status"]),
    ("ix_student_class_student_class_status", "student_class", ["student_id", "class_id", "status"]),
    ("ix_users_phone", "users", ["phone"]),
    ("ix_exercises_subject_creator_status", "exercises", ["subject_id", "created_by", "status"]),
)


def upgrade() -> None:
    for name, table, columns in _INDEXES:
        op.create_index(name, table, columns, unique=False, if_not_exists=True)


def downgrade() -> None:
    for name, table, _columns in reversed(_INDEXES):
        op.drop_index(name, table_name=table, if_exists=True)
