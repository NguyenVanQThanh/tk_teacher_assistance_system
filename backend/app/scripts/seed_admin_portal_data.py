# File Name: seed_admin_portal_data.py
# Description: Idempotent seed script for Admin Portal accounts, classes, exercises, logs, reports, and settings.
# Created At: 2026-11-14
# Created By: Tam Khang
# Updated At: 2026-11-14
# Updated By: Tam Khang

import json
import logging
import os
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

# Ensure backend directory is on sys.path for both module and script execution.
BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.modules.admin.routers import reports as reports_router
from app.modules.admin.routers import settings as settings_router
from app.modules.admin.routers.roles import _ensure_seeded
from app.modules.admin.state_store import (
    append_state_item,
    get_latest_state,
    list_state_items,
    upsert_state,
)
from app.scripts.rbac_seed import seed_rbac
from models.models import (
    AnswerOption,
    ApprovalRequest,
    AuditLog,
    Class,
    ClassAssignment,
    Document,
    Exercise,
    Permission,
    Question,
    Role,
    StudentClass,
    StudentExerciseAttempt,
    Subject,
    SupportTicket,
    TeacherSubject,
    User,
)

logger = logging.getLogger(__name__)
ACCOUNTS_INFO_PATH = Path(__file__).resolve().parent / "seed_accounts_info.json"

FEMALE_EXACT_TOKENS = {
    "cô",
    "thị",
    "mai",
    "trang",
    "hà",
    "ngọc",
    "liên",
    "vy",
    "linh",
    "thư",
    "hương",
    "lan",
    "phương",
    "dung",
    "my",
    "nhi",
    "uyên",
    "trinh",
    "yến",
    "quỳnh",
    "thảo",
    "hoa",
    "châu",
    "huyền",
    "hân",
    "kim",
    "tiên",
    "ngân",
    "nhung",
    "hạnh",
    "như",
    "nguyệt",
    "phượng",
    "trúc",
    "đào",
}

BASE_STAFF_SPECS: List[Dict[str, Any]] = [
    {
        "phone": "0999000001",
        "email": "admin@school.com",
        "full_name": "Quản trị viên Hệ thống",
        "role_name": "Admin",
        "password_plain": "Admin@1234",
        "birthday": date(1982, 1, 15),
        "gender": "Nam",
        "status": "ACTIVE",
    },
    {
        "phone": "0999000002",
        "email": "teacher@school.com",
        "full_name": "Sample Teacher (Thầy Nguyễn Văn A)",
        "role_name": "Teacher",
        "password_plain": "Teacher@1234",
        "birthday": date(1984, 6, 10),
        "gender": "Nam",
        "status": "ACTIVE",
    },
    {
        "phone": "0999000004",
        "email": "teacher_ly@school.com",
        "full_name": "Thầy Nguyễn Văn An",
        "role_name": "Teacher",
        "password_plain": "Teacher@1234",
        "birthday": date(1986, 3, 22),
        "gender": "Nam",
        "status": "ACTIVE",
    },
    {
        "phone": "0999000005",
        "email": "teacher_hoa@school.com",
        "full_name": "Cô Trần Thị Mai",
        "role_name": "Teacher",
        "password_plain": "Teacher@1234",
        "birthday": date(1987, 8, 14),
        "gender": "Nữ",
        "status": "ACTIVE",
    },
    {
        "phone": "0999000006",
        "email": "teacher_anh@school.com",
        "full_name": "Thầy Lê Hoàng Long",
        "role_name": "Teacher",
        "password_plain": "Teacher@1234",
        "birthday": date(1985, 11, 5),
        "gender": "Nam",
        "status": "ACTIVE",
    },
    {
        "phone": "0999000007",
        "email": "teacher_van@school.com",
        "full_name": "Cô Phạm Thu Trang",
        "role_name": "Teacher",
        "password_plain": "Teacher@1234",
        "birthday": date(1989, 2, 19),
        "gender": "Nữ",
        "status": "ACTIVE",
    },
    {
        "phone": "0999000008",
        "email": "teacher_sinh@school.com",
        "full_name": "Cô Đặng Thu Hà (Tổ Sinh học)",
        "role_name": "Teacher",
        "password_plain": "Teacher@1234",
        "birthday": date(1986, 7, 28),
        "gender": "Nữ",
        "status": "ACTIVE",
    },
    {
        "phone": "0999000009",
        "email": "teacher_su@school.com",
        "full_name": "Thầy Nguyễn Quốc Hùng (Tổ Lịch sử)",
        "role_name": "Teacher",
        "password_plain": "Teacher@1234",
        "birthday": date(1983, 12, 3),
        "gender": "Nam",
        "status": "ACTIVE",
    },
]

SPECIAL_ROLE_ACCOUNTS: List[Dict[str, Any]] = [
    {
        "phone": "0999000010",
        "email": "headteacher1@school.com",
        "full_name": "ThS. Lê Nguyên",
        "role_name": "head_teacher",
        "password_plain": "Teacher@1234",
        "birthday": date(1985, 5, 12),
        "gender": "Nam",
        "status": "ACTIVE",
    },
    {
        "phone": "0999000011",
        "email": "headteacher2@school.com",
        "full_name": "TS. Phạm Hoàng Nam",
        "role_name": "head_teacher",
        "password_plain": "Teacher@1234",
        "birthday": date(1985, 5, 12),
        "gender": "Nam",
        "status": "ACTIVE",
    },
    {
        "phone": "0999000012",
        "email": "academicstaff1@school.com",
        "full_name": "Cô Nguyễn Thị Bích Ngọc",
        "role_name": "academic_staff",
        "password_plain": "Teacher@1234",
        "birthday": date(1988, 9, 20),
        "gender": "Nữ",
        "status": "ACTIVE",
    },
    {
        "phone": "0999000013",
        "email": "academicstaff2@school.com",
        "full_name": "Thầy Trần Minh Khôi",
        "role_name": "academic_staff",
        "password_plain": "Teacher@1234",
        "birthday": date(1988, 9, 20),
        "gender": "Nam",
        "status": "ACTIVE",
    },
]

INACTIVE_ACCOUNTS: List[Dict[str, Any]] = [
    {
        "phone": "0999000014",
        "email": "teacher_inactive1@school.com",
        "full_name": "Thầy Vũ Minh Đức",
        "role_name": "Teacher",
        "password_plain": "Teacher@1234",
        "birthday": date(1990, 4, 10),
        "gender": "Nam",
        "status": "INACTIVE",
    },
    {
        "phone": "0999000015",
        "email": "teacher_inactive2@school.com",
        "full_name": "Cô Hoàng Bích Liên",
        "role_name": "Teacher",
        "password_plain": "Teacher@1234",
        "birthday": date(1991, 10, 22),
        "gender": "Nữ",
        "status": "INACTIVE",
    },
    {
        "phone": "0999200001",
        "email": "student_inactive1@school.com",
        "full_name": "Lê Gia Bảo",
        "role_name": "Student",
        "password_plain": "Student@1234",
        "birthday": date(2008, 2, 14),
        "gender": "Nam",
        "status": "INACTIVE",
    },
]

