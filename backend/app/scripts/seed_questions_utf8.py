# File Name: seed_questions_utf8.py
# Description: Seed properly UTF-8 encoded questions and answer options for Bài tập tin and Tiếng Anh exercises, and link student attempt detailed_results.
# Created At: 2026-10-30
# Created By: Tam Khang
# Updated At: 2026-10-30
# Updated By: Tam Khang

import uuid
from app.core.database import SessionLocal
from models.models import Exercise, Question, AnswerOption, StudentExerciseAttempt, ClassAssignment

def run():
    db = SessionLocal()
    try:
        # 1. Exercise: Bài tập tin (60fa9f84-009f-4e88-b66e-bb2e6333d854)
        ex_tin = db.query(Exercise).filter(Exercise.exercise_id == '60fa9f84-009f-4e88-b66e-bb2e6333d854').first()
        if ex_tin:
            # Delete existing questions with corrupted text
            for q in list(ex_tin.questions):
                db.delete(q)
            db.commit()

            # Q1: Multiple Choice
            q1 = Question(
                question_id=uuid.uuid4(),
                exercise_id=ex_tin.exercise_id,
                content="Trong kiến trúc máy tính Von Neumann, thành phần nào chịu trách nhiệm thực hiện các phép tính số học và logic?",
                question_type="MultipleChoice",
                display_order=1,
                status="ACTIVE"
            )
            db.add(q1)
            db.flush()

            opt1_a = AnswerOption(question_id=q1.question_id, content="ALU (Arithmetic Logic Unit)", is_correct=True, display_order=1)
            opt1_b = AnswerOption(question_id=q1.question_id, content="CU (Control Unit)", is_correct=False, display_order=2)
            opt1_c = AnswerOption(question_id=q1.question_id, content="Register (Thanh ghi)", is_correct=False, display_order=3)
            opt1_d = AnswerOption(question_id=q1.question_id, content="Memory Unit (Bộ nhớ chính)", is_correct=False, display_order=4)
            db.add_all([opt1_a, opt1_b, opt1_c, opt1_d])
            db.flush()

            # Q2: True / False
            q2 = Question(
                question_id=uuid.uuid4(),
                exercise_id=ex_tin.exercise_id,
                content="Giao thức TCP (Transmission Control Protocol) là giao thức truyền dữ liệu tin cậy, có cơ chế xác nhận gói tin và kiểm soát lỗi trên mạng Internet. Đúng hay Sai?",
                question_type="TrueFalse",
                display_order=2,
                status="ACTIVE"
            )
            db.add(q2)
            db.flush()

            opt2_a = AnswerOption(question_id=q2.question_id, content="Đúng", is_correct=True, display_order=1)
            opt2_b = AnswerOption(question_id=q2.question_id, content="Sai", is_correct=False, display_order=2)
            db.add_all([opt2_a, opt2_b])
            db.flush()

            # Q3: Short Answer
            q3 = Question(
                question_id=uuid.uuid4(),
                exercise_id=ex_tin.exercise_id,
                content="Trong ngôn ngữ lập trình Python, từ khóa nào được dùng để bắt đầu định nghĩa một hàm?",
                question_type="ShortAnswer",
                correct_answer="def",
                display_order=3,
                status="ACTIVE"
            )
            db.add(q3)
            db.flush()

            print(f"Created 3 UTF-8 questions for Bài tập tin: {q1.question_id}, {q2.question_id}, {q3.question_id}")

            # Update all attempts for Bài tập tin
            attempts = db.query(StudentExerciseAttempt).join(ClassAssignment).filter(
                ClassAssignment.exercise_id == ex_tin.exercise_id
            ).all()

            for att in attempts:
                if att.status == "pending_grading":
                    att.detailed_results = {
                        "questions": [
                            {
                                "question_id": str(q1.question_id),
                                "question_type": "MultipleChoice",
                                "student_answer_option_id": str(opt1_a.option_id),
                                "is_correct": True,
                                "pending_manual_grade": False
                            },
                            {
                                "question_id": str(q2.question_id),
                                "question_type": "TrueFalse",
                                "student_answer_option_id": str(opt2_a.option_id),
                                "is_correct": True,
                                "pending_manual_grade": False
                            },
                            {
                                "question_id": str(q3.question_id),
                                "question_type": "ShortAnswer",
                                "student_answer_text": "def",
                                "is_correct": None,
                                "pending_manual_grade": True
                            }
                        ],
                        "teacher_feedback": ""
                    }
                elif att.status == "pending_review":
                    is_correct_q3 = (float(att.score or 0) >= 8.0)
                    att.detailed_results = {
                        "questions": [
                            {
                                "question_id": str(q1.question_id),
                                "question_type": "MultipleChoice",
                                "student_answer_option_id": str(opt1_a.option_id),
                                "is_correct": True,
                                "pending_manual_grade": False
                            },
                            {
                                "question_id": str(q2.question_id),
                                "question_type": "TrueFalse",
                                "student_answer_option_id": str(opt2_a.option_id),
                                "is_correct": True,
                                "pending_manual_grade": False
                            },
                            {
                                "question_id": str(q3.question_id),
                                "question_type": "ShortAnswer",
                                "student_answer_text": "def" if is_correct_q3 else "function",
                                "is_correct": is_correct_q3,
                                "pending_manual_grade": False
                            }
                        ],
                        "teacher_feedback": "Hệ thống tự động chấm trắc nghiệm. Đang chờ giáo viên duyệt."
                    }
                else: # approved
                    is_correct_q3 = (float(att.score or 0) >= 8.0)
                    att.detailed_results = {
                        "questions": [
                            {
                                "question_id": str(q1.question_id),
                                "question_type": "MultipleChoice",
                                "student_answer_option_id": str(opt1_a.option_id),
                                "is_correct": True,
                                "pending_manual_grade": False
                            },
                            {
                                "question_id": str(q2.question_id),
                                "question_type": "TrueFalse",
                                "student_answer_option_id": str(opt2_a.option_id if (float(att.score or 0) >= 7.5) else opt2_b.option_id),
                                "is_correct": (float(att.score or 0) >= 7.5),
                                "pending_manual_grade": False
                            },
                            {
                                "question_id": str(q3.question_id),
                                "question_type": "ShortAnswer",
                                "student_answer_text": "def" if is_correct_q3 else "func",
                                "is_correct": is_correct_q3,
                                "pending_manual_grade": False
                            }
                        ],
                        "teacher_feedback": "Làm bài tốt, nắm chắc kiến thức cơ bản về Tin học."
                    }
            db.commit()
            print(f"Updated detailed_results for {len(attempts)} attempts of Bài tập tin.")

        # 2. Exercise: Bài kiểm tra định kỳ 2026-2027 - Môn Tiếng Anh (d985798e-25ac-41b1-b4bb-7b91e09b88ab)
        ex_eng = db.query(Exercise).filter(Exercise.exercise_id == 'd985798e-25ac-41b1-b4bb-7b91e09b88ab').first()
        if ex_eng:
            for q in list(ex_eng.questions):
                db.delete(q)
            db.commit()

            # Q1: Multiple Choice
            eq1 = Question(
                question_id=uuid.uuid4(),
                exercise_id=ex_eng.exercise_id,
                content="Choose the word whose underlined part is pronounced differently from the others:",
                question_type="MultipleChoice",
                display_order=1,
                status="ACTIVE"
            )
            db.add(eq1)
            db.flush()

            eopt1_a = AnswerOption(question_id=eq1.question_id, content="achieved", is_correct=False, display_order=1)
            eopt1_b = AnswerOption(question_id=eq1.question_id, content="required", is_correct=False, display_order=2)
            eopt1_c = AnswerOption(question_id=eq1.question_id, content="managed", is_correct=False, display_order=3)
            eopt1_d = AnswerOption(question_id=eq1.question_id, content="practiced", is_correct=True, display_order=4)
            db.add_all([eopt1_a, eopt1_b, eopt1_c, eopt1_d])
            db.flush()

            # Q2: Multiple Choice
            eq2 = Question(
                question_id=uuid.uuid4(),
                exercise_id=ex_eng.exercise_id,
                content="If the weather _______ fine tomorrow, our class will go on a field trip in the national park.",
                question_type="MultipleChoice",
                display_order=2,
                status="ACTIVE"
            )
            db.add(eq2)
            db.flush()

            eopt2_a = AnswerOption(question_id=eq2.question_id, content="is", is_correct=True, display_order=1)
            eopt2_b = AnswerOption(question_id=eq2.question_id, content="will be", is_correct=False, display_order=2)
            eopt2_c = AnswerOption(question_id=eq2.question_id, content="was", is_correct=False, display_order=3)
            eopt2_d = AnswerOption(question_id=eq2.question_id, content="had been", is_correct=False, display_order=4)
            db.add_all([eopt2_a, eopt2_b, eopt2_c, eopt2_d])
            db.flush()

            # Q3: Short Answer
            eq3 = Question(
                question_id=uuid.uuid4(),
                exercise_id=ex_eng.exercise_id,
                content="Fill in the blank with the appropriate preposition: She has always been keen _______ learning foreign languages.",
                question_type="ShortAnswer",
                correct_answer="on",
                display_order=3,
                status="ACTIVE"
            )
            db.add(eq3)
            db.flush()

            print(f"Created 3 questions for Tiếng Anh: {eq1.question_id}, {eq2.question_id}, {eq3.question_id}")

            eng_attempts = db.query(StudentExerciseAttempt).join(ClassAssignment).filter(
                ClassAssignment.exercise_id == ex_eng.exercise_id
            ).all()

            for att in eng_attempts:
                is_high = float(att.score or 0) >= 8.0
                att.detailed_results = {
                    "questions": [
                        {
                            "question_id": str(eq1.question_id),
                            "question_type": "MultipleChoice",
                            "student_answer_option_id": str(eopt1_d.option_id),
                            "is_correct": True,
                            "pending_manual_grade": False
                        },
                        {
                            "question_id": str(eq2.question_id),
                            "question_type": "MultipleChoice",
                            "student_answer_option_id": str(eopt2_a.option_id),
                            "is_correct": True,
                            "pending_manual_grade": False
                        },
                        {
                            "question_id": str(eq3.question_id),
                            "question_type": "ShortAnswer",
                            "student_answer_text": "on" if is_high else "about",
                            "is_correct": is_high,
                            "pending_manual_grade": False
                        }
                    ],
                    "teacher_feedback": "Em hoàn thành bài thi tốt, ngữ pháp và phát âm vững."
                }
            db.commit()
            print(f"Updated detailed_results for {len(eng_attempts)} attempts of Tiếng Anh.")

    finally:
        db.close()

if __name__ == "__main__":
    run()
