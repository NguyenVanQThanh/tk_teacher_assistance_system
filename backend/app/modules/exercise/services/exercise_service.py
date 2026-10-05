# File Name: exercise_service.py
# Description: Service layer for Exercise management (scoping, CRUD, soft-delete, restore).
# Created At: 2026-07-31
# Created By: Tam Khang
# Updated At: 2026-10-03
# Updated By: Tam Khang

from typing import List, Optional, Dict, Any
from uuid import UUID
import uuid
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.models import User, Subject, TeacherSubject, Exercise, Question, AnswerOption, ClassAssignment, StudentClass, Class
from app.modules.exercise.schemas import ExerciseCreate, ExerciseUpdate, AiExerciseGenerateRequest, AiExerciseGenerateOut
from app.modules.exercise.repository import ExerciseRepository
from app.modules.academic.scoping import get_user_role_name
from app.modules.exercise.services.ai_generator_service import AiExerciseGeneratorService


class ExerciseService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ExerciseRepository(db)

    def _get_teacher_active_subject_ids(self, teacher_id: UUID) -> List[UUID]:
        assigned = self.db.query(TeacherSubject.subject_id).filter(
            TeacherSubject.teacher_id == teacher_id,
            TeacherSubject.status == 'ACTIVE'
        ).distinct().all()
        return [row[0] for row in assigned]

    def create_exercise(self, current_user: User, payload: ExerciseCreate) -> Exercise:
        role_name = get_user_role_name(self.db, current_user)
        
        # 1. Verify subject exists
        subject = self.db.query(Subject).filter(Subject.subject_id == payload.subject_id).first()
        if not subject or subject.status == 'DELETED':
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-EXE-SUBJECT_NOT_FOUND",
                    "message": "Subject not found."
                }
            )

        # 2. Scope check for Teacher
        if role_name == "Teacher":
            active_subject_ids = self._get_teacher_active_subject_ids(current_user.user_id)
            if payload.subject_id not in active_subject_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "ERR-EXE-INVALID_SUBJECT_SCOPE",
                        "message": "You do not have permission to create exercises for this subject."
                    }
                )

        # 3. Create exercise
        exercise = Exercise(
            title=payload.title,
            subject_id=payload.subject_id,
            created_by=current_user.user_id,
            total_questions=0,
            ai_metadata=payload.ai_metadata,
            status='ACTIVE'
        )
        return self.repo.create(exercise)

    def list_exercises(
        self,
        current_user: User,
        subject_id: Optional[UUID] = None,
        search: Optional[str] = None,
        cursor: Optional[str] = None,
        direction: str = "next",
        page_size: int = 6
    ) -> Dict[str, Any]:
        role_name = get_user_role_name(self.db, current_user)
        
        if role_name == "Admin":
            if subject_id:
                return self.repo.list_exercises(
                    subject_ids=[subject_id],
                    status='ACTIVE',
                    search=search,
                    cursor=cursor,
                    direction=direction,
                    page_size=page_size
                )
            return self.repo.list_exercises(
                status='ACTIVE',
                search=search,
                cursor=cursor,
                direction=direction,
                page_size=page_size
            )
        else:
            # For Teacher: restrict to created_by OR teacher_subjects
            active_subject_ids = self._get_teacher_active_subject_ids(current_user.user_id)
            if subject_id:
                if subject_id not in active_subject_ids:
                    # Can only see if created by self for that subject
                    return self.repo.list_exercises(
                        created_by=current_user.user_id,
                        subject_ids=[subject_id],
                        status='ACTIVE',
                        search=search,
                        cursor=cursor,
                        direction=direction,
                        page_size=page_size
                    )
                return self.repo.list_exercises(
                    subject_ids=[subject_id],
                    status='ACTIVE',
                    search=search,
                    cursor=cursor,
                    direction=direction,
                    page_size=page_size
                )

            return self.repo.list_exercises(
                created_by=current_user.user_id,
                subject_ids=active_subject_ids,
                status='ACTIVE',
                search=search,
                cursor=cursor,
                direction=direction,
                page_size=page_size
            )

    def get_exercise_detail(self, current_user: User, exercise_id: UUID) -> Exercise:
        role_name = get_user_role_name(self.db, current_user)
        exercise = self.repo.get_by_id(exercise_id, include_deleted=False)
        
        if not exercise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-EXE-EXERCISE_NOT_FOUND",
                    "message": "Exercise not found."
                }
            )

        if role_name == "Teacher":
            active_subject_ids = self._get_teacher_active_subject_ids(current_user.user_id)
            if exercise.created_by != current_user.user_id and exercise.subject_id not in active_subject_ids:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "code": "ERR-EXE-EXERCISE_NOT_FOUND",
                        "message": "Exercise not found."
                    }
                )

        return exercise

    def update_exercise(self, current_user: User, exercise_id: UUID, payload: ExerciseUpdate) -> Exercise:
        exercise = self.get_exercise_detail(current_user, exercise_id)
        return self.repo.update(exercise, title=payload.title, ai_metadata=payload.ai_metadata)

    def delete_exercise(self, current_user: User, exercise_id: UUID) -> None:
        exercise = self.get_exercise_detail(current_user, exercise_id)
        self.repo.soft_delete(exercise)

    def restore_exercise(self, current_user: User, exercise_id: UUID) -> Exercise:
        role_name = get_user_role_name(self.db, current_user)
        exercise = self.repo.get_by_id(exercise_id, include_deleted=True)
        
        if not exercise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-EXE-EXERCISE_NOT_FOUND",
                    "message": "Exercise not found."
                }
            )

        if role_name == "Teacher":
            active_subject_ids = self._get_teacher_active_subject_ids(current_user.user_id)
            if exercise.created_by != current_user.user_id and exercise.subject_id not in active_subject_ids:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "code": "ERR-EXE-EXERCISE_NOT_FOUND",
                        "message": "Exercise not found."
                    }
                )

        return self.repo.restore(exercise)

    def generate_ai_exercise(self, current_user: User, payload: AiExerciseGenerateRequest) -> AiExerciseGenerateOut:
        """
        Generates realistic exam questions (Part 1, 2, 3), creates real Exercise,
        Question, AnswerOption, and ClassAssignment records, persisting them into PostgreSQL.
        """
        # 1. Resolve Subject
        subject = None
        if payload.subject_name:
            subject = self.db.query(Subject).filter(
                Subject.subject_name.ilike(f"%{payload.subject_name.strip()}%"),
                Subject.status != 'DELETED'
            ).first()
        if not subject:
            subject = self.db.query(Subject).filter(Subject.status != 'DELETED').first()
        if not subject:
            subject = Subject(subject_name=payload.subject_name or "Toán học", status="ACTIVE")
            self.db.add(subject)
            self.db.flush()

        # 2. Resolve Class
        class_obj = None
        if payload.class_id:
            class_obj = self.db.query(Class).filter(
                Class.class_id == payload.class_id,
                Class.status != 'DELETED'
            ).first()

        if not class_obj:
            student_class = self.db.query(StudentClass).filter(
                StudentClass.student_id == current_user.user_id,
                StudentClass.status != 'DELETED'
            ).first()
            if student_class:
                class_obj = self.db.query(Class).filter(
                    Class.class_id == student_class.class_id,
                    Class.status != 'DELETED'
                ).first()

        if not class_obj:
            class_obj = self.db.query(Class).filter(Class.status != 'DELETED').first()

        if not class_obj:
            class_obj = Class(class_name="12A1", status="ACTIVE")
            self.db.add(class_obj)
            self.db.flush()

        # Ensure student is active in this class so attempts and feed work seamlessly
        enrollment = self.db.query(StudentClass).filter(
            StudentClass.student_id == current_user.user_id,
            StudentClass.class_id == class_obj.class_id
        ).first()
        if not enrollment:
            enrollment = StudentClass(
                student_id=current_user.user_id,
                class_id=class_obj.class_id,
                student_code=f"STU_{uuid.uuid4().hex[:6]}",
                status="ACTIVE"
            )
            self.db.add(enrollment)
            self.db.flush()
        elif enrollment.status != 'ACTIVE':
            enrollment.status = 'ACTIVE'
            self.db.flush()

        # 3. Generate Questions using AiExerciseGeneratorService
        raw_questions = AiExerciseGeneratorService.generate_questions(
            subject_name=payload.subject_name,
            grade_name=payload.grade_name or "Lớp 12",
            topic_prompt=payload.topic_prompt,
            part1_count=payload.part1_count,
            part2_count=payload.part2_count,
            part3_count=payload.part3_count
        )

        total_questions = len(raw_questions)
        clean_topic = payload.topic_prompt.strip()
        title_topic = clean_topic[:50] + "..." if len(clean_topic) > 50 else clean_topic
        exercise_title = f"{payload.subject_name} {payload.grade_name or 'Lớp 12'} – {title_topic}"

        # 4. Create Exercise record
        exercise = Exercise(
            title=exercise_title,
            subject_id=subject.subject_id,
            created_by=current_user.user_id,
            total_questions=total_questions,
            ai_metadata={
                "is_ai_generated": True,
                "topic_prompt": payload.topic_prompt,
                "grade_name": payload.grade_name,
                "duration_minutes": payload.duration_minutes,
                "part1_count": payload.part1_count,
                "part2_count": payload.part2_count,
                "part3_count": payload.part3_count
            },
            status="ACTIVE"
        )
        self.db.add(exercise)
        self.db.flush()

        # 5. Insert Questions and AnswerOptions
        for order, q_data in enumerate(raw_questions):
            q_type = q_data.get("question_type", "MultipleChoice")
            diff = q_data.get("difficulty", "NhanBiet")
            content = q_data.get("content", f"Câu hỏi {order + 1}")
            explanation = q_data.get("explanation")
            correct_answer = q_data.get("correct_answer")
            segments = q_data.get("segments")

            question = Question(
                exercise_id=exercise.exercise_id,
                content=content,
                content_markdown=q_data.get("content_markdown", content),
                content_latex=q_data.get("content_latex"),
                question_type=q_type,
                difficulty=diff,
                correct_answer=correct_answer,
                explanation=explanation,
                segments=segments,
                display_order=order,
                is_ai_generated=True,
                status="ACTIVE"
            )
            self.db.add(question)
            self.db.flush()

            if q_type == "MultipleChoice" and "answer_options" in q_data:
                for opt_data in q_data["answer_options"]:
                    opt = AnswerOption(
                        question_id=question.question_id,
                        content=opt_data.get("content", ""),
                        is_correct=bool(opt_data.get("is_correct", False)),
                        display_order=opt_data.get("display_order", 0)
                    )
                    self.db.add(opt)

        # 6. Create ClassAssignment
        now = datetime.now(timezone.utc)
        due_at = now + timedelta(days=14)
        assignment = ClassAssignment(
            class_id=class_obj.class_id,
            exercise_id=exercise.exercise_id,
            assigned_by=current_user.user_id,
            assigned_at=now,
            due_at=due_at,
            status="ACTIVE"
        )
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        self.db.refresh(exercise)

        return AiExerciseGenerateOut(
            exercise_id=exercise.exercise_id,
            assignment_id=assignment.assignment_id,
            title=exercise.title,
            subject_name=subject.subject_name,
            total_questions=total_questions,
            duration_minutes=payload.duration_minutes,
            class_id=class_obj.class_id,
            class_name=class_obj.class_name,
            due_at=assignment.due_at,
            created_at=exercise.created_at
        )