UNASSIGNED_STUDENTS: List[Dict[str, Any]] = [
    {
        "phone": "0999200002",
        "email": "unassigned_student2@school.com",
        "full_name": "Trần Thảo Vy",
        "gender": "Nữ",
    },
    {
        "phone": "0999200003",
        "email": "unassigned_student3@school.com",
        "full_name": "Nguyễn Nhật Minh",
        "gender": "Nam",
    },
    {
        "phone": "0999200004",
        "email": "unassigned_student4@school.com",
        "full_name": "Phạm Khánh Linh",
        "gender": "Nữ",
    },
    {
        "phone": "0999200005",
        "email": "unassigned_student5@school.com",
        "full_name": "Hoàng Quốc Huy",
        "gender": "Nam",
    },
    {
        "phone": "0999200006",
        "email": "unassigned_student6@school.com",
        "full_name": "Võ Ngọc Anh",
        "gender": "Nữ",
    },
    {
        "phone": "0999200007",
        "email": "unassigned_student7@school.com",
        "full_name": "Đỗ Tuấn Kiệt",
        "gender": "Nam",
    },
    {
        "phone": "0999200008",
        "email": "unassigned_student8@school.com",
        "full_name": "Bùi Minh Thư",
        "gender": "Nữ",
    },
    {
        "phone": "0999200009",
        "email": "unassigned_student9@school.com",
        "full_name": "Dương Hải Đăng",
        "gender": "Nam",
    },
]

SUBJECT_SPECS: List[Dict[str, str]] = [
    {
        "subject_name": "Toán học",
        "description": "Chương trình Toán THPT và luyện thi đại học",
        "head_phone": "0999000002",
    },
    {
        "subject_name": "Vật lý",
        "description": "Chương trình Vật lý THPT cơ bản và nâng cao",
        "head_phone": "0999000004",
    },
    {
        "subject_name": "Hóa học",
        "description": "Hóa học vô cơ, hữu cơ và thí nghiệm THPT",
        "head_phone": "0999000005",
    },
    {
        "subject_name": "Tiếng Anh",
        "description": "Tiếng Anh THPT theo khung năng lực 6 bậc",
        "head_phone": "0999000006",
    },
    {
        "subject_name": "Ngữ văn",
        "description": "Ngữ văn, đọc hiểu và nghị luận THPT",
        "head_phone": "0999000007",
    },
    {
        "subject_name": "Sinh học",
        "description": "Sinh học tế bào, di truyền và tiến hóa THPT",
        "head_phone": "0999000008",
    },
    {
        "subject_name": "Lịch sử",
        "description": "Lịch sử Việt Nam và thế giới cận hiện đại",
        "head_phone": "0999000009",
    },
]

FALLBACK_ROSTER_STUDENT_SPECS: List[Dict[str, str]] = [
    {"phone": "0999100001", "email": "student1@school.com", "full_name": "Nguyễn Hoàng Anh", "gender": "Nam"},
    {"phone": "0999100002", "email": "student2@school.com", "full_name": "Trần Minh Bảo", "gender": "Nam"},
    {"phone": "0999100003", "email": "student3@school.com", "full_name": "Lê Thị Ngọc Châu", "gender": "Nữ"},
    {"phone": "0999100004", "email": "student4@school.com", "full_name": "Phạm Đức Dũng", "gender": "Nam"},
    {"phone": "0999100005", "email": "student5@school.com", "full_name": "Hoàng Thùy Dương", "gender": "Nữ"},
    {"phone": "0999100006", "email": "student6@school.com", "full_name": "Vũ Hải Đăng", "gender": "Nam"},
    {"phone": "0999100007", "email": "student7@school.com", "full_name": "Đặng Gia Hân", "gender": "Nữ"},
    {"phone": "0999100008", "email": "student8@school.com", "full_name": "Bùi Trung Hiếu", "gender": "Nam"},
    {"phone": "0999100021", "email": "student21@school.com", "full_name": "Nguyễn Khải Hoàn", "gender": "Nam"},
    {"phone": "0999100022", "email": "student22@school.com", "full_name": "Trần Ngọc Huyền", "gender": "Nữ"},
    {"phone": "0999100023", "email": "student23@school.com", "full_name": "Lê Quốc Hưng", "gender": "Nam"},
    {"phone": "0999100024", "email": "student24@school.com", "full_name": "Phạm Quỳnh Hương", "gender": "Nữ"},
    {"phone": "0999100025", "email": "student25@school.com", "full_name": "Hoàng Gia Khang", "gender": "Nam"},
    {"phone": "0999100026", "email": "student26@school.com", "full_name": "Vũ Anh Khoa", "gender": "Nam"},
    {"phone": "0999100027", "email": "student27@school.com", "full_name": "Đặng Thiên Kim", "gender": "Nữ"},
    {"phone": "0999100028", "email": "student28@school.com", "full_name": "Bùi Ngọc Lan", "gender": "Nữ"},
    {"phone": "0999100039", "email": "student39@school.com", "full_name": "Nguyễn Tấn Phát", "gender": "Nam"},
    {"phone": "0999100040", "email": "student40@school.com", "full_name": "Trần Hồng Phúc", "gender": "Nam"},
    {"phone": "0999100041", "email": "student41@school.com", "full_name": "Lê Minh Quân", "gender": "Nam"},
    {"phone": "0999100042", "email": "student42@school.com", "full_name": "Phạm Diễm Quỳnh", "gender": "Nữ"},
    {"phone": "0999100043", "email": "student43@school.com", "full_name": "Hoàng Phương Thảo", "gender": "Nữ"},
    {"phone": "0999100044", "email": "student44@school.com", "full_name": "Vũ Đức Thịnh", "gender": "Nam"},
    {"phone": "0999100045", "email": "student45@school.com", "full_name": "Đặng Anh Thư", "gender": "Nữ"},
    {"phone": "0999100046", "email": "student46@school.com", "full_name": "Bùi Thủy Tiên", "gender": "Nữ"},
]

