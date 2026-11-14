# File Name: seed_grading_data.py
# Description: Seed realistic student attempts and submissions for Teacher Grading and Feedback evaluation (Use Case 6).
# Created At: 2026-10-07
# Created By: Tam Khang
# Updated At: 2026-10-07
# Updated By: Tam Khang

import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

backend_root = str(Path(__file__).resolve().parent.parent.parent)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

os.environ["DB_PASSWORD"] = "dummy_password"
from dotenv import load_dotenv
load_dotenv()

from app.core.database import SessionLocal
from models.models import (
    User, Class, ClassAssignment, Exercise, StudentExerciseAttempt, StudentClass
)


def seed_grading_submissions():
    db = SessionLocal()
    try:
        # 1. Identify teacher and class 12A1
        teacher = db.query(User).filter(User.phone == "0999000002").first()
        if not teacher:
            teacher = db.query(User).filter(User.phone == "0912345678").first()
        if not teacher:
            print("Teacher not found!")
            return

        class_12a1 = db.query(Class).filter(Class.class_name == "12A1", Class.status != "DELETED").first()
        if not class_12a1:
            print("Class 12A1 not found!")
            return

        # 2. Get students in 12A1
        student_enrollments = db.query(StudentClass).filter(
            StudentClass.class_id == class_12a1.class_id,
            StudentClass.status == "ACTIVE"
        ).all()
        students = [se.student for se in student_enrollments if se.student]
        if len(students) < 10:
            print(f"Only {len(students)} students found in 12A1, fetching more...")
            all_students = db.query(User).filter(User.phone.like("09991%")).limit(12).all()
            for s in all_students:
                if not any(se.student_id == s.user_id for se in student_enrollments):
                    db.add(StudentClass(
                        student_id=s.user_id,
                        class_id=class_12a1.class_id,
                        student_code=f"HS12{str(s.user_id)[:4]}",
                        status="ACTIVE"
                    ))
                    students.append(s)
            db.flush()

        print(f"Loaded {len(students)} students for class 12A1.")

        # 3. Retrieve target exercises
        # Exercise with Part I (MCQ), Part II (TF), and Part III (ShortAnswer) -> Requires teacher grading
        ex_exam = db.query(Exercise).filter(
            Exercise.exercise_id == "3ad4c004-9616-4ee1-9b88-e281596bfa7b",
            Exercise.status == "ACTIVE"
        ).first()

        # Purely objective exercises (100% MCQ) -> Auto-graded by system
        ex_chem = db.query(Exercise).filter(
            Exercise.exercise_id == "20a10f39-5c81-402f-9a66-1f6d6a7b479d",
            Exercise.status == "ACTIVE"
        ).first()

        ex_math = db.query(Exercise).filter(
            Exercise.exercise_id == "56d035a0-1eff-4ef4-a5aa-65078e9bb260",
            Exercise.status == "ACTIVE"
        ).first()

        ex_phys = db.query(Exercise).filter(
            Exercise.exercise_id == "40258af0-41cd-43b6-81b5-f8ab7e710986",
            Exercise.status == "ACTIVE"
        ).first()

        now = datetime.now(timezone.utc)

        # 4. Ensure class assignments exist
        assignments_map = {}
        for ex, days_ago, days_ahead in [
            (ex_exam, 2, 5),
            (ex_chem, 3, 4),
            (ex_math, 2, 5),
            (ex_phys, 4, 3)
        ]:
            if not ex:
                continue
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
                    assigned_at=now - timedelta(days=days_ago),
                    due_at=now + timedelta(days=days_ahead),
                    status="ACTIVE"
                )
                db.add(assign)
                db.flush()
                print(f"Created ClassAssignment for {ex.title}")
            assignments_map[ex.exercise_id] = assign

        # Helper to construct detailed_results for an exercise
        def build_detailed_results(exercise, student_answers):
            res_list = []
            for q in exercise.questions:
                q_id = str(q.question_id)
                ans = student_answers.get(q_id, {})
                
                is_correct = ans.get("is_correct", False)
                opt_id = ans.get("option_id")
                ans_text = ans.get("text")
                pending = ans.get("pending_manual_grade", False)
                sub_results = ans.get("sub_results", {})

                res_list.append({
                    "question_id": q_id,
                    "question_type": q.question_type,
                    "student_answer_option_id": opt_id,
                    "student_answer_text": ans_text,
                    "is_correct": is_correct,
                    "pending_manual_grade": pending,
                    "sub_results": sub_results
                })
            return {"questions": res_list}

        # 5. Define answers for exercises
        # Answers for Chemistry:
        chem_correct_opts = {
            str(q.question_id): next((str(o.option_id) for o in q.answer_options if o.is_correct), None)
            for q in (ex_chem.questions if ex_chem else [])
        }
        chem_wrong_opts = {
            str(q.question_id): next((str(o.option_id) for o in q.answer_options if not o.is_correct), None)
            for q in (ex_chem.questions if ex_chem else [])
        }

        # Answers for Math:
        math_correct_opts = {
            str(q.question_id): next((str(o.option_id) for o in q.answer_options if o.is_correct), None)
            for q in (ex_math.questions if ex_math else [])
        }
        math_wrong_opts = {
            str(q.question_id): next((str(o.option_id) for o in q.answer_options if not o.is_correct), None)
            for q in (ex_math.questions if ex_math else [])
        }

        # Answers for Physics:
        phys_correct_opts = {
            str(q.question_id): next((str(o.option_id) for o in q.answer_options if o.is_correct), None)
            for q in (ex_phys.questions if ex_phys else [])
        }
        phys_wrong_opts = {
            str(q.question_id): next((str(o.option_id) for o in q.answer_options if not o.is_correct), None)
            for q in (ex_phys.questions if ex_phys else [])
        }

        # Answers builder for ĐỀ THI MINH HỌA - TOÁN 12 (Contains MCQ, TF, ShortAnswer)
        def build_exam_answers(short_answers_dict, mc_accuracy=0.8, tf_accuracy=0.75, short_pending=True):
            ans_map = {}
            if not ex_exam:
                return ans_map

            for idx, q in enumerate(ex_exam.questions):
                qid = str(q.question_id)
                if q.question_type == 'ShortAnswer':
                    st_val = short_answers_dict.get(qid, q.correct_answer or "5")
                    norm_student = str(st_val).strip().replace(',', '.')
                    norm_correct = str(q.correct_answer or "").strip().replace(',', '.')
                    is_correct = (norm_student == norm_correct) if (not short_pending and q.correct_answer) else None

                    ans_map[qid] = {
                        "text": st_val,
                        "is_correct": is_correct,
                        "pending_manual_grade": short_pending
                    }
                elif q.question_type == 'MultipleChoice':
                    corr_opt = next((str(o.option_id) for o in q.answer_options if o.is_correct), None)
                    wrong_opt = next((str(o.option_id) for o in q.answer_options if not o.is_correct), None)
                    is_corr = (idx % 10) < int(mc_accuracy * 10)
                    ans_map[qid] = {
                        "option_id": corr_opt if is_corr else wrong_opt,
                        "is_correct": is_corr,
                        "pending_manual_grade": False
                    }
                elif q.question_type == 'TrueFalse':
                    # Generate sub-results
                    sub_res = {
                        'a': True,
                        'b': (idx % 2 == 0),
                        'c': True,
                        'd': False
                    }
                    all_corr = all(sub_res.values())
                    ans_map[qid] = {
                        "text": "a:true;b:false;c:true;d:false",
                        "is_correct": all_corr,
                        "sub_results": sub_res,
                        "pending_manual_grade": False
                    }
            return ans_map

        # Map short answer questions for ex_exam
        exam_short_qids = [str(q.question_id) for q in (ex_exam.questions if ex_exam else []) if q.question_type == 'ShortAnswer']

        # 6. Create attempts plan
        # RULE:
        # - ONLY submissions with ShortAnswer (Part III) needing teacher review are in PENDING_GRADING (Chờ chấm)!
        # - Pure MCQ/TF submissions are 100% AUTO-GRADED and in APPROVED / GRADED status!
        attempts_plan = [
            # 1. ĐỀ THI MINH HỌA - TOÁN 12: PENDING GRADING (Đặng Thu Thảo)
            # Has Part III Short Answer questions -> Needs teacher grading!
            {
                "student_idx": 0,
                "exercise": ex_exam,
                "score": None, # Pending teacher grading!
                "time_offset_hours": 1,
                "feedback": "",
                "ans_builder": lambda: build_exam_answers({
                    exam_short_qids[0]: "12,7", # Student answer matching key
                    exam_short_qids[1]: "5",    # Student answer matching key
                    exam_short_qids[2]: "100",  # Student answer matching key
                    exam_short_qids[3]: "4"     # Student answer slightly off (key is 3)
                } if len(exam_short_qids) >= 4 else {}, mc_accuracy=0.85, tf_accuracy=0.75, short_pending=True)
            },
            # 2. ĐỀ THI MINH HỌA - TOÁN 12: PENDING GRADING (Trần Thị Mai Anh)
            {
                "student_idx": 1,
                "exercise": ex_exam,
                "score": None,
                "time_offset_hours": 3,
                "feedback": "",
                "ans_builder": lambda: build_exam_answers({
                    exam_short_qids[0]: "12,7",
                    exam_short_qids[1]: "8", # Wrong
                    exam_short_qids[2]: "90", # Wrong
                    exam_short_qids[3]: "3"
                } if len(exam_short_qids) >= 4 else {}, mc_accuracy=0.7, tf_accuracy=0.5, short_pending=True)
            },
            # 3. ĐỀ THI MINH HỌA - TOÁN 12: PENDING GRADING (Phạm Minh Tuấn)
            {
                "student_idx": 2,
                "exercise": ex_exam,
                "score": None,
                "time_offset_hours": 5,
                "feedback": "",
                "ans_builder": lambda: build_exam_answers({
                    exam_short_qids[0]: "15",
                    exam_short_qids[1]: "5",
                    exam_short_qids[2]: "100",
                    exam_short_qids[3]: "3"
                } if len(exam_short_qids) >= 4 else {}, mc_accuracy=0.9, tf_accuracy=1.0, short_pending=True)
            },
            # 4. ĐỀ THI MINH HỌA - TOÁN 12: PENDING GRADING (Vũ Hoàng Long) - Late submission yesterday
            {
                "student_idx": 3,
                "exercise": ex_exam,
                "score": None,
                "time_offset_hours": 25,
                "feedback": "",
                "ans_builder": lambda: build_exam_answers({
                    exam_short_qids[0]: "12.7",
                    exam_short_qids[1]: "5",
                    exam_short_qids[2]: "100",
                    exam_short_qids[3]: "3"
                } if len(exam_short_qids) >= 4 else {}, mc_accuracy=0.6, tf_accuracy=0.5, short_pending=True)
            },
            # 5. ĐỀ THI MINH HỌA - TOÁN 12: GRADED 9.0 (Lê Văn Đức) - Already graded by teacher
            {
                "student_idx": 4,
                "exercise": ex_exam,
                "score": 9.0,
                "time_offset_hours": 6,
                "feedback": "Làm bài rất tốt! Cả phần trắc nghiệm lẫn trả lời ngắn đều chính xác và logic.",
                "ans_builder": lambda: build_exam_answers({
                    exam_short_qids[0]: "12,7",
                    exam_short_qids[1]: "5",
                    exam_short_qids[2]: "100",
                    exam_short_qids[3]: "3"
                } if len(exam_short_qids) >= 4 else {}, mc_accuracy=1.0, tf_accuracy=1.0, short_pending=False)
            },
            # 6. Vật lý 12 (100% MCQ): GRADED 10.0 (Bùi Phương Linh) - AUTO-GRADED 100%
            {
                "student_idx": 5,
                "exercise": ex_phys,
                "score": 10.0,
                "time_offset_hours": 4,
                "feedback": "Hệ thống tự động chấm: Đúng 3/3 câu. Hiểu sâu bản chất sóng cơ và truyền âm.",
                "ans_builder": lambda: {
                    qid: {"option_id": phys_correct_opts.get(qid), "is_correct": True, "pending_manual_grade": False}
                    for qid in phys_correct_opts.keys()
                }
            },
            # 7. Vật lý 12 (100% MCQ): GRADED 6.7 (Đỗ Thị Kim Oanh) - AUTO-GRADED 100%
            {
                "student_idx": 6,
                "exercise": ex_phys,
                "score": 6.67,
                "time_offset_hours": 7,
                "feedback": "Hệ thống tự động chấm: Đúng 2/3 câu. Cần xem lại câu về tốc độ truyền sóng.",
                "ans_builder": lambda: {
                    qid: {
                        "option_id": phys_correct_opts.get(qid) if idx < 2 else phys_wrong_opts.get(qid),
                        "is_correct": (idx < 2),
                        "pending_manual_grade": False
                    }
                    for idx, qid in enumerate(phys_correct_opts.keys())
                }
            },
            # 8. Hóa học 12 (100% MCQ): GRADED 10.0 (Hoàng Quốc Bảo) - AUTO-GRADED 100%
            {
                "student_idx": 7,
                "exercise": ex_chem,
                "score": 10.0,
                "time_offset_hours": 8,
                "feedback": "Hệ thống tự động chấm: Đúng 3/3 câu. Nhớ vững công thức Este và phản ứng xà phòng hóa.",
                "ans_builder": lambda: {
                    qid: {"option_id": chem_correct_opts.get(qid), "is_correct": True, "pending_manual_grade": False}
                    for qid in chem_correct_opts.keys()
                }
            },
            # 9. Hóa học 12 (100% MCQ): GRADED 6.7 (Phan Gia Huy) - AUTO-GRADED 100%
            {
                "student_idx": 8,
                "exercise": ex_chem,
                "score": 6.67,
                "time_offset_hours": 26, # Yesterday
                "feedback": "Hệ thống tự động chấm: Đúng 2/3 câu.",
                "ans_builder": lambda: {
                    qid: {
                        "option_id": chem_correct_opts.get(qid) if idx < 2 else chem_wrong_opts.get(qid),
                        "is_correct": (idx < 2),
                        "pending_manual_grade": False
                    }
                    for idx, qid in enumerate(chem_correct_opts.keys())
                }
            },
            # 10. Toán 12 Đạo hàm (100% MCQ): GRADED 7.5 (Ngô Thành Đạt) - AUTO-GRADED 100%
            {
                "student_idx": 9,
                "exercise": ex_math,
                "score": 7.5,
                "time_offset_hours": 9,
                "feedback": "Hệ thống tự động chấm: Đúng 3/4 câu. Cần lưu ý dấu đạo hàm bậc hai.",
                "ans_builder": lambda: {
                    qid: {
                        "option_id": math_correct_opts.get(qid) if idx < 3 else math_wrong_opts.get(qid),
                        "is_correct": (idx < 3),
                        "pending_manual_grade": False
                    }
                    for idx, qid in enumerate(math_correct_opts.keys())
                }
            },
            # 11. Toán 12 Đạo hàm (100% MCQ): GRADED 5.0 (Nguyễn Văn Anh) - AUTO-GRADED 100%
            {
                "student_idx": 10 if len(students) > 10 else 0,
                "exercise": ex_math,
                "score": 5.0,
                "time_offset_hours": 28, # Yesterday
                "feedback": "Hệ thống tự động chấm: Đúng 2/4 câu.",
                "ans_builder": lambda: {
                    qid: {
                        "option_id": math_correct_opts.get(qid) if idx < 2 else math_wrong_opts.get(qid),
                        "is_correct": (idx < 2),
                        "pending_manual_grade": False
                    }
                    for idx, qid in enumerate(math_correct_opts.keys())
                }
            }
        ]

        created_count = 0
        updated_count = 0

        for plan in attempts_plan:
            student = students[plan["student_idx"] % len(students)]
            exercise = plan["exercise"]
            if not exercise or exercise.exercise_id not in assignments_map:
                continue

            assignment = assignments_map[exercise.exercise_id]
            submit_time = now - timedelta(hours=plan["time_offset_hours"])

            # Detailed results
            ans_dict = plan["ans_builder"]()
            detailed = build_detailed_results(exercise, ans_dict)
            if plan["feedback"]:
                detailed["teacher_feedback"] = plan["feedback"]

            # Check if this student already has an attempt for this assignment
            existing_attempt = db.query(StudentExerciseAttempt).filter(
                StudentExerciseAttempt.student_id == student.user_id,
                StudentExerciseAttempt.assignment_id == assignment.assignment_id,
                StudentExerciseAttempt.status != "DELETED"
            ).first()

            if existing_attempt:
                existing_attempt.score = plan["score"]
                existing_attempt.detailed_results = detailed
                existing_attempt.start_time = submit_time - timedelta(minutes=40)
                existing_attempt.end_time = submit_time
                existing_attempt.total_time_seconds = 2400
                existing_attempt.is_finished = True
                updated_count += 1
                print(f"Updated attempt for {student.full_name} -> {exercise.title[:35]} (Score: {plan['score']})")
            else:
                new_attempt = StudentExerciseAttempt(
                    attempt_id=uuid.uuid4(),
                    student_id=student.user_id,
                    assignment_id=assignment.assignment_id,
                    start_time=submit_time - timedelta(minutes=40),
                    end_time=submit_time,
                    total_time_seconds=2400,
                    score=plan["score"],
                    detailed_results=detailed,
                    is_finished=True,
                    status="ACTIVE"
                )
                db.add(new_attempt)
                created_count += 1
                print(f"Created attempt for {student.full_name} -> {exercise.title[:35]} (Score: {plan['score']})")

        db.commit()
        print(f"\nSuccessfully seeded attempts! Created: {created_count}, Updated: {updated_count}")

    except Exception as e:
        db.rollback()
        print(f"Error seeding grading data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    seed_grading_submissions()
