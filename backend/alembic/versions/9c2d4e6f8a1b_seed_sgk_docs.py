"""
File Name: 9c2d4e6f8a1b_seed_sgk_docs.py
Description: Seed the 41 SGK textbook rows into sgk_docs so RAG retrieval works without the source PDFs.
Created At: 2026-11-12
Created By: AI Agent
Updated At: 2026-11-12
Updated By: AI Agent

Revision ID: 9c2d4e6f8a1b
Revises: 0f13608589a4
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '9c2d4e6f8a1b'
down_revision: Union[str, Sequence[str], None] = '0f13608589a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (doc_id, grade, subject_key, title). doc_id = sha1(relative PDF path)[:12], matches chunks.doc_id.
SGK_DOCS = [
    ('9cd1428ab1a2', 10, 'cong_nghe', 'Công nghệ 10 - Công nghệ trồng trọt'),
    ('324468985abf', 10, 'cong_nghe', 'Công nghệ 10 - Thiết kế và công nghệ'),
    ('f8574ed5a1bc', 10, 'gdktpl', 'Giáo dục Kinh tế và Pháp luật 10'),
    ('bc62a58ca7ce', 10, 'hoa_hoc', 'Hóa học 10'),
    ('fc74a709358d', 10, 'lich_su', 'Lịch sử 10'),
    ('ae0d4c223295', 10, 'ngu_van', 'Ngữ văn 10, tập hai'),
    ('ec782855baef', 10, 'ngu_van', 'Ngữ văn 10, tập một'),
    ('c0b622c334d2', 10, 'sinh_hoc', 'Sinh học 10'),
    ('a26b46f2e428', 10, 'tin_hoc', 'Tin học 10'),
    ('972a81194598', 10, 'tieng_anh', 'Tiếng Anh 10 - Global Sucess'),
    ('1cabf591b343', 10, 'toan', 'Toán 10, tập hai'),
    ('aa6fdafe6e83', 10, 'toan', 'Toán 10, tập một'),
    ('901b54fff833', 10, 'vat_li', 'Vật lí 10'),
    ('7b98cba9eece', 10, 'dia_li', 'Địa lí 10'),
    ('4fee83512c2a', 11, 'cong_nghe', 'Công nghệ 11 - Công nghệ chăn nuôi'),
    ('2a59fd1529c0', 11, 'cong_nghe', 'Công nghệ 11 - Công nghệ cơ khí'),
    ('9aadc607997d', 11, 'gdktpl', 'Giáo dục Kinh tế và Pháp luật 11'),
    ('f16206fddf4b', 11, 'hoa_hoc', 'Hóa học 11'),
    ('1267450fc50d', 11, 'lich_su', 'Lịch sử 11'),
    ('4281107c1c87', 11, 'ngu_van', 'Ngữ văn 11, tập hai'),
    ('8523db73a09d', 11, 'ngu_van', 'Ngữ văn 11, tập một'),
    ('ed9a20ee117b', 11, 'sinh_hoc', 'Sinh học 11'),
    ('e7060a759e3d', 11, 'tin_hoc', 'Tin học 11 - Định hướng khoa học máy tính'),
    ('aa608bd2882f', 11, 'tin_hoc', 'Tin học 11 - Định hướng tin học ứng dụng'),
    ('99619b48b534', 11, 'tieng_anh', 'Tiếng Anh 11 - Global Success'),
    ('ef84c7ef5f64', 11, 'toan', 'Toán 11, tập hai'),
    ('aed800ad41cc', 11, 'toan', 'Toán 11, tập một'),
    ('5411e12dae51', 11, 'vat_li', 'Vật lí 11'),
    ('9d2f0ae164bd', 11, 'dia_li', 'Địa lí 11'),
    ('963d00e8cf1e', 12, 'gdktpl', 'Giáo dục Kinh tế và Pháp luật 12'),
    ('2cf45f8b6b55', 12, 'hoa_hoc', 'Hóa học 12'),
    ('b5936f943434', 12, 'lich_su', 'Lịch sử 12'),
    ('7658f8440c78', 12, 'ngu_van', 'Ngữ văn 12, tập hai'),
    ('fae11a588ff7', 12, 'ngu_van', 'Ngữ văn 12, tập một'),
    ('65379bb6c9f2', 12, 'sinh_hoc', 'Sinh học 12'),
    ('8eebb432a635', 12, 'tin_hoc', 'Tin học 12 - Định hướng Khoa học máy tính'),
    ('bd7ac79e2435', 12, 'tin_hoc', 'Tin học 12 - Định hướng Tin học ứng dụng'),
    ('19c815c541ee', 12, 'tieng_anh', 'Tiếng Anh 12 - Global Success'),
    ('ee38d058b9f6', 12, 'toan', 'Toán 12, tập hai'),
    ('824ede47d2bb', 12, 'toan', 'Toán 12, tập một'),
    ('afa9e705174d', 12, 'dia_li', 'Địa lí 12'),
]


def upgrade() -> None:
    conn = op.get_bind()
    for doc_id, grade, key, title in SGK_DOCS:
        conn.execute(
            sa.text(
                "INSERT INTO sgk_docs (doc_id, grade, subject_key, title, status) "
                "VALUES (:d, :g, :k, :t, 'ACTIVE') ON CONFLICT (doc_id) DO NOTHING"
            ),
            {"d": doc_id, "g": grade, "k": key, "t": title},
        )


def downgrade() -> None:
    # Soft delete only: keep rows, mark inactive.
    ids = [d[0] for d in SGK_DOCS]
    op.get_bind().execute(
        sa.text("UPDATE sgk_docs SET status = 'DELETED' WHERE doc_id = ANY(:ids)"), {"ids": ids}
    )
