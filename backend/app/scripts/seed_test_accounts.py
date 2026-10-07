# File Name: seed_test_accounts.py
# Description: Script to generate and ensure all test accounts (Teacher, Student, Admin) with proper roles, classes, and credentials.
# Created At: 2026-10-07
# Created By: Tam Khang
# Updated At: 2026-10-07
# Updated By: Tam Khang

import os
import sys
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

# Ensure UTF-8 output encoding on Windows console
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

backend_root = str(Path(__file__).resolve().parent.parent.parent)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

os.environ["DB_PASSWORD"] = "dummy_password"
from dotenv import load_dotenv
load_dotenv()

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from models.models import (
    User, Role, Class, Subject, TeacherSubject, StudentClass,
    ClassAssignment, Exercise
)


def seed_test_accounts():
    db = SessionLocal()
    try:
        # 1. Fetch Roles
        roles_dict = {r.name: r.role_id for r in db.query(Role).all()}
        teacher_role_id = roles_dict.get("Teacher")
        student_role_id = roles_dict.get("Student")
        admin_role_id = roles_dict.get("Admin")

        if not teacher_role_id or not student_role_id or not admin_role_id:
            print("Required roles missing from database!")
            return

        # 2. Define standard test accounts
        test_accounts = [
            # Teacher Accounts
            {
                "phone": "0999000002",
                "email": "teacher@school.com",
                "full_name": "Thầy Nguyễn Văn A (Giáo viên chính)",
                "role_id": teacher_role_id,
                "password_plain": "Teacher@1234",
                "role_name": "Teacher"
            },
            {
                "phone": "0988000001",
                "email": "teacher_auto_test@school.com",
                "full_name": "Thầy Automation Tester (Test tự động)",
                "role_id": teacher_role_id,
                "password_plain": "Teacher@1234",
                "role_name": "Teacher"
            },
            {
                "phone": "0999000004",
                "email": "teacher_an@school.com",
                "full_name": "Thầy Nguyễn Văn An (Bộ môn Toán)",
                "role_id": teacher_role_id,
                "password_plain": "Teacher@1234",
                "role_name": "Teacher"
            },
            {
                "phone": "0999000005",
                "email": "teacher_mai@school.com",
                "full_name": "Cô Trần Thị Mai (Bộ môn Vật lý)",
                "role_id": teacher_role_id,
                "password_plain": "Teacher@1234",
                "role_name": "Teacher"
            },
            {
                "phone": "0999000006",
                "email": "teacher_long@school.com",
                "full_name": "Thầy Lê Hoàng Long (Bộ môn Hóa học)",
                "role_id": teacher_role_id,
                "password_plain": "Teacher@1234",
                "role_name": "Teacher"
            },
            # Student Accounts
            {
                "phone": "0999100001",
                "email": "student_nam@school.com",
                "full_name": "Nguyễn Hoàng Nam",
                "role_id": student_role_id,
                "password_plain": "Student@1234",
                "role_name": "Student"
            },
            {
                "phone": "0999100002",
                "email": "student_mai_anh@school.com",
                "full_name": "Trần Thị Mai Anh",
                "role_id": student_role_id,
                "password_plain": "Student@1234",
                "role_name": "Student"
            },
            {
                "phone": "0999100003",
                "email": "student_duc@school.com",
                "full_name": "Lê Văn Đức",
                "role_id": student_role_id,
                "password_plain": "Student@1234",
                "role_name": "Student"
            },
            {
                "phone": "0999100004",
                "email": "student_tuan@school.com",
                "full_name": "Phạm Minh Tuấn",
                "role_id": student_role_id,
                "password_plain": "Student@1234",
                "role_name": "Student"
            },
            {
                "phone": "0999100005",
                "email": "student_thao@school.com",
                "full_name": "Đặng Thu Thảo",
                "role_id": student_role_id,
                "password_plain": "Student@1234",
                "role_name": "Student",
                "status": "ACTIVE"
            },
            {
                "phone": "0999100099",
                "email": "student_inactive@school.com",
                "full_name": "Học sinh Tạm khóa",
                "role_id": student_role_id,
                "password_plain": "Student@1234",
                "role_name": "Student",
                "status": "INACTIVE"
            },
            {
                "phone": "0999000098",
                "email": "teacher_test_target@school.com",
                "full_name": "Thầy Giáo Viên Thử Nghiệm",
                "role_id": teacher_role_id,
                "password_plain": "Teacher@1234",
                "role_name": "Teacher",
                "status": "ACTIVE"
            },
            # Admin Accounts
            {
                "phone": "0999000001",
                "email": "admin@school.com",
                "full_name": "Quản trị viên Hệ thống",
                "role_id": admin_role_id,
                "password_plain": "Admin@1234",
                "role_name": "Admin",
                "status": "ACTIVE"
            },
            {
                "phone": "0999000099",
                "email": "admin_test@school.com",
                "full_name": "Quản trị viên Dự phòng",
                "role_id": admin_role_id,
                "password_plain": "Admin@1234",
                "role_name": "Admin",
                "status": "ACTIVE"
            }
        ]

        created_users = []
        for acc in test_accounts:
            user = db.query(User).filter(
                (User.phone == acc["phone"]) | (User.email == acc["email"])
            ).first()

            pw_hash = get_password_hash(acc["password_plain"])
            acc_status = acc.get("status", "ACTIVE")
            if user:
                user.password_hash = pw_hash
                user.role_id = acc["role_id"]
                user.full_name = acc["full_name"]
                user.status = acc_status
                print(f"[OK] Updated account: {acc['phone']} ({acc['full_name']})")
                created_users.append(user)
            else:
                user = User(
                    user_id=uuid.uuid4(),
                    phone=acc["phone"],
                    email=acc["email"],
                    password_hash=pw_hash,
                    full_name=acc["full_name"],
                    role_id=acc["role_id"],
                    status=acc_status
                )
                db.add(user)
                db.flush()
                print(f"[CREATED] New test account: {acc['phone']} ({acc['full_name']})")
                created_users.append(user)

        # 3. Associate Teachers with Class 12A1
        class_12a1 = db.query(Class).filter(Class.class_name == "12A1", Class.status != "DELETED").first()
        subj_math = db.query(Subject).filter(Subject.subject_name.ilike("%Toán%")).first()

        teacher_main = db.query(User).filter(User.phone == "0999000002").first()
        teacher_test = db.query(User).filter(User.phone == "0988000001").first()

        if class_12a1:
            if teacher_main and not class_12a1.homeroom_teacher_id:
                class_12a1.homeroom_teacher_id = teacher_main.user_id

            for t in [teacher_main, teacher_test]:
                if not t:
                    continue
                if subj_math:
                    exist_assign = db.query(TeacherSubject).filter(
                        TeacherSubject.class_id == class_12a1.class_id,
                        TeacherSubject.teacher_id == t.user_id,
                        TeacherSubject.subject_id == subj_math.subject_id
                    ).first()
                    if not exist_assign:
                        db.add(TeacherSubject(
                            class_id=class_12a1.class_id,
                            teacher_id=t.user_id,
                            subject_id=subj_math.subject_id,
                            status="ACTIVE"
                        ))
                        print(f"[ASSIGNED] Teacher {t.full_name} assigned to Class 12A1 ({subj_math.subject_name})")

        db.commit()
        print("\nAll test accounts successfully generated and verified!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding test accounts: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    seed_test_accounts()