CLASS_SPECS: List[Dict[str, Any]] = [
    {
        "class_name": "10A1 - Chuyên Toán",
        "homeroom_phone": "0999000006",
        "academic_year": "2025-2026",
        "specialization": "Chuyên Toán",
        "preserve_existing": False,
        "code_prefix": "HS10A1",
        "student_phones": ["0999100039", "0999100040", "0999100041", "0999100042"],
    },
    {
        "class_name": "10A2 - Chuyên Anh",
        "homeroom_phone": "0999000007",
        "academic_year": "2025-2026",
        "specialization": "Chuyên Anh",
        "preserve_existing": False,
        "code_prefix": "HS10A2",
        "student_phones": ["0999100043", "0999100044", "0999100045", "0999100046"],
    },
    {
        "class_name": "10A3",
        "homeroom_phone": "0999000005",
        "academic_year": "2025-2026",
        "specialization": "Ban Cơ bản",
        "preserve_existing": True,
        "code_prefix": None,
        "student_phones": [],
    },
    {
        "class_name": "11A1 - Chuyên Lý",
        "homeroom_phone": "0999000008",
        "academic_year": "2025-2026",
        "specialization": "Chuyên Lý",
        "preserve_existing": False,
        "code_prefix": "HS11A1",
        "student_phones": ["0999100021", "0999100022", "0999100023", "0999100024"],
    },
    {
        "class_name": "11B1 - Khoa học Tự nhiên",
        "homeroom_phone": "0999000009",
        "academic_year": "2025-2026",
        "specialization": "Khoa học Tự nhiên",
        "preserve_existing": False,
        "code_prefix": "HS11B1",
        "student_phones": ["0999100025", "0999100026", "0999100027", "0999100028"],
    },
    {
        "class_name": "11B2",
        "homeroom_phone": "0999000004",
        "academic_year": "2025-2026",
        "specialization": "Ban Tự nhiên",
        "preserve_existing": True,
        "code_prefix": None,
        "student_phones": [],
    },
    {
        "class_name": "12A1",
        "homeroom_phone": "0999000002",
        "academic_year": "2025-2026",
        "specialization": "Ban Tự nhiên",
        "preserve_existing": True,
        "code_prefix": None,
        "student_phones": [],
    },
    {
        "class_name": "12A2 - Chuyên Hóa",
        "homeroom_phone": "0999000004",
        "academic_year": "2025-2026",
        "specialization": "Chuyên Hóa",
        "preserve_existing": False,
        "code_prefix": "HS12A2",
        "student_phones": ["0999100001", "0999100002", "0999100003", "0999100004"],
    },
    {
        "class_name": "12A3 - Khoa học Xã hội",
        "homeroom_phone": None,
        "academic_year": "2025-2026",
        "specialization": "Khoa học Xã hội",
        "preserve_existing": False,
        "code_prefix": "HS12A3",
        "student_phones": ["0999100005", "0999100006", "0999100007", "0999100008"],
    },
]

TEACHER_SUBJECT_ASSIGNMENTS: List[Tuple[str, str, str]] = [
    ("0999000002", "10A1 - Chuyên Toán", "Toán học"),
    ("0999000002", "12A2 - Chuyên Hóa", "Toán học"),
    ("0999000004", "11A1 - Chuyên Lý", "Vật lý"),
    ("0999000004", "11B1 - Khoa học Tự nhiên", "Vật lý"),
    ("0999000005", "11B1 - Khoa học Tự nhiên", "Hóa học"),
    ("0999000005", "12A2 - Chuyên Hóa", "Hóa học"),
    ("0999000006", "10A1 - Chuyên Toán", "Tiếng Anh"),
    ("0999000006", "10A2 - Chuyên Anh", "Tiếng Anh"),
    ("0999000007", "10A2 - Chuyên Anh", "Ngữ văn"),
    ("0999000007", "12A3 - Khoa học Xã hội", "Ngữ văn"),
    ("0999000008", "11B1 - Khoa học Tự nhiên", "Sinh học"),
    ("0999000008", "12A2 - Chuyên Hóa", "Sinh học"),
    ("0999000009", "11A1 - Chuyên Lý", "Lịch sử"),
    ("0999000009", "12A3 - Khoa học Xã hội", "Lịch sử"),
]

APPROVAL_REQUEST_SPECS: List[Dict[str, Any]] = [
    {
        "requester_name": "Thầy Nguyễn Văn An",
        "requester_sub": "Tổ Vật lý · GVCN 11B2",
        "avatar_text": "NA",
        "avatar_bg": "#4f46e5",
        "type": "Đăng ký dạy thay lớp 11B1 (Tiết 3-4 Thứ 5)",
        "status": "pending",
        "review_note": None,
        "days_ago": 0,
    },
    {
        "requester_name": "Cô Trần Thị Mai",
        "requester_sub": "Tổ Hóa học · GVCN 10A3",
        "avatar_text": "TM",
        "avatar_bg": "#0ea5e9",
        "type": "Đề nghị cấp quyền xuất bảng điểm tổng kết Khối 12",
        "status": "pending",
        "review_note": None,
        "days_ago": 1,
    },
    {
        "requester_name": "ThS. Lê Nguyên",
        "requester_sub": "Trưởng bộ môn · Khối Chuyên",
        "avatar_text": "LN",
        "avatar_bg": "#10b981",
        "type": "Phê duyệt ngân hàng câu hỏi ôn tập Học kỳ I - Môn Toán",
        "status": "pending",
        "review_note": None,
        "days_ago": 1,
    },
    {
        "requester_name": "Cô Phạm Thu Trang",
        "requester_sub": "Tổ Ngữ văn · GVCN 10A2",
        "avatar_text": "PT",
        "avatar_bg": "#f59e0b",
        "type": "Xin mở khóa nộp điểm kiểm tra 15 phút lớp 10A2",
        "status": "pending",
        "review_note": None,
        "days_ago": 2,
    },
    {
        "requester_name": "Thầy Lê Hoàng Long",
        "requester_sub": "Tổ Tiếng Anh · GVCN 10A1",
        "avatar_text": "HL",
        "avatar_bg": "#8b5cf6",
        "type": "Cập nhật sĩ số và chuyển lớp cho học sinh khối 10",
        "status": "approved",
        "review_note": "Đã phê duyệt theo đề xuất của tổ chuyên môn.",
        "days_ago": 3,
    },
    {
        "requester_name": "Cô Đặng Thu Hà (Tổ Sinh học)",
        "requester_sub": "Tổ Sinh học · GVCN 11A1",
        "avatar_text": "ĐH",
        "avatar_bg": "#ef4444",
        "type": "Yêu cầu thay đổi lịch thi giữa kỳ môn Sinh học",
        "status": "rejected",
        "review_note": "Chưa đủ hồ sơ minh chứng điều chỉnh lịch thi tập trung.",
        "days_ago": 4,
    },
]

SUPPORT_TICKET_SPECS: List[Dict[str, str]] = [
    {
        "full_name": "Nguyễn Hoàng Minh",
        "phone": "0912345001",
        "request_type": "forgot_password",
        "message": "Em quên mật khẩu tài khoản học sinh lớp 11B1, nhờ Admin hỗ trợ cấp lại.",
        "status": "PENDING",
    },
    {
        "full_name": "Cô Hoàng Bích Liên",
        "phone": "0999000015",
        "request_type": "new_account",
        "message": "Giáo viên mới nhận công tác tổ Vật lý, xin kích hoạt tài khoản truy cập hệ thống.",
        "status": "PENDING",
    },
    {
        "full_name": "Lê Gia Bảo",
        "phone": "0999200001",
        "request_type": "new_account",
        "message": "Học sinh chuyển trường mới nhập học, đề nghị kích hoạt tài khoản SmartLMS.",
        "status": "PENDING",
    },
]

