# File Name: teacher_dashboard.py
# Description: API Router for Teacher and Homeroom Teacher Dashboard metrics, learning quality radar analytics, recent submissions, and weekly schedule.
# Created At: 2026-10-25
# Created By: Tam Khang
# Updated At: 2026-10-30
# Updated By: Tam Khang

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.core.database import get_db
from models.models import (
    User, Class, StudentClass, TeacherSubject, Subject,
    ClassAssignment, Exercise, StudentExerciseAttempt
)
from app.modules.auth.dependencies import require_perm, get_current_user
from app.modules.academic.scoping import get_user_role_name
from app.modules.exercise.routers.teacher_schedule import get_synced_schedule_items
from app.modules.exercise.services.attempt_service import AttemptService
from app.modules.exercise.services.learning_quality_service import LearningQualityService

router = APIRouter(prefix="/api/v1/teacher", tags=["teacher-dashboard"])


class TeacherDashboardMetrics(BaseModel):
    pending_grading_count: int = 0
    today_classes_count: int = 0
    total_classes_count: int = 0
    total_students_count: int = 0


class RadarSubjectScore(BaseModel):
    subject_name: str
    class_score: float
    grade_score: float = 7.5


class LearningQualityData(BaseModel):
    class_name: str
    radar_data: List[RadarSubjectScore]
    feedback_notes: List[str]


class RecentSubmissionItem(BaseModel):
    id: str
    student_name: str
    avatar_initial: str
    avatar_bg: str = "#E0E7FF"
    avatar_color: str = "#4338CA"
    exercise_title: str
    class_name: str
    submitted_time: str
    status: str
    status_label: str
    score: Optional[float] = None


class WeeklyScheduleItem(BaseModel):
    id: str
    day_of_week: int
    day_label: str
    date_number: Optional[str] = None
    date_str: Optional[str] = None
    title: str
    time: str
    period: str
    room: Optional[str] = None
    theme: str = "purple"
    urgency: str = "teaching"
    class_name: Optional[str] = None
    year: Optional[int] = 2026
    month: Optional[int] = 9
    day: Optional[int] = None


class TeacherDashboardResponse(BaseModel):
    metrics: TeacherDashboardMetrics
    learning_quality: LearningQualityData
    recent_submissions: List[RecentSubmissionItem]
    weekly_schedule: List[WeeklyScheduleItem]


def validate_class_access_for_dashboard(
    db: Session,
    current_user: User,
    class_id: UUID
) -> Class:
    """
    Validate that target class exists and caller has permission to view its homeroom analytics.
    Non-admin callers must be the homeroom teacher or an assigned subject teacher of this class.
    Raises 404 if class does not exist or is soft-deleted.
    Raises 403 if caller lacks authorization.
    """
    cls = db.query(Class).filter(
        Class.class_id == class_id,
        Class.status != "DELETED"
    ).first()
    if not cls:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found."
        )

    role_name = get_user_role_name(db, current_user)
    if role_name != "Admin":
        is_homeroom = (cls.homeroom_teacher_id == current_user.user_id)
        is_assigned = db.query(TeacherSubject.teacher_id).filter(
            TeacherSubject.class_id == class_id,
            TeacherSubject.teacher_id == current_user.user_id,
            TeacherSubject.status != "DELETED"
        ).first() is not None

        if not (is_homeroom or is_assigned):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You are not authorized to view data for this class."
            )
    return cls


