> Path: `docs/tasks/f_acad_05/f_acad_05_teacher_schedule.md`
> Slice: `SL-ACAD-05` · Type: `feature` · Size: `large` · SP: `5`
> Depends on: `F-ACAD-02`, `F-ACAD-04`
> Status: `ready to test`
> Created At: `2026-10-27`
> Updated At: `2026-10-28`

# Task — `F-ACAD-05` Teacher Schedule & Timetable (Thời khóa biểu & Lịch Giảng dạy Giáo viên)

**Created By:** Tam Khang  
**Updated By:** Tam Khang  

## Mô tả Task
Triển khai phân hệ Quản lý Thời khóa biểu, Lịch Giảng dạy và Ghi chú công việc sư phạm cho Giáo viên (`/api/v1/teacher/schedules` & `/api/v1/teacher/notes`):
1. Alembic Migration: Tạo bảng `teacher_schedules` và `teacher_notes` với cột `status` (`ACTIVE`, `INACTIVE`, `DELETED`) tuân thủ Soft Delete Policy.
2. Service Layer (`TeacherScheduleService`):
   - Kiểm tra xung đột khung giờ giảng dạy của giáo viên (`ERR-SCHED-TIME_CONFLICT`) và xung đột phòng học (`ERR-SCHED-ROOM_OCCUPIED`).
   - Hỗ trợ 5 mức độ ưu tiên (`critical`, `high`, `teaching`, `ai`, `meeting`).
   - CRUD, Soft Delete & Restore cho lịch dạy và ghi chú công việc theo ngày.
3. Tích hợp Frontend: Khai báo `scheduleApi` trong `frontend/src/services/api.js` và nối vào `TeacherSchedulePage.jsx`, `TeachingScheduleCard.jsx`, `TeacherScheduleCalendarCard.jsx`, `DailyScheduleDetailCard.jsx`.

## Checklist Thực Hiện
- [x] Tạo Alembic migration cho `teacher_schedules` và `teacher_notes`.
- [x] Seed permissions `SCHED_TEACHER_MANAGE` và `SCHED_TEACHER_VIEW`.
- [x] Xây dựng 11 endpoints cho lịch giảng dạy và ghi chú công việc.
- [x] Cập nhật `frontend/src/services/api.js` và nối với `TeacherSchedulePage.jsx`.
- [x] Viết Unit & Integration Tests (`pytest tests/academic/test_schedules.py`) đạt 100% pass rate.