AUDIT_LOG_SPECS: List[Dict[str, Any]] = [
    {
        "title": "Khởi tạo dữ liệu phân quyền RBAC chuẩn",
        "description": "Đồng bộ 5 vai trò hệ thống và ma trận quyền truy cập 28 chức năng.",
        "actor_name": "Quản trị viên Hệ thống",
        "ip_address": "192.168.1.10",
        "severity": "info",
        "days_ago": 6,
    },
    {
        "title": "Phân công giáo viên chủ nhiệm năm học 2025-2026",
        "description": "Cập nhật danh sách giáo viên chủ nhiệm cho các lớp khối 10, 11 và 12.",
        "actor_name": "Cô Nguyễn Thị Bích Ngọc",
        "ip_address": "192.168.1.11",
        "severity": "info",
        "days_ago": 5,
    },
    {
        "title": "Cập nhật danh sách học sinh nhập học đợt 1",
        "description": "Tiếp nhận hồ sơ 8 học sinh bổ sung chờ phân lớp chính thức.",
        "actor_name": "Thầy Trần Minh Khôi",
        "ip_address": "192.168.1.12",
        "severity": "info",
        "days_ago": 4,
    },
    {
        "title": "Đồng bộ cấu hình ngưỡng điểm tổng kết",
        "description": "Áp dụng thang điểm 10 với trọng số 20% - 30% - 50% cho HK1.",
        "actor_name": "Quản trị viên Hệ thống",
        "ip_address": "192.168.1.13",
        "severity": "info",
        "days_ago": 3,
    },
    {
        "title": "Cảnh báo đăng nhập sai mật khẩu liên tiếp (0999000014)",
        "description": "Ghi nhận 3 lần nhập sai mật khẩu từ tài khoản giáo viên chưa kích hoạt.",
        "actor_name": "Cổng xác thực JWT",
        "ip_address": "192.168.1.15",
        "severity": "warning",
        "days_ago": 3,
    },
    {
        "title": "Thay đổi hạn mức token AI hàng ngày cho giáo viên",
        "description": "Điều chỉnh giới hạn Gemini Flash lên 250,000 token/ngày mỗi tài khoản.",
        "actor_name": "Quản trị viên Hệ thống",
        "ip_address": "192.168.1.16",
        "severity": "warning",
        "days_ago": 2,
    },
    {
        "title": "Tạm khóa tài khoản học sinh chờ xác minh thông tin",
        "description": "Đặt trạng thái INACTIVE cho tài khoản 0999200001 theo yêu cầu giáo vụ.",
        "actor_name": "Cô Nguyễn Thị Bích Ngọc",
        "ip_address": "192.168.1.17",
        "severity": "warning",
        "days_ago": 2,
    },
    {
        "title": "Điều chỉnh hạn nộp bài tập khối 12 tuần 10",
        "description": "Gia hạn thời gian nộp bài tập chuyên đề Hóa hữu cơ thêm 48 giờ.",
        "actor_name": "ThS. Lê Nguyên",
        "ip_address": "192.168.1.18",
        "severity": "warning",
        "days_ago": 1,
    },
    {
        "title": "Phát hiện truy cập trái phép vào endpoint quản trị cấu hình",
        "description": "Chặn yêu cầu không có quyền admin.settings.manage từ phiên người dùng.",
        "actor_name": "Hệ thống Giám sát RBAC",
        "ip_address": "192.168.1.22",
        "severity": "danger",
        "days_ago": 1,
    },
    {
        "title": "Thu hồi phiên đăng nhập bất thường từ thiết bị lạ",
        "description": "Hệ thống đã tự động vô hiệu hóa token cũ và yêu cầu xác thực lại.",
        "actor_name": "Hệ thống Bảo mật",
        "ip_address": "192.168.1.25",
        "severity": "danger",
        "days_ago": 0,
    },
]

EXERCISE_SPECS: List[Dict[str, Any]] = [
    {
        "subject": "Toán học",
        "title": "Chuyên đề Hàm số và Cực trị (AI Bloom)",
        "class_name": "10A1 - Chuyên Toán",
        "kind": "PRACTICE",
        "is_ai": True,
        "scores": [8.5, 9.2, 7.5],
        "days_ago": 5,
    },
    {
        "subject": "Toán học",
        "title": "Kiểm tra Đại số Tổ hợp và Xác suất",
        "class_name": "10A1 - Chuyên Toán",
        "kind": "EXAM",
        "is_ai": False,
        "scores": [6.8, 8.0, 9.5],
        "days_ago": 2,
    },
    {
        "subject": "Vật lý",
        "title": "Dao động điều hòa và Con lắc lò xo (AI)",
        "class_name": "11A1 - Chuyên Lý",
        "kind": "PRACTICE",
        "is_ai": True,
        "scores": [7.2, 8.8, 9.0],
        "days_ago": 4,
    },
    {
        "subject": "Vật lý",
        "title": "Bài tập Sóng cơ và Giao thoa sóng",
        "class_name": "11A1 - Chuyên Lý",
        "kind": "EXAM",
        "is_ai": False,
        "scores": [5.5, 7.8, 8.4],
        "days_ago": 1,
    },
    {
        "subject": "Hóa học",
        "title": "Cân bằng hóa học và Dung dịch điện ly (AI)",
        "class_name": "12A2 - Chuyên Hóa",
        "kind": "PRACTICE",
        "is_ai": True,
        "scores": [8.1, 9.4, 6.5],
        "days_ago": 5,
    },
    {
        "subject": "Hóa học",
        "title": "Chuyên đề Este - Lipit nâng cao",
        "class_name": "12A2 - Chuyên Hóa",
        "kind": "EXAM",
        "is_ai": False,
        "scores": [7.0, 8.6, 9.8],
        "days_ago": 3,
    },
    {
        "subject": "Tiếng Anh",
        "title": "Academic Vocabulary & Grammar Review (AI)",
        "class_name": "10A2 - Chuyên Anh",
        "kind": "PRACTICE",
        "is_ai": True,
        "scores": [8.9, 9.6, 7.4],
        "days_ago": 4,
    },
    {
        "subject": "Tiếng Anh",
        "title": "Reading Comprehension Unit 3 Mock Test",
        "class_name": "10A2 - Chuyên Anh",
        "kind": "EXAM",
        "is_ai": False,
        "scores": [6.2, 7.9, 8.7],
        "days_ago": 1,
    },
    {
        "subject": "Ngữ văn",
        "title": "Phân tích tác phẩm Thơ hiện đại (AI)",
        "class_name": "12A3 - Khoa học Xã hội",
        "kind": "PRACTICE",
        "is_ai": True,
        "scores": [7.5, 8.2, 9.1],
        "days_ago": 6,
    },
    {
        "subject": "Ngữ văn",
        "title": "Đọc hiểu văn bản Nghị luận xã hội",
        "class_name": "12A3 - Khoa học Xã hội",
        "kind": "EXAM",
        "is_ai": False,
        "scores": [5.0, 6.9, 8.0],
        "days_ago": 2,
    },
    {
        "subject": "Sinh học",
        "title": "Cơ chế di truyền và Biến dị cấp phân tử (AI)",
        "class_name": "11B1 - Khoa học Tự nhiên",
        "kind": "PRACTICE",
        "is_ai": True,
        "scores": [8.3, 7.6, 9.3],
        "days_ago": 3,
    },
    {
        "subject": "Sinh học",
        "title": "Quy luật Menđen và Tương tác gen",
        "class_name": "11B1 - Khoa học Tự nhiên",
        "kind": "EXAM",
        "is_ai": False,
        "scores": [4.5, 7.1, 8.5],
        "days_ago": 1,
    },
    {
        "subject": "Lịch sử",
        "title": "Chiến tranh thế giới thứ hai 1939-1945 (AI)",
        "class_name": "12A3 - Khoa học Xã hội",
        "kind": "PRACTICE",
        "is_ai": True,
        "scores": [7.8, 8.9, 9.0],
        "days_ago": 4,
    },
    {
        "subject": "Lịch sử",
        "title": "Cách mạng tháng Tám năm 1945 ở Việt Nam",
        "class_name": "12A3 - Khoa học Xã hội",
        "kind": "EXAM",
        "is_ai": False,
        "scores": [6.0, 7.7, 8.8],
        "days_ago": 0,
    },
]


