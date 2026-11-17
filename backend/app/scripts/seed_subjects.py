# File Name: seed_subjects.py
# Description: Idempotent seed of the core school subjects, run on every container start.
# Created At: 2026-11-17
# Created By: AI Agent
# Updated At: 2026-11-17
# Updated By: AI Agent
"""Insert missing core subjects. Existing rows (any status) are never modified or removed."""

import sys
from pathlib import Path

backend_root = str(Path(__file__).resolve().parent.parent.parent)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from sqlalchemy.orm import Session

from models.models import Subject

CORE_SUBJECTS = [
    ("Toán học", "Môn Toán học phổ thông nâng cao và cơ bản"),
    ("Vật lý", "Môn Vật lý phổ thông và thí nghiệm"),
    ("Hóa học", "Môn Hóa học vô cơ và hữu cơ"),
    ("Sinh học", "Môn Sinh học tế bào, di truyền và tiến hóa"),
    ("Lịch sử", "Môn Lịch sử Việt Nam và thế giới"),
    ("Tiếng Anh", "Môn Tiếng Anh học thuật và giao tiếp"),
    ("Ngữ văn", "Môn Ngữ văn và đọc hiểu tác phẩm"),
    ("Địa lí", "Môn Địa lí tự nhiên và kinh tế - xã hội"),
    ("Tin học", "Môn Tin học và khoa học máy tính"),
    ("Công nghệ", "Môn Công nghệ phổ thông"),
    ("Giáo dục kinh tế và pháp luật", "Môn Giáo dục kinh tế và pháp luật"),
]


def seed_subjects(session: Session) -> int:
    """Add subjects missing by name; return the number created. Caller commits."""
    existing = {name for (name,) in session.query(Subject.subject_name).all()}
    created = 0
    for name, desc in CORE_SUBJECTS:
        if name not in existing:
            session.add(Subject(subject_name=name, description=desc, status="ACTIVE"))
            created += 1
    session.flush()
    return created


def main() -> int:
    from app.core.database import SessionLocal

    session = SessionLocal()
    try:
        created = seed_subjects(session)
        session.commit()
    except Exception as exc:  # noqa: BLE001 - fail the deploy loudly on DB problems
        session.rollback()
        print(f"seed_subjects: ERROR - {exc}")
        return 1
    finally:
        session.close()
    print(f"seed_subjects: created {created} subject(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
