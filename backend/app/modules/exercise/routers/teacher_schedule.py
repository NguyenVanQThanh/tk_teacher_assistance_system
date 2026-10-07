# File Name: teacher_schedule.py
# Description: Router providing weekly teaching timetable and schedule for teachers.
# Created At: 2026-10-07
# Created By: Tam Khang
# Updated At: 2026-10-07
# Updated By: Tam Khang

from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User

router = APIRouter(prefix="/api/v1/teacher/schedule", tags=["Teacher Schedule"])


class TeacherScheduleItemOut(BaseModel):
    id: int
    day_of_week: int  # 2 to 7 (Monday to Saturday)
    period: int
    class_name: str
    subject_name: str
    room: str
    start_time: str
    end_time: str
    urgency: str = "teaching"  # 'critical', 'high', 'teaching'


class TeacherScheduleResponse(BaseModel):
    semester: str = "Học kỳ I"
    academic_year: str = "2023 - 2024"
    items: List[TeacherScheduleItemOut]


@router.get("", response_model=TeacherScheduleResponse)
def get_teacher_schedule(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve teaching timetable for the authenticated teacher.
    """
    sessions = [
        TeacherScheduleItemOut(
            id=1,
            day_of_week=2,
            period=1,
            class_name="12A1",
            subject_name="Toán học",
            room="P.302",
            start_time="07:30",
            end_time="09:00",
            urgency="teaching",
        ),
        TeacherScheduleItemOut(
            id=2,
            day_of_week=2,
            period=3,
            class_name="12A2",
            subject_name="Toán học",
            room="P.304",
            start_time="09:15",
            end_time="10:45",
            urgency="high",
        ),
        TeacherScheduleItemOut(
            id=3,
            day_of_week=3,
            period=2,
            class_name="11B1",
            subject_name="Toán học",
            room="P.201",
            start_time="08:15",
            end_time="09:45",
            urgency="teaching",
        ),
        TeacherScheduleItemOut(
            id=4,
            day_of_week=4,
            period=1,
            class_name="12A1",
            subject_name="Toán học",
            room="P.302",
            start_time="07:30",
            end_time="09:00",
            urgency="critical",
        ),
        TeacherScheduleItemOut(
            id=5,
            day_of_week=5,
            period=4,
            class_name="10C3",
            subject_name="Toán học",
            room="P.105",
            start_time="10:00",
            end_time="11:30",
            urgency="teaching",
        ),
        TeacherScheduleItemOut(
            id=6,
            day_of_week=6,
            period=1,
            class_name="12A1",
            subject_name="Sinh hoạt chủ nhiệm",
            room="P.302",
            start_time="07:30",
            end_time="08:15",
            urgency="teaching",
        ),
    ]

    return TeacherScheduleResponse(
        semester="Học kỳ I",
        academic_year="2023 - 2024",
        items=sessions,
    )