def _infer_gender(full_name: str, phone: Optional[str] = None) -> str:
    """Resolve explicit seeded gender or infer from Vietnamese name tokens."""
    if phone:
        for group in (
            BASE_STAFF_SPECS,
            SPECIAL_ROLE_ACCOUNTS,
            INACTIVE_ACCOUNTS,
            UNASSIGNED_STUDENTS,
            FALLBACK_ROSTER_STUDENT_SPECS,
        ):
            for spec in group:
                if spec["phone"] == phone and spec.get("gender"):
                    return spec["gender"]

    tokens = {tok.strip(".,()").lower() for tok in (full_name or "").split()}
    if tokens & FEMALE_EXACT_TOKENS:
        return "Nữ"
    return "Nam"


def _default_birthday_for_role(role_name: str, index_seed: int) -> date:
    """Return a valid deterministic birthday honoring check_user_age_by_role."""
    norm = role_name.lower()
    month = (index_seed % 12) + 1
    day = (index_seed % 25) + 1
    if norm == "student":
        return date(2008, month, day)
    if norm == "admin":
        return date(1982, 1, 15)
    year = 1985 + (index_seed % 6)
    return date(year, month, day)


def _upsert_user_gender_meta(session: Session, user: User, role_name: str, gender: Optional[str]) -> bool:
    """Persist gender into state_store only if missing so re-runs stay idempotent."""
    meta_prefix = "__STUDENT_META__:" if role_name.lower() == "student" else "__USER_META__:"
    key_title = f"{meta_prefix}{user.user_id}"
    existing = get_latest_state(session, key_title)
    if existing and existing.get("gender"):
        return False

    resolved_gender = gender or _infer_gender(user.full_name or "", user.phone)
    payload = dict(existing) if existing else {}
    payload["gender"] = resolved_gender
    upsert_state(session, key_title, payload, actor_name="System")
    return True


def _get_or_create_user(
    session: Session,
    spec: Dict[str, Any],
    roles_map: Dict[str, Role],
    summary: Dict[str, int],
) -> User:
    """Get an existing user by phone or create one cleanly without duplicating."""
    existing = session.query(User).filter(User.phone == spec["phone"]).first()
    role = roles_map[spec["role_name"]]
    if existing is not None:
        summary["users_existing"] += 1
        return existing

    user = User(
        phone=spec["phone"],
        email=spec["email"],
        password_hash=get_password_hash(spec["password_plain"]),
        full_name=spec["full_name"],
        birthday=spec["birthday"],
        role_id=role.role_id,
        status=spec.get("status", "ACTIVE"),
    )
    session.add(user)
    session.flush()
    _upsert_user_gender_meta(session, user, spec["role_name"], spec.get("gender"))
    summary["users_created"] += 1
    return user


def _backfill_seeded_users(
    session: Session,
    roles_by_id: Dict[Any, Role],
    summary: Dict[str, int],
) -> None:
    """Backfill birthday and gender state metadata on existing 0999% seeded users."""
    seeded_users = (
        session.query(User)
        .filter(User.phone.like("0999%"), func.upper(User.status) != "DELETED")
        .order_by(User.phone.asc())
        .all()
    )
    for idx, user in enumerate(seeded_users):
        role = roles_by_id.get(user.role_id)
        role_name = role.name if role else "Student"
        if user.birthday is None:
            user.birthday = _default_birthday_for_role(role_name, idx)
            summary["users_backfilled_birthday"] += 1
        if _upsert_user_gender_meta(session, user, role_name, None):
            summary["users_backfilled_gender"] += 1
    session.flush()


def _seed_subjects(
    session: Session,
    users_by_phone: Dict[str, User],
    summary: Dict[str, int],
) -> Dict[str, Subject]:
    """Ensure all 7 core subjects exist with active head teachers."""
    subjects_by_name: Dict[str, Subject] = {}
    for spec in SUBJECT_SPECS:
        subj = session.query(Subject).filter(Subject.subject_name == spec["subject_name"]).first()
        head_user = users_by_phone.get(spec["head_phone"])
        if subj is None:
            subj = Subject(
                subject_name=spec["subject_name"],
                description=spec["description"],
                status="ACTIVE",
                head_teacher_id=head_user.user_id if head_user else None,
            )
            session.add(subj)
            session.flush()
            summary["subjects_created"] += 1
        else:
            if subj.head_teacher_id is None and head_user is not None:
                subj.head_teacher_id = head_user.user_id
            summary["subjects_existing"] += 1
        subjects_by_name[subj.subject_name] = subj
    return subjects_by_name


def _seed_classes_rosters_and_links(
    session: Session,
    users_by_phone: Dict[str, User],
    subjects_by_name: Dict[str, Subject],
    summary: Dict[str, int],
) -> Dict[str, Class]:
    """Ensure classes across Grades 10-12, student rosters, and TeacherSubject links."""
    classes_by_name: Dict[str, Class] = {}

    for spec in CLASS_SPECS:
        cls = session.query(Class).filter(Class.class_name == spec["class_name"]).first()
        homeroom_phone = spec["homeroom_phone"]
        homeroom_user = users_by_phone.get(homeroom_phone) if homeroom_phone else None

        if cls is None:
            cls = Class(
                class_name=spec["class_name"],
                homeroom_teacher_id=homeroom_user.user_id if homeroom_user else None,
                academic_year=spec["academic_year"],
                status="ACTIVE",
            )
            session.add(cls)
            session.flush()
            summary["classes_created"] += 1
        else:
            if not spec["preserve_existing"] and (cls.status or "").upper() == "DELETED":
                cls.status = "ACTIVE"
            summary["classes_existing"] += 1

        classes_by_name[cls.class_name] = cls

        meta_key = f"__CLASS_META__:{cls.class_id}"
        if get_latest_state(session, meta_key) is None:
            upsert_state(
                session,
                meta_key,
                {"specialization": spec["specialization"]},
                actor_name="System",
            )

        if spec["code_prefix"]:
            for idx, student_phone in enumerate(spec["student_phones"], start=1):
                student_user = users_by_phone.get(student_phone)
                if student_user is None:
                    continue
                existing_link = (
                    session.query(StudentClass)
                    .filter(
                        StudentClass.student_id == student_user.user_id,
                        StudentClass.class_id == cls.class_id,
                    )
                    .first()
                )
                if existing_link is not None:
                    summary["enrollments_existing"] += 1
                    continue

                student_code = f"{spec['code_prefix']}-{idx:02d}"
                if session.query(StudentClass).filter(StudentClass.student_code == student_code).first():
                    student_code = f"{spec['code_prefix']}-{str(cls.class_id)[:4].upper()}-{idx:02d}"

                session.add(
                    StudentClass(
                        student_id=student_user.user_id,
                        class_id=cls.class_id,
                        student_code=student_code,
                        status="ACTIVE",
                    )
                )
                summary["enrollments_created"] += 1

    for teacher_phone, class_name, subject_name in TEACHER_SUBJECT_ASSIGNMENTS:
        teacher = users_by_phone.get(teacher_phone)
        cls = classes_by_name.get(class_name)
        subj = subjects_by_name.get(subject_name)
        if not (teacher and cls and subj):
            continue
        existing_ts = (
            session.query(TeacherSubject)
            .filter(
                TeacherSubject.teacher_id == teacher.user_id,
                TeacherSubject.class_id == cls.class_id,
                TeacherSubject.subject_id == subj.subject_id,
            )
            .first()
        )
        if existing_ts is None:
            session.add(
                TeacherSubject(
                    teacher_id=teacher.user_id,
                    class_id=cls.class_id,
                    subject_id=subj.subject_id,
                    status="ACTIVE",
                )
            )
            summary["teacher_subjects_created"] += 1
        else:
            summary["teacher_subjects_existing"] += 1

    session.flush()
    return classes_by_name


