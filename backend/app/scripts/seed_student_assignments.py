# File Name: seed_student_assignments.py
# Description: Seed realistic class assignments and attempts for Student role use cases.
# Created At: 2026-10-02
# Created By: Tam Khang
# Updated At: 2026-10-02
# Updated By: Tam Khang

import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

backend_root = str(Path(__file__).resolve().parent.parent.parent)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from dotenv import load_dotenv
load_dotenv()

from app.core.database import SessionLocal
from models.models import User, Class, ClassAssignment, Exercise, StudentExerciseAttempt, StudentClass

def seed_student_assignments():
    db = SessionLocal()
    try:
        # 1. Find class 12A1
        class_12a1 = db.query(Class).filter(Class.class_name == "12A1", Class.status != "DELETED").first()
        if not class_12a1:
            print("Class 12A1 not found!")
            return

        # 2. Find teacher for class 12A1
        teacher = db.query(User).filter(User.phone == "0999000002").first()
        if not teacher:
            teacher = db.query(User).filter(User.phone == "0912345678").first()
        if not teacher:
            print("Teacher not found!")
            return

        # 3. Find student Nguyen Hoang Nam
        student = db.query(User).filter(User.phone == "0999100001").first()
        if not student:
            print("Student Nguyen Hoang Nam not found!")
            return

        # Ensure student is enrolled in 12A1
        enrollment = db.query(StudentClass).filter(
            StudentClass.student_id == student.user_id,
            StudentClass.class_id == class_12a1.class_id
        ).first()
        if not enrollment:
            db.add(StudentClass(
                student_id=student.user_id,
                class_id=class_12a1.class_id,
                student_code="HS12001",
                status="ACTIVE"
            ))
            db.flush()

        # 4. Find exercises
        exercises = db.query(Exercise).filter(Exercise.status != "DELETED").all()
        if len(exercises) < 3:
            print("Not enough exercises found:", len(exercises))
            return

        ex_active = exercises[0]
        ex_overdue = exercises[1]
        ex_completed = exercises[2]

        now = datetime.now(timezone.utc)

        # Assignment 1: Active (Due in 5 days)
        assign_1 = db.query(ClassAssignment).filter(
            ClassAssignment.class_id == class_12a1.class_id,
            ClassAssignment.exercise_id == ex_active.exercise_id,
            ClassAssignment.status != "DELETED"
        ).first()
        if not assign_1:
            assign_1 = ClassAssignment(
                assignment_id=uuid.uuid4(),
                class_id=class_12a1.class_id,
                exercise_id=ex_active.exercise_id,
                assigned_by=teacher.user_id,
                assigned_at=now - timedelta(days=2),
                due_at=now + timedelta(days=5),
                status="ACTIVE"
            )
            db.add(assign_1)
            print("Created Active Assignment:", ex_active.title)

        # Assignment 2: Overdue (Due 2 days ago)
        assign_2 = db.query(ClassAssignment).filter(
            ClassAssignment.class_id == class_12a1.class_id,
            ClassAssignment.exercise_id == ex_overdue.exercise_id,
            ClassAssignment.status != "DELETED"
        ).first()
        if not assign_2:
            assign_2 = ClassAssignment(
                assignment_id=uuid.uuid4(),
                class_id=class_12a1.class_id,
                exercise_id=ex_overdue.exercise_id,
                assigned_by=teacher.user_id,
                assigned_at=now - timedelta(days=5),
                due_at=now - timedelta(days=2),
                status="ACTIVE"
            )
            db.add(assign_2)
            print("Created Overdue Assignment:", ex_overdue.title)

        # Assignment 3: Completed (Due in 3 days, but student completed it)
        assign_3 = db.query(ClassAssignment).filter(
            ClassAssignment.class_id == class_12a1.class_id,
            ClassAssignment.exercise_id == ex_completed.exercise_id,
            ClassAssignment.status != "DELETED"
        ).first()
        if not assign_3:
            assign_3 = ClassAssignment(
                assignment_id=uuid.uuid4(),
                class_id=class_12a1.class_id,
                exercise_id=ex_completed.exercise_id,
                assigned_by=teacher.user_id,
                assigned_at=now - timedelta(days=3),
                due_at=now + timedelta(days=3),
                status="ACTIVE"
            )
            db.add(assign_3)
            print("Created Completed Assignment:", ex_completed.title)

        db.flush()

        # Add completed attempt for assign_3
        attempt = db.query(StudentExerciseAttempt).filter(
            StudentExerciseAttempt.assignment_id == assign_3.assignment_id,
            StudentExerciseAttempt.student_id == student.user_id
        ).first()
        if not attempt:
            attempt = StudentExerciseAttempt(
                attempt_id=uuid.uuid4(),
                student_id=student.user_id,
                assignment_id=assign_3.assignment_id,
                start_time=now - timedelta(hours=2),
                end_time=now - timedelta(hours=1, minutes=15),
                total_time_seconds=2700,
                score=8.5,
                is_finished=True,
                status="ACTIVE"
            )
            db.add(attempt)
            print("Created Completed Attempt for student:", student.full_name)

        db.commit()
        print("Successfully seeded student assignments!")
    except Exception as e:
        db.rollback()
        print("Error seeding assignments:", e)
    finally:
        db.close()

if __name__ == "__main__":
    seed_student_assignments()
