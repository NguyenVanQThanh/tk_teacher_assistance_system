# File Name: seed_synced_teacher_data.py
# Description: Seed script synchronizing realistic 3-state grading attempts and 1-week teaching schedule timetable for teacher.
# Created At: 2026-10-25
# Created By: Tam Khang
# Updated At: 2026-10-25
# Updated By: Tam Khang

import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

backend_root = str(Path(__file__).resolve().parent.parent.parent)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from app.core.database import SessionLocal
from models.models import (
    User, Class, StudentClass, ClassAssignment, Exercise,
    StudentExerciseAttempt
)


def seed_synced_teacher_data():
    db = SessionLocal()
    try:
        # 1. Locate teacher (Thầy Nguyễn Văn A)
        teacher = db.query(User).filter(User.phone == "0999000002").first()
        if not teacher:
            teacher = db.query(User).filter(User.phone == "0912345678").first()
        if not teacher:
            print("Teacher user not found.")
            return

        class_12a1 = db.query(Class).filter(Class.class_name == "12A1", Class.status != "DELETED").first()
        if not class_12a1:
            print("Class 12A1 not found.")
            return

        # 2. Retrieve students
        enrollments = db.query(StudentClass).filter(
            StudentClass.class_id == class_12a1.class_id,
            StudentClass.status != "DELETED"
        ).all()
        students = [e.student for e in enrollments if e.student]
        if len(students) < 15:
            additional_students = db.query(User).filter(User.phone.like("09991%")).limit(20).all()
            for s in additional_students:
                if s not in students:
                    db.add(StudentClass(
                        student_id=s.user_id,
                        class_id=class_12a1.class_id,
                        student_code=f"HS12{str(s.user_id)[:4]}",
                        status="ACTIVE"
                    ))
                    students.append(s)
            db.flush()

        print(f"Total active students available: {len(students)}")

        # 3. Retrieve or create assignments for class 12A1
        exercises = db.query(Exercise).filter(Exercise.status != "DELETED").limit(6).all()
        if not exercises:
            print("No exercises found in database.")
            return

        now = datetime.now(timezone.utc)
        assignments = []
        for ex in exercises:
            assign = db.query(ClassAssignment).filter(
                ClassAssignment.class_id == class_12a1.class_id,
                ClassAssignment.exercise_id == ex.exercise_id,
                ClassAssignment.status != "DELETED"
            ).first()
            if not assign:
                assign = ClassAssignment(
                    assignment_id=uuid.uuid4(),
                    class_id=class_12a1.class_id,
                    exercise_id=ex.exercise_id,
                    assigned_by=teacher.user_id,
                    assigned_at=now - timedelta(days=3),
                    due_at=now + timedelta(days=7),
                    status="ACTIVE"
                )
                db.add(assign)
                db.flush()
            assignments.append(assign)

        # 4. Synchronize 32 student exercise attempts with official 3-state grading lifecycle:
        # - 12 attempts: pending_grading (Chờ chấm: short answers/essays pending teacher evaluation)
        # - 8 attempts: pending_review (Chờ duyệt: system auto-graded, waiting for teacher approval)
        # - 12 attempts: approved (Đã duyệt: finalized and published)
        existing_attempts = db.query(StudentExerciseAttempt).join(
            ClassAssignment, StudentExerciseAttempt.assignment_id == ClassAssignment.assignment_id
        ).filter(
            ClassAssignment.class_id == class_12a1.class_id,
            StudentExerciseAttempt.status != "DELETED"
        ).all()

        target_total = 32
        plans = []

        # 12 Pending Grading (Chờ chấm)
        for i in range(12):
            plans.append({
                "status": "pending_grading",
                "score": None,
                "hours_ago": 1 + i * 2,
                "feedback": "",
                "pending_manual": True
            })

        # 8 Pending Review (Chờ duyệt)
        for i in range(8):
            plans.append({
                "status": "pending_review",
                "score": round(6.5 + (i * 0.4) % 3.5, 1),
                "hours_ago": 3 + i * 3,
                "feedback": "Hệ thống tự động chấm trắc nghiệm. Đang chờ giáo viên duyệt.",
                "pending_manual": False
            })

        # 12 Approved (Đã duyệt)
        for i in range(12):
            plans.append({
                "status": "approved",
                "score": round(7.0 + (i * 0.3) % 3.0, 1),
                "hours_ago": 12 + i * 4,
                "feedback": "Làm bài tốt, lập luận rõ ràng và hoàn thành đầy đủ các bước giải.",
                "pending_manual": False
            })

        updated_count = 0
        created_count = 0

        for idx, plan in enumerate(plans):
            student = students[idx % len(students)]
            assign = assignments[idx % len(assignments)]
            submit_time = now - timedelta(hours=plan["hours_ago"])

            # Mock detailed results with pending_manual_grade flag
            detailed_results = {
                "questions": [
                    {
                        "question_id": f"q-{idx}-1",
                        "question_type": "MultipleChoice",
                        "is_correct": True,
                        "pending_manual_grade": False
                    },
                    {
                        "question_id": f"q-{idx}-2",
                        "question_type": "ShortAnswer",
                        "is_correct": False if not plan["pending_manual"] else None,
                        "pending_manual_grade": plan["pending_manual"]
                    }
                ],
                "teacher_feedback": plan["feedback"]
            }

            if idx < len(existing_attempts):
                att = existing_attempts[idx]
                att.student_id = student.user_id
                att.assignment_id = assign.assignment_id
                att.status = plan["status"]
                att.score = plan["score"]
                att.is_finished = True
                att.start_time = submit_time - timedelta(minutes=45)
                att.end_time = submit_time
                att.total_time_seconds = 2700
                att.detailed_results = detailed_results
                updated_count += 1
            else:
                att = StudentExerciseAttempt(
                    attempt_id=uuid.uuid4(),
                    student_id=student.user_id,
                    assignment_id=assign.assignment_id,
                    start_time=submit_time - timedelta(minutes=45),
                    end_time=submit_time,
                    total_time_seconds=2700,
                    score=plan["score"],
                    detailed_results=detailed_results,
                    is_finished=True,
                    status=plan["status"]
                )
                db.add(att)
                created_count += 1

        db.commit()
        print(f"Attempts seeded successfully. Created: {created_count}, Updated: {updated_count}")

        # Verification count
        pending_g = db.query(StudentExerciseAttempt).filter(StudentExerciseAttempt.status == "pending_grading").count()
        pending_r = db.query(StudentExerciseAttempt).filter(StudentExerciseAttempt.status == "pending_review").count()
        approved_c = db.query(StudentExerciseAttempt).filter(StudentExerciseAttempt.status == "approved").count()
        print(f"Summary Verification -> Pending Grading: {pending_g}, Pending Review: {pending_r}, Approved: {approved_c}")

    except Exception as e:
        db.rollback()
        print(f"Seeding error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_synced_teacher_data()
