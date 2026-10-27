# File Name: teacher_schedule.py
# Description: Router providing the teaching timetable for teachers. Single source of truth shared by
#              the Teaching Schedule page and the Teacher Dashboard (today's classes + weekly schedule).
# Created At: 2026-10-07
# Created By: Tam Khang
# Updated At: 2026-10-25
# Updated By: Tam Khang

from typing import List, Optional
from datetime import date, timedelta
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User

router = APIRouter(prefix="/api/v1/teacher/schedule", tags=["Teacher Schedule"])

# Number of upcoming days (starting today) covered by the generated timetable
SCHEDULE_WINDOW_DAYS = 7

DAY_LABELS = {
    0: "THỨ 2", 1: "THỨ 3", 2: "THỨ 4", 3: "THỨ 5", 4: "THỨ 6", 5: "THỨ 7", 6: "CHỦ NHẬT",
}

# Weekly timetable template keyed by Python weekday (0 = Monday ... 5 = Saturday).
# Sunday (6) intentionally has no teaching sessions.
WEEKLY_TEMPLATE = {
    0: [
        {"period": 1, "class_name": "12A1", "subject_name": "Toán Cao Cấp", "room": "Phòng 302, Tòa A",
         "start_time": "07:30", "end_time": "09:00", "urgency": "teaching"},
        {"period": 6, "class_name": "Tổ Toán", "subject_name": "Họp Tổ Bộ Môn", "room": "Phòng Hội đồng",
         "start_time": "14:00", "end_time": "15:30", "urgency": "high"},
    ],
    1: [
        {"period": 3, "class_name": "11B2", "subject_name": "Đại số", "room": "Phòng 204, Tòa B",
         "start_time": "09:15", "end_time": "10:45", "urgency": "teaching"},
        {"period": 6, "class_name": "12A2", "subject_name": "Luyện thi TN THPT Toán", "room": "Phòng 304, Tòa A",
         "start_time": "14:00", "end_time": "15:30", "urgency": "critical"},
    ],
    2: [
        {"period": 1, "class_name": "12A1", "subject_name": "Hình học Không gian", "room": "Phòng 302, Tòa A",
         "start_time": "07:30", "end_time": "09:00", "urgency": "critical"},
        {"period": 4, "class_name": "10A3", "subject_name": "Giải tích nâng cao", "room": "Phòng 105, Tòa C",
         "start_time": "10:00", "end_time": "11:30", "urgency": "teaching"},
    ],
    3: [
        {"period": 2, "class_name": "11B2", "subject_name": "Kiểm tra 45p Đại số 11", "room": "Phòng 204, Tòa B",
         "start_time": "08:00", "end_time": "09:30", "urgency": "critical"},
        {"period": 4, "class_name": "12A1", "subject_name": "Chuyên đề Đạo hàm & Cực trị", "room": "Phòng 302, Tòa A",
         "start_time": "10:00", "end_time": "11:30", "urgency": "teaching"},
    ],
    4: [
        {"period": 1, "class_name": "12A1", "subject_name": "Sinh hoạt Lớp Chủ nhiệm", "room": "Phòng 302, Tòa A",
         "start_time": "07:30", "end_time": "08:15", "urgency": "teaching"},
        {"period": 3, "class_name": "12A1", "subject_name": "Ôn tập cuối tuần Toán 12", "room": "Phòng 302, Tòa A",
         "start_time": "09:15", "end_time": "10:45", "urgency": "high"},
    ],
    5: [
        {"period": 1, "class_name": "Khối 12", "subject_name": "Thi thử Đánh giá năng lực", "room": "Hội trường lớn",
         "start_time": "08:00", "end_time": "11:00", "urgency": "critical"},
    ],
}


class TeacherScheduleItemOut(BaseModel):
    id: int
    day_of_week: int  # 2..7 = Monday..Saturday, 8 = Sunday
    day_label: str
    date_str: str  # ISO date, e.g. 2026-10-26
    day_number: int
    month: int  # 0-indexed month (matches JavaScript Date)
    year: int
    period: int
    class_name: str
    subject_name: str
    room: str
    start_time: str
    end_time: str
    urgency: str = "teaching"  # 'critical', 'high', 'teaching'


class TeacherScheduleResponse(BaseModel):
    semester: str = "Học kỳ I"
    academic_year: str = "2026 - 2027"
    items: List[TeacherScheduleItemOut]


def get_synced_schedule_items(start_date: Optional[date] = None) -> List[TeacherScheduleItemOut]:
    """Generate timetable sessions for the next SCHEDULE_WINDOW_DAYS days starting from start_date (default today)."""
    start = start_date or date.today()
    items: List[TeacherScheduleItemOut] = []
    next_id = 1
    for offset in range(SCHEDULE_WINDOW_DAYS):
        current = start + timedelta(days=offset)
        weekday = current.weekday()
        for session in WEEKLY_TEMPLATE.get(weekday, []):
            items.append(TeacherScheduleItemOut(
                id=next_id,
                day_of_week=weekday + 2,
                day_label=DAY_LABELS[weekday],
                date_str=current.isoformat(),
                day_number=current.day,
                month=current.month - 1,
                year=current.year,
                **session,
            ))
            next_id += 1
    return items


@router.get("", response_model=TeacherScheduleResponse)
def get_teacher_schedule(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve synchronized teaching timetable for the authenticated teacher.
    """
    return TeacherScheduleResponse(
        semester="Học kỳ I",
        academic_year="2026 - 2027",
        items=get_synced_schedule_items(),
    )
