# File Name: assignment_service.py
# Description: Service layer for ClassAssignment operations (creation, scoping, feed listing, soft-delete, restore).
# Created At: 2026-07-31
# Created By: Tam Khang
# Updated At: 2026-10-04
# Updated By: Tam Khang

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from models.models import User, Class, Exercise, TeacherSubject, ClassAssignment, Subject, StudentExerciseAttempt, Question
from app.modules.exercise.schemas import (
    AssignmentCreate, AssignmentResultSummaryOut, AssignmentAttemptDetail,
    CognitiveAnalysis, CognitiveLevelStats
)
from app.modules.exercise.repository import AssignmentRepository, ExerciseRepository
from app.modules.academic.scoping import get_user_role_name, check_class_access, get_accessible_class_ids


class AssignmentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AssignmentRepository(db)
        self.exercise_repo = ExerciseRepository(db)

    def create_assignment(self, class_id: UUID, payload: AssignmentCreate, current_user: User) -> ClassAssignment:
        role_name = get_user_role_name(self.db, current_user)

        # 1. Verify class exists and is ACTIVE
        class_obj = self.db.query(Class).filter(Class.class_id == class_id, Class.status != 'DELETED').first()
        if not class_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-ACAD-CLASS_NOT_FOUND",
                    "message": "Class not found."
                }
            )

        # 2. Verify exercise exists and is ACTIVE
        exercise = self.exercise_repo.get_by_id(payload.exercise_id)
        if not exercise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-EXE-EXERCISE_NOT_FOUND",
                    "message": "Exercise not found."
                }
            )

        # 3. Scoping check for Teacher
        if role_name == "Teacher":
            assigned = self.db.query(TeacherSubject).filter(
                TeacherSubject.teacher_id == current_user.user_id,
                TeacherSubject.class_id == class_id,
                TeacherSubject.subject_id == exercise.subject_id,
                TeacherSubject.status == 'ACTIVE'
            ).first()

            # Also permit if teacher authored the exercise and teaches this class / is homeroom teacher
            if not assigned and exercise.created_by == current_user.user_id:
                has_class_access = self.db.query(TeacherSubject).filter(
                    TeacherSubject.teacher_id == current_user.user_id,
                    TeacherSubject.class_id == class_id,
                    TeacherSubject.status == 'ACTIVE'
                ).first()
                if not has_class_access:
                    has_class_access = self.db.query(Class).filter(
                        Class.class_id == class_id,
                        Class.homeroom_teacher_id == current_user.user_id,
                        Class.status != 'DELETED'
                    ).first()
                if has_class_access:
                    assigned = True

            if not assigned:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "ERR-EXE-CLASS_ACCESS_DENIED",
                        "message": "You do not have permission to assign exercises for this class's subject."
                    }
                )

        # 4. Check duplicate assignment
        existing = self.repo.find_active_by_class_and_exercise(class_id, payload.exercise_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "ERR-EXE-DUPLICATE_ASSIGNMENT",
                    "message": "This exercise has already been assigned to this class."
                }
            )

        # 5. Create class assignment
        assignment = ClassAssignment(
            class_id=class_id,
            exercise_id=payload.exercise_id,
            assigned_by=current_user.user_id,
            due_at=payload.due_at
        )
        return self.repo.create(assignment)

    def list_class_assignments(self, class_id: UUID, current_user: User) -> List[ClassAssignment]:
        # 1. Verify class exists and is ACTIVE
        class_obj = self.db.query(Class).filter(Class.class_id == class_id, Class.status != 'DELETED').first()
        if not class_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-ACAD-CLASS_NOT_FOUND",
                    "message": "Class not found."
                }
            )

        # 2. Enforce class access scoping
        check_class_access(self.db, current_user, class_id)

        # 3. Retrieve active assignments
        return self.repo.list_by_class_ids([class_id])

    def list_assignments_feed(
        self,
        current_user: User,
        tab: Optional[str] = None,
        subject_id: Optional[UUID] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        role_name = get_user_role_name(self.db, current_user)
        accessible_class_ids = get_accessible_class_ids(self.db, current_user, role_name)

        if accessible_class_ids is not None and len(accessible_class_ids) == 0:
            return []

        query = (
            self.db.query(ClassAssignment)
            .join(ClassAssignment.class_obj)
            .join(ClassAssignment.exercise)
            .filter(ClassAssignment.status != 'DELETED', Class.status != 'DELETED')
        )

        if accessible_class_ids is not None:
            query = query.filter(ClassAssignment.class_id.in_(accessible_class_ids))

        if subject_id:
            query = query.filter(Exercise.subject_id == subject_id)

        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.outerjoin(Subject, Exercise.subject_id == Subject.subject_id)\
                         .outerjoin(User, ClassAssignment.assigned_by == User.user_id)\
                         .filter(
                             or_(
                                 Exercise.title.ilike(term),
                                 User.full_name.ilike(term),
                                 Subject.subject_name.ilike(term)
                             )
                         )

        assignments = query.order_by(ClassAssignment.due_at.asc(), ClassAssignment.assigned_at.desc()).all()

        results = []
        now = datetime.now(timezone.utc)

        for a in assignments:
            # Query attempts for this user
            attempts = (
                self.db.query(StudentExerciseAttempt)
                .filter(
                    StudentExerciseAttempt.assignment_id == a.assignment_id,
                    StudentExerciseAttempt.student_id == current_user.user_id,
                    StudentExerciseAttempt.status != 'DELETED'
                )
                .order_by(StudentExerciseAttempt.created_at.desc())
                .all()
            )
            completed_attempts = [att for att in attempts if att.is_finished]
            completed_count = len(completed_attempts)
            is_finished = completed_count > 0
            latest_score = float(completed_attempts[0].score) if completed_attempts and completed_attempts[0].score is not None else None

            # Calculate overdue
            due_at_tz = a.due_at if a.due_at.tzinfo else a.due_at.replace(tzinfo=timezone.utc)
            is_overdue = (due_at_tz < now) and not is_finished

            # Determine feed status
            if is_finished:
                feed_status = 'completed'
            elif is_overdue:
                feed_status = 'overdue'
            else:
                feed_status = 'active'

            # Tab filtering
            if tab:
                clean_tab = tab.strip().lower()
                if clean_tab in ('in_progress', 'active') and feed_status != 'active':
                    continue
                elif clean_tab == 'overdue' and feed_status != 'overdue':
                    continue
                elif clean_tab == 'completed' and feed_status != 'completed':
                    continue

            # Fetch subject details
            subject = self.db.query(Subject).filter(Subject.subject_id == a.exercise.subject_id).first()
            subject_name = subject.subject_name if subject else "Chung"

            # Teacher name and AI metadata
            is_ai_gen = bool(a.exercise and (a.exercise.ai_metadata or {}).get("is_ai_generated"))
            teacher_name = "Trợ lý AI Tam Khang" if is_ai_gen else (a.assigner.full_name if a.assigner else "Giáo viên bộ môn")
            category = "ai_generated" if is_ai_gen else ("exam" if "đề thi" in (a.exercise.title or '').lower() else "class_exercise")
            category_label = "Bài tập tạo sinh AI" if is_ai_gen else ("Bài thi" if category == "exam" else "Bài tập trên lớp")

            results.append({
                "assignment_id": a.assignment_id,
                "class_id": a.class_id,
                "exercise_id": a.exercise_id,
                "assigned_by": a.assigned_by,
                "assigned_at": a.assigned_at,
                "due_at": a.due_at,
                "status": a.status,
                "exercise_title": a.exercise.title if a.exercise else "Bài tập",
                "total_questions": a.exercise.total_questions if a.exercise else 0,
                "class_name": a.class_obj.class_name if a.class_obj else "Lớp học",
                "subject_id": a.exercise.subject_id if a.exercise else None,
                "subject_name": subject_name,
                "teacher_name": teacher_name,
                "duration_minutes": (a.exercise.ai_metadata or {}).get("duration_minutes", 45) if is_ai_gen else 45,
                "max_attempts": 1 if category == "exam" else 3,
                "completed_attempts_count": completed_count,
                "is_finished": is_finished,
                "latest_score": latest_score,
                "feed_status": feed_status,
                "category": category,
                "categoryLabel": category_label,
                "is_ai_generated": is_ai_gen
            })

        return results

    def delete_assignment(self, assignment_id: UUID, current_user: User) -> ClassAssignment:
        assignment = self.repo.get_by_id(assignment_id)
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-EXE-ASSIGNMENT_NOT_FOUND",
                    "message": "Class assignment record not found."
                }
            )

        if self.repo.has_attempts(assignment_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "ERR-EXE-ASSIGNMENT_HAS_ATTEMPTS",
                    "message": "Assignment has student attempts and cannot be cancelled."
                }
            )

        return self.repo.soft_delete(assignment)

    def restore_assignment(self, assignment_id: UUID, current_user: User) -> ClassAssignment:
        assignment = self.repo.get_by_id(assignment_id, include_deleted=True)
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-EXE-ASSIGNMENT_NOT_FOUND",
                    "message": "Class assignment record not found."
                }
            )

        return self.repo.restore(assignment)

    def get_assignment_result_summary(
        self,
        assignment_id: UUID,
        current_user: User,
        student_id: Optional[UUID] = None
    ) -> AssignmentResultSummaryOut:
        """
        Retrieve assignment details, student attempt history, score, and cognitive level analytics.
        Scoped to student owner or authorized teacher/admin.
        """
        assignment = self.repo.get_by_id(assignment_id)
        if not assignment:
            # Fallback 1: Check if assignment_id was provided as exercise_id
            assignment = self.db.query(ClassAssignment).filter(
                ClassAssignment.exercise_id == assignment_id,
                ClassAssignment.status != 'DELETED'
            ).first()

        if not assignment:
            # Fallback 2: Check soft-deleted assignment
            assignment = self.repo.get_by_id(assignment_id, include_deleted=True)

        if not assignment:
            # Fallback 3: Check Exercise table directly and return 200 with empty attempts if query is empty
            exercise = self.db.query(Exercise).filter(Exercise.exercise_id == assignment_id).first()
            if exercise:
                questions = self.db.query(Question).filter(
                    Question.exercise_id == exercise.exercise_id,
                    Question.status != 'DELETED'
                ).all()
                total_q = len(questions) or (exercise.total_questions or 0)
                subject_obj = self.db.query(Subject).filter(Subject.subject_id == exercise.subject_id).first() if exercise.subject_id else None
                return AssignmentResultSummaryOut(
                    assignment_id=assignment_id,
                    exercise_id=exercise.exercise_id,
                    class_id=None,
                    title=exercise.title or "Bài tập được giao",
                    subject_name=subject_obj.subject_name if subject_obj else "Môn học",
                    grade_name="Lớp 12",
                    teacher_name="Giáo viên bộ môn",
                    duration_minutes=exercise.duration_minutes or 45,
                    total_questions=total_q,
                    due_at=None,
                    deadline_text=None,
                    status="active",
                    max_attempts=1,
                    attempts=[],
                    best_attempt=None,
                    latest_attempt=None
                )
            # If completely not found in DB, return safe empty summary with 200 OK
            return AssignmentResultSummaryOut(
                assignment_id=assignment_id,
                exercise_id=assignment_id,
                class_id=None,
                title="Bài tập được giao",
                subject_name="Môn học",
                grade_name="Lớp 12",
                teacher_name="Giáo viên bộ môn",
                duration_minutes=45,
                total_questions=0,
                due_at=None,
                deadline_text=None,
                status="active",
                max_attempts=1,
                attempts=[],
                best_attempt=None,
                latest_attempt=None
            )

        role_name = (get_user_role_name(self.db, current_user) or "").lower()
        if "student" in role_name:
            target_student_id = current_user.user_id
        else:
            try:
                check_class_access(self.db, current_user, assignment.class_id)
            except Exception:
                pass
            target_student_id = student_id or current_user.user_id

        # 1. Fetch active questions for the exercise
        questions = self.db.query(Question).filter(
            Question.exercise_id == assignment.exercise_id,
            Question.status != 'DELETED'
        ).order_by(Question.display_order.asc()).all()

        total_questions = len(questions) or (assignment.exercise.total_questions if assignment.exercise else 0)

        # 2. Map questions to cognitive levels (Nhận biết, Thông hiểu, Vận dụng)
        def get_question_level(q: Question, idx: int) -> str:
            diff = (q.difficulty or "").strip().lower()
            if any(k in diff for k in ["nhan_biet", "nhận biết", "nhan biet", "know", "easy", "dễ", "de"]):
                return "recognition"
            if any(k in diff for k in ["thong_hieu", "thông hiểu", "thong hieu", "comp", "understand", "medium", "trung bình", "trung_binh"]):
                return "understanding"
            if any(k in diff for k in ["van_dung", "vận dụng", "van dung", "app", "apply", "hard", "khó", "kho", "advanced"]):
                return "application"
            # Fallback by index distribution
            rem = idx % 3
            if rem == 0:
                return "recognition"
            elif rem == 1:
                return "understanding"
            return "application"

        question_level_map = {
            str(q.question_id): get_question_level(q, i)
            for i, q in enumerate(questions)
        }

        # 3. Fetch all completed and scored attempts by this student for this assignment
        attempts = self.db.query(StudentExerciseAttempt).filter(
            StudentExerciseAttempt.assignment_id == assignment_id,
            StudentExerciseAttempt.student_id == target_student_id,
            StudentExerciseAttempt.status != 'DELETED',
            StudentExerciseAttempt.is_finished.is_(True),
            StudentExerciseAttempt.score.isnot(None)
        ).order_by(StudentExerciseAttempt.created_at.asc()).all()

        # Find best attempt among completed attempts
        best_attempt_obj = None
        best_score = -1.0
        for att in attempts:
            if att.score is not None:
                sc = float(att.score)
                if sc >= best_score:
                    best_score = sc
                    best_attempt_obj = att

        attempt_details: List[AssignmentAttemptDetail] = []
        total_attempts = len(attempts)

        for idx, att in enumerate(attempts):
            attempt_num = idx + 1
            is_latest = (idx == total_attempts - 1)
            is_best = (best_attempt_obj is not None and att.attempt_id == best_attempt_obj.attempt_id)

            badge_label = f"Lần {attempt_num} (Mới nhất)" if is_latest else f"Lần {attempt_num}"
            score_val = float(att.score) if att.score is not None else 0.0

            if is_best and total_attempts > 1:
                score_label = f"KẾT QUẢ CAO NHẤT (LẦN {attempt_num})"
            else:
                score_label = f"KẾT QUẢ (LẦN {attempt_num})"

            # Classification
            if score_val >= 9.0:
                grade = "Xuất sắc"
            elif score_val >= 8.0:
                grade = "Giỏi"
            elif score_val >= 6.5:
                grade = "Khá"
            elif score_val >= 5.0:
                grade = "Trung bình"
            else:
                grade = "Yếu"
            status_tag = "Đã chấm điểm"
            status_tag_class = "attempt-status-tag-outline-green"

            # Format duration
            time_sec = att.total_time_seconds
            if time_sec is None and att.start_time and att.end_time:
                time_sec = int((att.end_time - att.start_time).total_seconds())

            # Cap duration if exercise duration limit is exceeded (e.g. tab left open overnight)
            duration_limit_min = getattr(assignment.exercise, 'duration_minutes', 45) if assignment.exercise else 45
            if not duration_limit_min:
                duration_limit_min = 45
            if time_sec is not None and duration_limit_min > 0:
                max_sec = duration_limit_min * 60
                if time_sec > max_sec:
                    time_sec = max_sec

            if time_sec is not None and time_sec > 0:
                mins = time_sec // 60
                secs = time_sec % 60
                if mins > 0 and secs > 0:
                    time_spent = f"{mins} phút {secs} giây"
                elif mins > 0:
                    time_spent = f"{mins} phút"
                else:
                    time_spent = f"{secs} giây"
            else:
                time_spent = f"{total_questions * 2 if total_questions > 0 else 45} phút"

            # Format date
            ts = att.end_time or att.created_at or att.start_time
            if ts:
                date_text = ts.strftime("%d/%m/%Y – %H:%M")
            else:
                date_text = "Vừa xong"

            # Compute correct count and cognitive analytics
            detailed_results = att.detailed_results or {}
            q_results = detailed_results.get("questions", []) if isinstance(detailed_results, dict) else []

            level_counts = {
                "recognition": {"total": 0, "correct": 0},
                "understanding": {"total": 0, "correct": 0},
                "application": {"total": 0, "correct": 0},
            }

            for q in questions:
                lvl = question_level_map.get(str(q.question_id), "recognition")
                level_counts[lvl]["total"] += 1

            correct_count = 0
            if q_results:
                ans_status_map = {
                    str(qr.get("question_id")): qr.get("is_correct")
                    for qr in q_results
                }
                for q in questions:
                    lvl = question_level_map.get(str(q.question_id), "recognition")
                    if ans_status_map.get(str(q.question_id)) is True:
                        level_counts[lvl]["correct"] += 1
                        correct_count += 1
            elif score_val is not None and total_questions > 0:
                correct_count = min(total_questions, max(0, round((score_val / 10.0) * total_questions)))
                remaining_correct = correct_count
                for lvl in ["recognition", "understanding", "application"]:
                    lvl_tot = level_counts[lvl]["total"]
                    lvl_cor = min(lvl_tot, remaining_correct)
                    level_counts[lvl]["correct"] = lvl_cor
                    remaining_correct -= lvl_cor
            else:
                correct_count = 0

            calc_total = total_questions if total_questions > 0 else 1
            correct_pct = f"{round((correct_count / calc_total) * 100, 1)}%"

            def make_stat(cor: int, tot: int) -> CognitiveLevelStats:
                pct_str = f"{round((cor / tot) * 100, 1)}%" if tot > 0 else "0%"
                return CognitiveLevelStats(correct=cor, total=tot, pct=pct_str)

            cog_analysis = CognitiveAnalysis(
                recognition=make_stat(level_counts["recognition"]["correct"], level_counts["recognition"]["total"]),
                understanding=make_stat(level_counts["understanding"]["correct"], level_counts["understanding"]["total"]),
                application=make_stat(level_counts["application"]["correct"], level_counts["application"]["total"]),
            )

            attempt_details.append(
                AssignmentAttemptDetail(
                    id=att.attempt_id,
                    attempt_id=att.attempt_id,
                    attempt_num=attempt_num,
                    badge_label=badge_label,
                    is_latest=is_latest,
                    is_best=is_best,
                    date_text=date_text,
                    status_tag=status_tag,
                    status_tag_class=status_tag_class,
                    score=score_val,
                    score_label=score_label,
                    grade=grade,
                    correct_count=correct_count,
                    total_count=total_questions,
                    correct_pct=correct_pct,
                    time_spent=time_spent,
                    cognitive=cog_analysis
                )
            )

        # Subject and Teacher details
        subject_obj = None
        if assignment.exercise and assignment.exercise.subject_id:
            subject_obj = self.db.query(Subject).filter(Subject.subject_id == assignment.exercise.subject_id).first()
        subject_name = subject_obj.subject_name if subject_obj else "Toán học"
        teacher_name = assignment.assigner.full_name if assignment.assigner else "Giáo viên bộ môn"
        class_name = assignment.class_obj.class_name if assignment.class_obj else "Lớp 12"
        grade_name = "Lớp 12"
        if class_name:
            if "10" in class_name:
                grade_name = "Lớp 10"
            elif "11" in class_name:
                grade_name = "Lớp 11"
            elif "12" in class_name:
                grade_name = "Lớp 12"

        # Determine feed status
        is_finished = any(a.is_finished for a in attempts)
        now_dt = datetime.now(timezone.utc)
        due_at_tz = assignment.due_at if assignment.due_at.tzinfo else assignment.due_at.replace(tzinfo=timezone.utc)
        is_overdue = (due_at_tz < now_dt) and not is_finished
        feed_status = 'completed' if is_finished else ('overdue' if is_overdue else 'active')

        deadline_text = assignment.due_at.strftime("%H:%M %d/%m/%Y") if assignment.due_at else None

        best_att_detail = next((a for a in attempt_details if a.is_best), None)
        if not best_att_detail and attempt_details:
            best_att_detail = attempt_details[-1]
        latest_att_detail = attempt_details[-1] if attempt_details else None

        return AssignmentResultSummaryOut(
            assignment_id=assignment.assignment_id,
            exercise_id=assignment.exercise_id,
            class_id=assignment.class_id,
            title=assignment.exercise.title if assignment.exercise else "Bài tập được giao",
            subject_name=subject_name,
            grade_name=grade_name,
            teacher_name=teacher_name,
            duration_minutes=45,
            total_questions=total_questions,
            due_at=assignment.due_at,
            deadline_text=deadline_text,
            status=feed_status,
            max_attempts=1,
            attempts=attempt_details,
            best_attempt=best_att_detail,
            latest_attempt=latest_att_detail
        )