@router.get(
    "/dashboard",
    response_model=TeacherDashboardResponse,
    dependencies=[Depends(require_perm("EXE_ATTEMPT_VIEW"))]
)
def get_teacher_dashboard(
    class_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve consolidated metrics, learning quality radar data, recent student submissions,
    and weekly timetable schedule for the authenticated teacher.
    """
    teacher_id = current_user.user_id
    role_name = get_user_role_name(db, current_user)

    # 1. Fetch assigned classes and homeroom class (prioritizing current academic year)
    today = date.today()
    start_year = today.year if today.month >= 8 else today.year - 1
    current_year = f"{start_year}-{start_year + 1}"

    assigned_records = db.query(TeacherSubject.class_id).filter(
        TeacherSubject.teacher_id == teacher_id,
        TeacherSubject.status != "DELETED"
    ).all()
    assigned_class_ids = {r[0] for r in assigned_records}

    homeroom_class = None
    if class_id:
        homeroom_class = validate_class_access_for_dashboard(db, current_user, class_id)

    if not homeroom_class:
        homeroom_class = db.query(Class).filter(
            Class.homeroom_teacher_id == teacher_id,
            Class.academic_year == current_year,
            Class.status != "DELETED"
        ).first()

    all_class_ids = set(assigned_class_ids)
    if homeroom_class:
        all_class_ids.add(homeroom_class.class_id)

    # Only Admin has platform-wide fallback view if they have no explicit assignments
    if not all_class_ids and role_name == "Admin":
        all_classes = db.query(Class).filter(Class.status != "DELETED").all()
        all_class_ids = {c.class_id for c in all_classes}

    total_classes = len(all_class_ids)

    # 2. Count active students
    student_count = db.query(func.count(func.distinct(StudentClass.student_id))).filter(
        StudentClass.class_id.in_(all_class_ids),
        StudentClass.status != "DELETED"
    ).scalar() or 0

    # 3. Retrieve student attempts for these classes
    attempts_query = db.query(
        StudentExerciseAttempt, User, Exercise, Class
    ).join(
        User, StudentExerciseAttempt.student_id == User.user_id
    ).join(
        ClassAssignment, StudentExerciseAttempt.assignment_id == ClassAssignment.assignment_id
    ).join(
        Exercise, ClassAssignment.exercise_id == Exercise.exercise_id
    ).join(
        Class, ClassAssignment.class_id == Class.class_id
    ).filter(
        ClassAssignment.class_id.in_(all_class_ids),
        StudentExerciseAttempt.status != "DELETED"
    )

    all_attempts = attempts_query.order_by(
        func.coalesce(
            StudentExerciseAttempt.end_time,
            StudentExerciseAttempt.start_time,
            StudentExerciseAttempt.created_at
        ).desc()
    ).limit(50).all()

    # Pending grading count: reuse the exact same service used by the Grading & Feedback page
    # so both screens always show identical numbers (no hardcoded fallback).
    grading_stats = AttemptService(db).get_grading_dashboard(current_user)
    pending_grading_count = grading_stats.pending_grading_count
    pending_review_count = grading_stats.pending_review_count

    # 4. Construct recent submissions list
    avatar_color_palette = [
        {"bg": "#E0E7FF", "color": "#4338CA"},
        {"bg": "#FEF3C7", "color": "#D97706"},
        {"bg": "#FCE7F3", "color": "#DB2777"},
        {"bg": "#DCFCE7", "color": "#15803D"},
        {"bg": "#F3E8FF", "color": "#7E22CE"},
    ]

    recent_submissions: List[RecentSubmissionItem] = []
    for idx, (att, stu, ex, cls) in enumerate(all_attempts[:6]):
        palette = avatar_color_palette[idx % len(avatar_color_palette)]
        name_parts = (stu.full_name or "Học sinh").strip().split(" ")
        initial = (name_parts[0][0] + name_parts[-1][0]).upper() if len(name_parts) >= 2 else (stu.full_name or "HS")[:2].upper()

        # Format submitted time in Vietnam timezone (UTC+7)
        time_ref = att.end_time or att.start_time
        time_str = "Hôm nay, 10:30"
        if time_ref:
            if time_ref.tzinfo is None:
                time_ref = time_ref.replace(tzinfo=timezone.utc)
            tz_vn = timezone(timedelta(hours=7))
            local_time = time_ref.astimezone(tz_vn)
            time_str = local_time.strftime("%d/%m, %H:%M")

        is_late = False
        status_code = "submitted"
        status_label = "Đã nộp"
        if att.score is None:
            status_code = "submitted"
            status_label = "Đã nộp"
        else:
            status_code = "graded"
            status_label = f"{float(att.score):.1f} điểm"

        recent_submissions.append(RecentSubmissionItem(
            id=str(att.attempt_id),
            student_name=stu.full_name or f"Học sinh {idx+1}",
            avatar_initial=initial,
            avatar_bg=palette["bg"],
            avatar_color=palette["color"],
            exercise_title=ex.title,
            class_name=cls.class_name,
            submitted_time=time_str,
            status=status_code,
            status_label=status_label,
            score=float(att.score) if att.score is not None else None
        ))

    # Fallback if no attempts in DB yet
    if not recent_submissions:
        recent_submissions = [
            RecentSubmissionItem(
                id="sub-1",
                student_name="Trần Thị B",
                avatar_initial="TB",
                avatar_bg="#E0E7FF",
                avatar_color="#4338CA",
                exercise_title="Đề thi thử Hóa học #2",
                class_name="12A1",
                submitted_time="10 phút trước",
                status="submitted",
                status_label="Đã nộp",
                score=None
            ),
            RecentSubmissionItem(
                id="sub-2",
                student_name="Lê Văn C",
                avatar_initial="LC",
                avatar_bg="#FEF3C7",
                avatar_color="#D97706",
                exercise_title="Bài tập Toán Hình học",
                class_name="12A1",
                submitted_time="1 giờ trước",
                status="late",
                status_label="Trễ hạn",
                score=None
            ),
            RecentSubmissionItem(
                id="sub-3",
                student_name="Phạm Hương D",
                avatar_initial="PD",
                avatar_bg="#FCE7F3",
                avatar_color="#DB2777",
                exercise_title="Tiểu luận Lịch sử",
                class_name="12A1",
                submitted_time="Hôm qua, 15:30",
                status="submitted",
                status_label="Đã nộp",
                score=None
            )
        ]

    # 5. Build synchronized weekly timetable schedule for upcoming week
    synced_items = get_synced_schedule_items()
    weekly_schedule: List[WeeklyScheduleItem] = []
    for item in synced_items:
        theme = "purple" if "12A1" in item.class_name or "11B2" in item.class_name else "blue"
        weekly_schedule.append(WeeklyScheduleItem(
            id=f"sch-{item.id}",
            day_of_week=item.day_of_week,
            day_label=item.day_label,
            date_number=str(item.day_number),
            date_str=item.date_str,
            title=f"{item.subject_name} - Lớp {item.class_name}" if "Lớp" not in item.subject_name and "Tổ" not in item.class_name and "Khối" not in item.class_name else item.subject_name,
            time=f"{item.start_time} - {item.end_time}",
            period=f"Tiết {item.period}",
            room=item.room,
            theme=theme,
            urgency=item.urgency,
            class_name=item.class_name,
            year=item.year,
            month=item.month,
            day=item.day_number,
        ))

    # Today's classes count: sessions in the shared timetable dated today (0 when no classes, e.g. Sunday)
    today_iso = date.today().isoformat()
    today_classes_count = sum(1 for s in weekly_schedule if s.date_str == today_iso)

    # 6. Build learning quality radar competencies with class average and grade comparison
    quality_service = LearningQualityService(db)
    quality_dict = quality_service.get_homeroom_learning_quality(
        teacher_user=current_user,
        class_id=homeroom_class.class_id if homeroom_class else class_id
    )

    radar_subjects = [
        RadarSubjectScore(
            subject_name=r["subject_name"],
            class_score=r["class_score"],
            grade_score=r["grade_score"]
        )
        for r in quality_dict["radar_data"]
    ]

    learning_quality = LearningQualityData(
        class_name=quality_dict["class_name"],
        radar_data=radar_subjects,
        feedback_notes=quality_dict["feedback_notes"]
    )

    return TeacherDashboardResponse(
        metrics=TeacherDashboardMetrics(
            pending_grading_count=pending_grading_count,
            today_classes_count=today_classes_count,
            total_classes_count=total_classes,
            total_students_count=student_count
        ),
        learning_quality=learning_quality,
        recent_submissions=recent_submissions,
        weekly_schedule=weekly_schedule
    )


@router.get(
    "/learning-quality",
    response_model=LearningQualityData,
    dependencies=[Depends(require_perm("EXE_ATTEMPT_VIEW"))]
)
def get_teacher_learning_quality(
    class_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve academic learning quality radar scores (class average vs grade cohort average)
    and pedagogical comparison remarks for a homeroom class.
    """
    if class_id:
        validate_class_access_for_dashboard(db, current_user, class_id)

    quality_service = LearningQualityService(db)
    quality_dict = quality_service.get_homeroom_learning_quality(
        teacher_user=current_user,
        class_id=class_id
    )
    return LearningQualityData(
        class_name=quality_dict["class_name"],
        radar_data=[
            RadarSubjectScore(
                subject_name=r["subject_name"],
                class_score=r["class_score"],
                grade_score=r["grade_score"]
            )
            for r in quality_dict["radar_data"]
        ],
        feedback_notes=quality_dict["feedback_notes"]
    )

