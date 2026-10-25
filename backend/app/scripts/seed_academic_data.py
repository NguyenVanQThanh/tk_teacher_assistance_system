# File Name: seed_academic_data.py
# Description: Idempotent database seed script for academic subjects, classes, teachers, student accounts, and enrollments.
# Created At: 2026-09-01
# Created By: Tam Khang
# Updated At: 2026-09-01
# Updated By: Tam Khang

import os
import sys
import json
import uuid
from pathlib import Path

# Ensure UTF-8 output encoding on Windows console
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure backend root is in sys.path
backend_root = str(Path(__file__).resolve().parent.parent.parent)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

load_dotenv()

from models.models import User, Role, Subject, Class, StudentClass, TeacherSubject
from app.core.security import get_password_hash

DB_USERNAME = os.environ.get("DB_USERNAME")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME")

if not all([DB_USERNAME, DB_PASSWORD, DB_NAME]):
    raise ValueError("Missing database configuration in environment variables")

DATABASE_URL = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def seed_academic_sample_data():
    session = SessionLocal()
    accounts_info = []

    try:
        print("--- [1] Checking and fetching Roles ---")
        role_teacher = session.query(Role).filter(Role.name == "Teacher").first()
        role_student = session.query(Role).filter(Role.name == "Student").first()
        role_admin = session.query(Role).filter(Role.name == "Admin").first()

        if not role_teacher or not role_student:
            raise ValueError("Role Teacher or Student not found in database. Run seed.py first.")

        # Existing admin and sample teacher accounts
        admin_user = session.query(User).filter(User.phone == "0999000001").first()
        if admin_user:
            accounts_info.append({
                "user_id": str(admin_user.user_id),
                "phone": admin_user.phone,
                "email": admin_user.email,
                "full_name": admin_user.full_name,
                "role_name": "Admin",
                "password_plain": "Admin@1234"
            })

        print("--- [2] Seeding Subjects ---")
        subjects_data = [
            {"name": "Toán học", "desc": "Môn Toán học phổ thông nâng cao và cơ bản"},
            {"name": "Vật lý", "desc": "Môn Vật lý phổ thông và thí nghiệm"},
            {"name": "Hóa học", "desc": "Môn Hóa học vô cơ và hữu cơ"},
            {"name": "Tiếng Anh", "desc": "Môn Tiếng Anh học thuật và giao tiếp"},
            {"name": "Ngữ văn", "desc": "Môn Ngữ văn và đọc hiểu tác phẩm"}
        ]
        subjects_dict = {}
        for s_info in subjects_data:
            subj = session.query(Subject).filter(Subject.subject_name == s_info["name"]).first()
            if not subj:
                subj = Subject(
                    subject_id=uuid.uuid4(),
                    subject_name=s_info["name"],
                    description=s_info["desc"],
                    status="ACTIVE"
                )
                session.add(subj)
                session.flush()
                print(f"Created Subject: {subj.subject_name}")
            subjects_dict[s_info["name"]] = subj

        session.commit()

        print("--- [3] Seeding Teachers (5 Teachers) ---")
        teachers_data = [
            {
                "phone": "0999000002",
                "email": "teacher@school.com",
                "full_name": "Sample Teacher (Thầy Nguyễn Văn A)",
                "password": "Teacher@1234"
            },
            {
                "phone": "0999000004",
                "email": "teacher_an@school.com",
                "full_name": "Thầy Nguyễn Văn An",
                "password": "Teacher@1234"
            },
            {
                "phone": "0999000005",
                "email": "teacher_mai@school.com",
                "full_name": "Cô Trần Thị Mai",
                "password": "Teacher@1234"
            },
            {
                "phone": "0999000006",
                "email": "teacher_long@school.com",
                "full_name": "Thầy Lê Hoàng Long",
                "password": "Teacher@1234"
            },
            {
                "phone": "0999000007",
                "email": "teacher_trang@school.com",
                "full_name": "Cô Phạm Thu Trang",
                "password": "Teacher@1234"
            }
        ]
        teachers_dict = {}
        for t_info in teachers_data:
            t_user = session.query(User).filter(User.phone == t_info["phone"]).first()
            if not t_user:
                t_user = User(
                    user_id=uuid.uuid4(),
                    phone=t_info["phone"],
                    email=t_info["email"],
                    password_hash=get_password_hash(t_info["password"]),
                    full_name=t_info["full_name"],
                    role_id=role_teacher.role_id,
                    status="ACTIVE"
                )
                session.add(t_user)
                session.flush()
                print(f"Created Teacher: {t_user.full_name} ({t_user.phone})")
            else:
                # Update password hash to ensure consistency
                t_user.password_hash = get_password_hash(t_info["password"])
                t_user.full_name = t_info["full_name"]
                session.flush()

            teachers_dict[t_info["phone"]] = t_user
            accounts_info.append({
                "user_id": str(t_user.user_id),
                "phone": t_user.phone,
                "email": t_user.email,
                "full_name": t_user.full_name,
                "role_name": "Teacher",
                "password_plain": t_info["password"]
            })

        session.commit()

        print("--- [4] Seeding Classes (3 Classes) ---")
        # 12A1: Homeroom is Sample Teacher (0999000002)
        # 11B2: Homeroom is Thầy An (0999000004)
        # 10A3: Homeroom is Cô Mai (0999000005)
        classes_data = [
            {
                "name": "12A1",
                "school_year": "2023-2024",
                "homeroom_phone": "0999000002"
            },
            {
                "name": "11B2",
                "school_year": "2023-2024",
                "homeroom_phone": "0999000004"
            },
            {
                "name": "10A3",
                "school_year": "2023-2024",
                "homeroom_phone": "0999000005"
            }
        ]
        classes_dict = {}
        for c_info in classes_data:
            cls = session.query(Class).filter(Class.class_name == c_info["name"], Class.status != "DELETED").first()
            homeroom_user = teachers_dict[c_info["homeroom_phone"]]
            if not cls:
                cls = Class(
                    class_id=uuid.uuid4(),
                    class_name=c_info["name"],
                    academic_year=c_info["school_year"],
                    homeroom_teacher_id=homeroom_user.user_id,
                    status="ACTIVE"
                )
                session.add(cls)
                session.flush()
                print(f"Created Class: {cls.class_name} (GVCN: {homeroom_user.full_name})")
            else:
                cls.homeroom_teacher_id = homeroom_user.user_id
                cls.academic_year = c_info["school_year"]
                cls.status = "ACTIVE"
                session.flush()
            classes_dict[c_info["name"]] = cls

        session.commit()

        print("--- [5] Seeding Teacher-Subject Assignments ---")
        assignments_plan = [
            ("0999000004", "11B2", "Vật lý"),
            ("0999000004", "12A1", "Vật lý"),
            ("0999000005", "10A3", "Hóa học"),
            ("0999000005", "11B2", "Hóa học"),
            ("0999000006", "12A1", "Tiếng Anh"),
            ("0999000006", "11B2", "Tiếng Anh"),
            ("0999000007", "12A1", "Ngữ văn"),
            ("0999000007", "10A3", "Ngữ văn"),
        ]
        for t_phone, c_name, s_name in assignments_plan:
            teacher = teachers_dict[t_phone]
            class_obj = classes_dict[c_name]
            subject = subjects_dict[s_name]

            ts = session.query(TeacherSubject).filter(
                TeacherSubject.teacher_id == teacher.user_id,
                TeacherSubject.class_id == class_obj.class_id,
                TeacherSubject.subject_id == subject.subject_id
            ).first()
            if not ts:
                ts = TeacherSubject(
                    teacher_id=teacher.user_id,
                    class_id=class_obj.class_id,
                    subject_id=subject.subject_id,
                    status="ACTIVE"
                )
                session.add(ts)
                print(f"Assigned {teacher.full_name} -> {s_name} at {c_name}")

        session.commit()

        print("--- [6] Seeding Students (55 Students) ---")
        student_names = [
            # 12A1 (20 students)
            "Nguyễn Hoàng Nam", "Trần Thị Mai Anh", "Lê Văn Đức", "Phạm Minh Tuấn",
            "Đặng Thu Thảo", "Vũ Hoàng Long", "Bùi Phương Linh", "Hoàng Quốc Bảo",
            "Đỗ Thị Kim Oanh", "Phan Gia Huy", "Ngô Thành Đạt", "Lý Thanh Thảo",
            "Trương Tấn Sang", "Dương Ngọc Ánh", "Hồ Minh Quân", "Lâm Quốc Cường",
            "Võ Thị Tuyết", "Đoàn Văn Hậu", "Chu Quang Khải", "Đinh Bích Phương",
            # 11B2 (18 students)
            "Nguyễn Anh Dũng", "Phạm Thúy Hằng", "Lê Hoàng Yến", "Trần Đình Trọng",
            "Bùi Tiến Dũng", "Nguyễn Công Phượng", "Nguyễn Quang Hải", "Vũ Văn Thanh",
            "Lương Xuân Trường", "Phan Văn Đức", "Hà Đức Chinh", "Đỗ Duy Mạnh",
            "Nguyễn Tuấn Anh", "Nguyễn Phong Hồng Duy", "Bùi Hoàng Việt Anh",
            "Nguyễn Thanh Bình", "Nhâm Mạnh Dũng", "Khuất Văn Khang",
            # 10A3 (17 students)
            "Nguyễn Văn Toàn", "Phạm Tuấn Hải", "Hồ Tấn Tài", "Trần Nguyên Mạnh",
            "Đặng Văn Lâm", "Bùi Tấn Trường", "Nguyễn Đức Chiến", "Trương Văn Thái Quý",
            "Lê Văn Xuân", "Dụng Quang Nho", "Trần Danh Trung", "Mai Xuân Quyết",
            "Lê Minh Bình", "Nguyễn Hữu Thắng", "Trần Bảo Toàn", "Lê Xuân Tú",
            "Nguyễn Văn Tùng"
        ]

        class_distribution = (
            [("12A1", "HS12")] * 20 +
            [("11B2", "HS11")] * 18 +
            [("10A3", "HS10")] * 17
        )

        for idx, (name, (class_name, code_prefix)) in enumerate(zip(student_names, class_distribution), start=1):
            phone = f"099910{idx:04d}"
            email = f"student{idx:02d}@school.com"
            student_code = f"{code_prefix}{idx:03d}"

            student_user = session.query(User).filter(User.phone == phone).first()
            if not student_user:
                student_user = User(
                    user_id=uuid.uuid4(),
                    phone=phone,
                    email=email,
                    password_hash=get_password_hash("Student@1234"),
                    full_name=name,
                    role_id=role_student.role_id,
                    status="ACTIVE"
                )
                session.add(student_user)
                session.flush()
            else:
                student_user.full_name = name
                student_user.password_hash = get_password_hash("Student@1234")
                session.flush()

            accounts_info.append({
                "user_id": str(student_user.user_id),
                "phone": student_user.phone,
                "email": student_user.email,
                "full_name": student_user.full_name,
                "role_name": "Student",
                "student_code": student_code,
                "class_name": class_name,
                "password_plain": "Student@1234"
            })

            # Enroll into class
            target_class = classes_dict[class_name]
            enrollment = session.query(StudentClass).filter(
                StudentClass.student_id == student_user.user_id,
                StudentClass.class_id == target_class.class_id
            ).first()
            if not enrollment:
                enrollment = StudentClass(
                    student_id=student_user.user_id,
                    class_id=target_class.class_id,
                    student_code=student_code,
                    status="ACTIVE"
                )
                session.add(enrollment)

        session.commit()
        print("Successfully seeded 55 students and enrolled them into classes!")

        # Save to seed_accounts_info.json
        output_json_path = os.path.join(os.path.dirname(__file__), "seed_accounts_info.json")
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(accounts_info, f, ensure_ascii=False, indent=2)
        print(f"Updated account reference file: {output_json_path}")

        print("\nAll academic sample data has been seeded successfully!")

    except Exception as e:
        session.rollback()
        print(f"Error seeding academic data: {e}")
        raise e
    finally:
        session.close()


if __name__ == "__main__":
    seed_academic_sample_data()
