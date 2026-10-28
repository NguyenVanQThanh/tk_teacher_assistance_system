# File Name: seed_remaining_class_students.py
# Description: Seed script ensuring all classes in the database have enrolled students and assigned homeroom teachers.
# Created At: 2026-10-28
# Created By: Tam Khang
# Updated At: 2026-10-28
# Updated By: Tam Khang

import os
import sys
import uuid
from pathlib import Path
from datetime import date

backend_root = str(Path(__file__).resolve().parent.parent.parent)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from app.core.database import SessionLocal
from models.models import User, Role, Class, StudentClass
from app.core.security import get_password_hash

SAMPLE_NAMES_11 = [
    "Nguyễn Thị Hương", "Lê Quốc Trung", "Trần Văn Minh", "Phạm Thị Thu",
    "Hoàng Văn Nam", "Đỗ Thị Lan", "Bùi Đức Thắng", "Vũ Thị Mai",
    "Đặng Hoàng Việt", "Ngô Thị Hạnh", "Lý Gia Huy", "Trương Mỹ Linh",
    "Phan Tấn Tài", "Dương Minh Trí", "Hồ Bích Ngọc", "Lâm Thanh Tùng",
    "Võ Hoài Nam", "Đoàn Mỹ Duyên", "Chu Thế Anh", "Đinh Phương Thảo"
]

SAMPLE_NAMES_12 = [
    "Trần Hoàng Bách", "Nguyễn Thùy Dung", "Lê Thanh Sơn", "Phạm Hải Đăng",
    "Vũ Diệu Linh", "Đỗ Nhật Minh", "Bùi Quỳnh Nga", "Hoàng Tuấn Kiệt",
    "Đặng Khánh Huyền", "Ngô Bảo Châu", "Lý Minh Quân", "Trương Thảo Nhi",
    "Phan Quốc Đạt", "Dương Thu Trang", "Hồ Đức Phúc", "Lâm Ngọc Hân",
    "Võ Trường Giang", "Đoàn Thiên Ân", "Chu Đình Trọng", "Đinh Gia Khiêm"
]

def seed_remaining_students():
    db = SessionLocal()
    try:
        role_student = db.query(Role).filter(Role.name == "Student").first()
        if not role_student:
            print("Role Student not found.")
            return

        classes = db.query(Class).filter(Class.status != "DELETED").all()
        print(f"Total active classes: {len(classes)}")

        # Fetch available teachers for homeroom assignment
        role_teacher = db.query(Role).filter(Role.name == "Teacher").first()
        teachers = db.query(User).filter(User.role_id == role_teacher.role_id, User.status == "ACTIVE").all()
        teacher_map = {t.email: t for t in teachers}

        for cls in classes:
            student_count = db.query(StudentClass).filter(
                StudentClass.class_id == cls.class_id,
                StudentClass.status != "DELETED"
            ).count()

            print(f"Checking class: {cls.class_name} (year: {cls.academic_year}) - Current students: {student_count}")

            # Assign homeroom teacher if missing
            if not cls.homeroom_teacher_id and teachers:
                if "11" in cls.class_name and "teacher_trang@school.com" in teacher_map:
                    cls.homeroom_teacher_id = teacher_map["teacher_trang@school.com"].user_id
                elif "12" in cls.class_name and "teacher_long@school.com" in teacher_map:
                    cls.homeroom_teacher_id = teacher_map["teacher_long@school.com"].user_id
                else:
                    cls.homeroom_teacher_id = teachers[0].user_id
                db.commit()
                print(f"Assigned homeroom teacher for {cls.class_name}: {cls.homeroom_teacher_id}")

            if student_count < 15:
                needed = 20 - student_count
                print(f"Seeding {needed} students for {cls.class_name}...")
                name_list = SAMPLE_NAMES_11 if "11" in cls.class_name else SAMPLE_NAMES_12

                for i in range(needed):
                    code_num = student_count + i + 1
                    student_code = f"HS{cls.class_name}_{code_num:03d}"
                    phone = f"09992{abs(hash(cls.class_name + str(code_num))) % 1000000:06d}"
                    email = f"student_{cls.class_name.lower()}_{code_num:02d}@school.com"
                    full_name = name_list[i % len(name_list)]

                    existing_user = db.query(User).filter((User.phone == phone) | (User.email == email)).first()
                    if not existing_user:
                        student_user = User(
                            user_id=uuid.uuid4(),
                            phone=phone,
                            email=email,
                            password_hash=get_password_hash("Student@1234"),
                            full_name=full_name,
                            birthday=date(2008, (code_num % 12) + 1, (code_num % 28) + 1),
                            role_id=role_student.role_id,
                            status="ACTIVE"
                        )
                        db.add(student_user)
                        db.flush()
                    else:
                        student_user = existing_user

                    # Enroll in class
                    enrollment = db.query(StudentClass).filter(
                        StudentClass.student_id == student_user.user_id,
                        StudentClass.class_id == cls.class_id
                    ).first()

                    if not enrollment:
                        enrollment = StudentClass(
                            student_id=student_user.user_id,
                            class_id=cls.class_id,
                            student_code=student_code,
                            status="ACTIVE"
                        )
                        db.add(enrollment)
                    else:
                        enrollment.status = "ACTIVE"
                        enrollment.student_code = student_code

                db.commit()
                final_count = db.query(StudentClass).filter(
                    StudentClass.class_id == cls.class_id,
                    StudentClass.status != "DELETED"
                ).count()
                print(f"Successfully seeded students for {cls.class_name}. New count: {final_count}")

        print("Finished seeding students for all classes.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_remaining_students()
