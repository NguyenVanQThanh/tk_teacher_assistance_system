"""seed subjects that have SGK data (Dia li, Tin hoc, Cong nghe, GDKTPL)

File Name: b3c4d5e6f7a8_seed_sgk_subjects.py
Description: Insert missing ACTIVE subjects so the AI exercise subject dropdown covers all SGK data.
Created At: 2026-11-17
Created By: AI Agent
Updated At: 2026-11-17
Updated By: AI Agent

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-11-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b3c4d5e6f7a8'
down_revision: Union[str, Sequence[str], None] = 'a2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SUBJECTS = [
    ("Địa lí", "Môn Địa lí tự nhiên và kinh tế - xã hội"),
    ("Tin học", "Môn Tin học và khoa học máy tính"),
    ("Công nghệ", "Môn Công nghệ phổ thông"),
    ("Giáo dục kinh tế và pháp luật", "Môn Giáo dục kinh tế và pháp luật"),
]


def upgrade() -> None:
    conn = op.get_bind()
    for name, desc in SUBJECTS:
        conn.execute(
            sa.text(
                "INSERT INTO subjects (subject_id, subject_name, description, status) "
                "VALUES (gen_random_uuid(), :n, :d, 'ACTIVE') "
                "ON CONFLICT (subject_name) DO NOTHING"
            ),
            {"n": name, "d": desc},
        )


def downgrade() -> None:
    # Soft delete only; keep subjects already referenced by exercises.
    conn = op.get_bind()
    for name, _ in SUBJECTS:
        conn.execute(
            sa.text(
                "UPDATE subjects SET status = 'DELETED' WHERE subject_name = :n "
                "AND NOT EXISTS (SELECT 1 FROM exercises e WHERE e.subject_id = subjects.subject_id)"
            ),
            {"n": name},
        )