def _seed_approvals_tickets_and_logs(
    session: Session,
    admin_user: User,
    now: datetime,
    summary: Dict[str, int],
) -> None:
    """Seed ApprovalRequest, SupportTicket, and human-visible AuditLog records."""
    for spec in APPROVAL_REQUEST_SPECS:
        existing_req = (
            session.query(ApprovalRequest)
            .filter(
                ApprovalRequest.requester_name == spec["requester_name"],
                ApprovalRequest.type == spec["type"],
            )
            .first()
        )
        if existing_req is not None:
            summary["approvals_existing"] += 1
            continue

        is_reviewed = spec["status"] in ("approved", "rejected")
        created_at = now - timedelta(days=spec["days_ago"], hours=2)
        session.add(
            ApprovalRequest(
                requester_name=spec["requester_name"],
                requester_sub=spec["requester_sub"],
                avatar_text=spec["avatar_text"],
                avatar_bg=spec["avatar_bg"],
                is_system=False,
                type=spec["type"],
                status=spec["status"],
                reviewed_by=admin_user.user_id if is_reviewed else None,
                reviewed_at=now - timedelta(days=spec["days_ago"]) if is_reviewed else None,
                review_note=spec["review_note"],
                created_at=created_at,
                updated_at=created_at,
            )
        )
        summary["approvals_created"] += 1

    for spec in SUPPORT_TICKET_SPECS:
        existing_ticket = (
            session.query(SupportTicket)
            .filter(
                SupportTicket.phone == spec["phone"],
                SupportTicket.request_type == spec["request_type"],
            )
            .first()
        )
        if existing_ticket is not None:
            summary["tickets_existing"] += 1
            continue

        session.add(
            SupportTicket(
                full_name=spec["full_name"],
                phone=spec["phone"],
                request_type=spec["request_type"],
                message=spec["message"],
                status=spec["status"],
            )
        )
        summary["tickets_created"] += 1

    for idx, spec in enumerate(AUDIT_LOG_SPECS):
        existing_log = (
            session.query(AuditLog)
            .filter(
                AuditLog.title == spec["title"],
                AuditLog.ip_address != "INTERNAL_STATE",
            )
            .first()
        )
        if existing_log is not None:
            summary["audit_logs_existing"] += 1
            continue

        created_at = now - timedelta(days=spec["days_ago"], hours=(idx % 5) + 1)
        session.add(
            AuditLog(
                title=spec["title"],
                description=spec["description"],
                actor_name=spec["actor_name"],
                ip_address=spec["ip_address"],
                severity=spec["severity"],
                status="ACTIVE",
                created_at=created_at,
            )
        )
        summary["audit_logs_created"] += 1

    session.flush()


def _seed_questions_for_exercise(
    session: Session,
    exercise: Exercise,
    subject_name: str,
    is_ai: bool,
    summary: Dict[str, int],
) -> None:
    """Create 3 MultipleChoice questions with 4 AnswerOptions if none exist for exercise."""
    existing_count = session.query(Question).filter(Question.exercise_id == exercise.exercise_id).count()
    if existing_count > 0:
        return

    difficulties = ["Easy", "Medium", "Hard"]
    for order_idx, diff in enumerate(difficulties, start=1):
        q = Question(
            exercise_id=exercise.exercise_id,
            content=f"[{subject_name}] Câu hỏi {order_idx} ({diff}): Phân tích nội dung trọng tâm của '{exercise.title}'.",
            question_type="MultipleChoice",
            difficulty=diff,
            correct_answer="A",
            explanation=f"Phương án A thể hiện chính xác nguyên lý cốt lõi của chuyên đề {subject_name}.",
            display_order=order_idx,
            is_ai_generated=is_ai,
            needs_review=False,
            status="ACTIVE",
        )
        session.add(q)
        session.flush()
        summary["questions_created"] += 1

        option_texts = [
            f"Phương án A - Đáp án chuẩn cho câu {order_idx}",
            f"Phương án B - Biến thể gây nhiễu câu {order_idx}",
            f"Phương án C - Giả thiết chưa đầy đủ câu {order_idx}",
            f"Phương án D - Kết luận đảo ngược câu {order_idx}",
        ]
        for opt_idx, opt_text in enumerate(option_texts, start=1):
            session.add(
                AnswerOption(
                    question_id=q.question_id,
                    content=opt_text,
                    is_correct=(opt_idx == 1),
                    display_order=opt_idx,
                )
            )


def _seed_exercises_and_attempts(
    session: Session,
    subjects_by_name: Dict[str, Subject],
    classes_by_name: Dict[str, Class],
    users_by_phone: Dict[str, User],
    now: datetime,
    summary: Dict[str, int],
) -> None:
    """Seed AI and manual exercises across all 7 subjects, assignments, and finished attempts."""
    fallback_creator = users_by_phone["0999000002"]

    for spec in EXERCISE_SPECS:
        subj = subjects_by_name[spec["subject"]]
        cls = classes_by_name[spec["class_name"]]
        creator_id = subj.head_teacher_id or fallback_creator.user_id

        exercise = (
            session.query(Exercise)
            .filter(
                Exercise.title == spec["title"],
                Exercise.subject_id == subj.subject_id,
            )
            .first()
        )
        if exercise is None:
            ai_meta = (
                {"provider": "google_gemini", "model": "gemini-2.5-flash", "bloom_level": "Apply"}
                if spec["is_ai"]
                else None
            )
            exercise = Exercise(
                title=spec["title"],
                subject_id=subj.subject_id,
                created_by=creator_id,
                total_questions=3,
                ai_metadata=ai_meta,
                exercise_kind=spec["kind"],
                status="ACTIVE",
            )
            session.add(exercise)
            session.flush()
            summary["exercises_created"] += 1
        else:
            summary["exercises_existing"] += 1

        _seed_questions_for_exercise(session, exercise, spec["subject"], spec["is_ai"], summary)

        assignment = (
            session.query(ClassAssignment)
            .filter(
                ClassAssignment.class_id == cls.class_id,
                ClassAssignment.exercise_id == exercise.exercise_id,
            )
            .first()
        )
        if assignment is None:
            assignment = ClassAssignment(
                class_id=cls.class_id,
                exercise_id=exercise.exercise_id,
                assigned_by=creator_id,
                assigned_at=now - timedelta(days=spec["days_ago"] + 1),
                due_at=now + timedelta(days=7),
                status="ACTIVE",
            )
            session.add(assignment)
            session.flush()
            summary["assignments_created"] += 1
        else:
            summary["assignments_existing"] += 1

        class_enrollments = (
            session.query(StudentClass)
            .filter(
                StudentClass.class_id == cls.class_id,
                func.upper(StudentClass.status) != "DELETED",
            )
            .order_by(StudentClass.student_code.asc())
            .all()
        )
        for idx, score_val in enumerate(spec["scores"]):
            if idx >= len(class_enrollments):
                break
            student_id = class_enrollments[idx].student_id
            existing_attempt = (
                session.query(StudentExerciseAttempt)
                .filter(
                    StudentExerciseAttempt.student_id == student_id,
                    StudentExerciseAttempt.assignment_id == assignment.assignment_id,
                )
                .first()
            )
            if existing_attempt is not None:
                summary["attempts_existing"] += 1
                continue

            finish_time = now - timedelta(days=spec["days_ago"], hours=idx + 1)
            session.add(
                StudentExerciseAttempt(
                    student_id=student_id,
                    assignment_id=assignment.assignment_id,
                    start_time=finish_time - timedelta(minutes=22),
                    end_time=finish_time,
                    total_time_seconds=1320,
                    score=Decimal(f"{score_val:.2f}"),
                    detailed_results={
                        "correct_count": 3 if score_val >= 8.0 else 2,
                        "total_questions": 3,
                        "graded_by": "seed_admin_portal_data",
                    },
                    is_finished=True,
                    status="ACTIVE",
                    created_at=finish_time,
                    updated_at=finish_time,
                )
            )
            summary["attempts_created"] += 1

    session.flush()


def _seed_reports_settings_and_backups(
    session: Session,
    admin_user: User,
    now: datetime,
    summary: Dict[str, int],
) -> None:
    """Seed __SYS_SETTINGS__, __BACKUP_SNAPSHOT__, __REPORT_SCHEDULE__, and __CUSTOM_REPORT__ if absent."""
    if get_latest_state(session, "__SYS_SETTINGS__") is None:
        upsert_state(
            session,
            "__SYS_SETTINGS__",
            settings_router._default_settings_payload(),
            actor_name="System",
        )
        summary["settings_created"] += 1

    if not list_state_items(session, "__REPORT_SCHEDULE__"):
        schedule_specs = [
            {
                "title": "Báo cáo điểm trung bình toàn trường hàng tuần",
                "frequency": "weekly",
                "format": "xlsx",
                "metricType": "score",
                "recipients": ["admin@school.com", "headteacher1@school.com"],
                "grade": "all",
                "department": "all",
            },
            {
                "title": "Thống kê tỷ lệ hoàn thành bài tập theo khối",
                "frequency": "weekly",
                "format": "pdf",
                "metricType": "completion",
                "recipients": ["academicstaff1@school.com"],
                "grade": "12",
                "department": "all",
            },
            {
                "title": "Tổng hợp mức độ sử dụng AI tạo câu hỏi theo tổ bộ môn",
                "frequency": "monthly",
                "format": "csv",
                "metricType": "ai_adoption",
                "recipients": ["headteacher2@school.com", "admin@school.com"],
                "grade": "all",
                "department": "Toán học",
            },
        ]
        for spec in schedule_specs:
            append_state_item(
                session,
                "__REPORT_SCHEDULE__",
                {
                    **spec,
                    "enabled": True,
                    "status": "ACTIVE",
                    "createdBy": admin_user.full_name,
                },
                actor_name=admin_user.full_name,
            )
            summary["report_schedules_created"] += 1

    if not list_state_items(session, "__CUSTOM_REPORT__"):
        analytics = reports_router._compute_analytics(
            db=session,
            academic_year="2025-2026",
            semester="HK1",
            grade="all",
            department="all",
        )
        custom_specs = [
            {
                "title": "Báo cáo tổng hợp chất lượng học tập HK1",
                "metricType": "score",
                "format": "pdf",
                "frequency": "once",
            },
            {
                "title": "Phân tích hiệu quả ứng dụng AI theo 7 tổ bộ môn",
                "metricType": "ai_adoption",
                "format": "xlsx",
                "frequency": "monthly",
            },
            {
                "title": "Theo dõi chuyên cần và tiến độ hoàn thành bài tập Khối 10-12",
                "metricType": "completion",
                "format": "csv",
                "frequency": "weekly",
            },
        ]
        for spec in custom_specs:
            append_state_item(
                session,
                "__CUSTOM_REPORT__",
                {
                    **spec,
                    "status": "generated",
                    "createdBy": admin_user.full_name,
                    "summary": analytics["kpis"],
                },
                actor_name=admin_user.full_name,
            )
            summary["custom_reports_created"] += 1

    if not list_state_items(session, "__BACKUP_SNAPSHOT__"):
        table_counts = {
            "users": session.query(User).filter(func.upper(User.status) != "DELETED").count(),
            "roles": session.query(Role).count(),
            "permissions": session.query(Permission).count(),
            "classes": session.query(Class).filter(func.upper(Class.status) != "DELETED").count(),
            "subjects": session.query(Subject).filter(func.upper(Subject.status) != "DELETED").count(),
            "student_classes": session.query(StudentClass).filter(func.upper(StudentClass.status) != "DELETED").count(),
            "teacher_subjects": session.query(TeacherSubject).filter(func.upper(TeacherSubject.status) != "DELETED").count(),
            "documents": session.query(Document).filter(func.upper(Document.status) != "DELETED").count(),
            "exercises": session.query(Exercise).filter(func.upper(Exercise.status) != "DELETED").count(),
            "questions": session.query(Question).filter(func.upper(Question.status) != "DELETED").count(),
            "student_exercise_attempts": (
                session.query(StudentExerciseAttempt)
                .filter(func.upper(StudentExerciseAttempt.status) != "DELETED")
                .count()
            ),
            "audit_logs": session.query(AuditLog).filter(func.upper(AuditLog.status) != "DELETED").count(),
        }
        current_settings = settings_router._load_settings(session)
        for day_offset in (2, 1, 0):
            snap_time = now - timedelta(days=day_offset)
            snapshot_doc = {
                "generated_at": snap_time.isoformat(),
                "created_by": admin_user.full_name,
                "table_counts": table_counts,
                "settings": current_settings,
            }
            raw_bytes = json.dumps(snapshot_doc, ensure_ascii=False, indent=2).encode("utf-8")
            filename = f"smartlms_backup_{snap_time.strftime('%Y%m%d_%H%M%S')}.json"
            append_state_item(
                session,
                "__BACKUP_SNAPSHOT__",
                {
                    "filename": filename,
                    "size": settings_router._format_size(len(raw_bytes)),
                    "byte_size": len(raw_bytes),
                    "createdAt": snap_time.isoformat(),
                    "status": "completed",
                    "createdBy": admin_user.full_name,
                    "table_counts": table_counts,
                    "snapshot": snapshot_doc,
                },
                actor_name=admin_user.full_name,
            )
            summary["backups_created"] += 1


def _sync_seed_accounts_info(
    managed_records: List[Dict[str, Any]],
) -> int:
    """Merge seeded special, inactive, and unassigned accounts into seed_accounts_info.json."""
    existing_items: List[Dict[str, Any]] = []
    if ACCOUNTS_INFO_PATH.exists():
        existing_items = json.loads(ACCOUNTS_INFO_PATH.read_text(encoding="utf-8"))

    by_phone: Dict[str, int] = {
        item["phone"]: idx for idx, item in enumerate(existing_items) if item.get("phone")
    }
    updated_items = [dict(item) for item in existing_items]
    changed_count = 0

    for record in managed_records:
        phone = record["phone"]
        if phone in by_phone:
            idx = by_phone[phone]
            merged = {**updated_items[idx], **record}
            if merged != updated_items[idx]:
                updated_items[idx] = merged
                changed_count += 1
        else:
            by_phone[phone] = len(updated_items)
            updated_items.append(record)
            changed_count += 1

    if changed_count > 0 or not ACCOUNTS_INFO_PATH.exists():
        ACCOUNTS_INFO_PATH.write_text(
            json.dumps(updated_items, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    return changed_count


def seed_admin_portal_data(
    session: Optional[Session] = None,
    sync_accounts_json: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Idempotently seed all Admin Portal demo/verification data across roles, users,
    classes, enrollments, approvals, tickets, audit logs, exercises, reports, and settings.
    """
    owns_session = session is None
    if owns_session:
        session = SessionLocal()

    should_sync_json = owns_session if sync_accounts_json is None else sync_accounts_json

    summary: Dict[str, int] = {
        "users_created": 0,
        "users_existing": 0,
        "users_backfilled_birthday": 0,
        "users_backfilled_gender": 0,
        "subjects_created": 0,
        "subjects_existing": 0,
        "classes_created": 0,
        "classes_existing": 0,
        "enrollments_created": 0,
        "enrollments_existing": 0,
        "teacher_subjects_created": 0,
        "teacher_subjects_existing": 0,
        "approvals_created": 0,
        "approvals_existing": 0,
        "tickets_created": 0,
        "tickets_existing": 0,
        "audit_logs_created": 0,
        "audit_logs_existing": 0,
        "exercises_created": 0,
        "exercises_existing": 0,
        "questions_created": 0,
        "assignments_created": 0,
        "assignments_existing": 0,
        "attempts_created": 0,
        "attempts_existing": 0,
        "settings_created": 0,
        "report_schedules_created": 0,
        "custom_reports_created": 0,
        "backups_created": 0,
        "accounts_json_updates": 0,
    }

    try:
        now = datetime.now(timezone.utc)
        seed_rbac(session)
        _ensure_seeded(session)
        all_roles = session.query(Role).all()
        roles_map = {role.name: role for role in all_roles}
        roles_by_id = {role.role_id: role for role in all_roles}

        users_by_phone: Dict[str, User] = {}
        managed_json_records: List[Dict[str, Any]] = []

        for spec in BASE_STAFF_SPECS + SPECIAL_ROLE_ACCOUNTS + INACTIVE_ACCOUNTS:
            user = _get_or_create_user(session, spec, roles_map, summary)
            users_by_phone[user.phone] = user
            if spec in SPECIAL_ROLE_ACCOUNTS or spec in INACTIVE_ACCOUNTS:
                managed_json_records.append(
                    {
                        "user_id": str(user.user_id),
                        "phone": user.phone,
                        "email": user.email,
                        "full_name": user.full_name,
                        "role_name": spec["role_name"],
                        "status": user.status,
                        "password_plain": spec["password_plain"],
                    }
                )

        for spec in UNASSIGNED_STUDENTS:
            full_spec = {
                **spec,
                "role_name": "Student",
                "password_plain": "Student@1234",
                "birthday": date(2008, 4, 15),
                "status": "ACTIVE",
            }
            user = _get_or_create_user(session, full_spec, roles_map, summary)
            users_by_phone[user.phone] = user
            managed_json_records.append(
                {
                    "user_id": str(user.user_id),
                    "phone": user.phone,
                    "email": user.email,
                    "full_name": user.full_name,
                    "role_name": "Student",
                    "status": user.status,
                    "password_plain": "Student@1234",
                }
            )

        for idx, spec in enumerate(FALLBACK_ROSTER_STUDENT_SPECS):
            existing_student = session.query(User).filter(User.phone == spec["phone"]).first()
            if existing_student is not None:
                users_by_phone[existing_student.phone] = existing_student
                summary["users_existing"] += 1
            else:
                full_spec = {
                    **spec,
                    "role_name": "Student",
                    "password_plain": "Student@1234",
                    "birthday": date(2008, (idx % 12) + 1, (idx % 25) + 1),
                    "status": "ACTIVE",
                }
                user = _get_or_create_user(session, full_spec, roles_map, summary)
                users_by_phone[user.phone] = user

        _backfill_seeded_users(session, roles_by_id, summary)
        subjects_by_name = _seed_subjects(session, users_by_phone, summary)
        classes_by_name = _seed_classes_rosters_and_links(
            session, users_by_phone, subjects_by_name, summary
        )

        admin_user = users_by_phone["0999000001"]
        _seed_approvals_tickets_and_logs(session, admin_user, now, summary)
        _seed_exercises_and_attempts(
            session, subjects_by_name, classes_by_name, users_by_phone, now, summary
        )
        _seed_reports_settings_and_backups(session, admin_user, now, summary)

        session.commit()

        if should_sync_json:
            summary["accounts_json_updates"] = _sync_seed_accounts_info(managed_json_records)

        logger.info("Admin portal seed completed: %s", summary)
        return summary
    except Exception:
        session.rollback()
        logger.exception("Admin portal seed failed; rolled back transaction.")
        raise
    finally:
        if owns_session:
            session.close()


def main() -> None:
    """CLI entrypoint for running Admin Portal seed script."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    # The seed creates accounts with known demo passwords; never run it against production.
    if os.getenv("APP_ENV", "").strip().lower() in ("prod", "production"):
        raise SystemExit("Refusing to seed demo accounts when APP_ENV is production.")
    result = seed_admin_portal_data()
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
