> Path: `docs/tasks/f_dash_01/f_dash_01_teacher_dashboard.md`
> Slice: `SL-DASH-01` · Type: `feature` · Size: `medium` · SP: `5`
> Depends on: `F-EXE-03`, `F-EXE-04`, `F-ACAD-05`
> Status: `ready to test`
> Created At: `2026-10-27`
> Updated At: `2026-10-28`

# Task — `F-DASH-01` Teacher Analytics Dashboard (Bảng điều khiển Phân tích cho Giáo viên)

**Created By:** Tam Khang  
**Updated By:** Tam Khang  

## Mô tả Task
Hoàn thiện đặc tả API (PART B của `f_dash_01_teacher_dashboard_spec.md`) và triển khai các API thống kê phục vụ `HomeroomTeacherDashboard.jsx` và `SubjectTeacherDashboard.jsx`:
1. Thống kê số lượng bài tập đang chờ chấm (`pending_grading`), số lớp dạy trong ngày và danh sách bài nộp gần đây (`RecentSubmissionsTable.jsx`, `PendingGradingCard.jsx`).
2. Tính toán dữ liệu biểu đồ mạng nhện (Radar Chart 6 trục) đánh giá chất lượng học tập trung bình của lớp và nhận xét sư phạm (`LearningQualityCard.jsx`).
3. Thống kê điểm trung bình (GPA) và điểm bộ môn thực tế của học sinh trong lớp chủ nhiệm (`TeacherHomeroomPage.jsx`, `TeacherClassDetailPage.jsx`), phát hiện học sinh nộp bài sát giờ (last-minute submission).

## Checklist Thực Hiện
- [x] Bổ sung PART B (API Contracts) vào `docs/v_1/specs/f_dash_01_teacher_dashboard_spec.md`.
- [x] Xây dựng `TeacherAnalyticsService` và các endpoints `/api/v1/teacher/dashboard/*`.
- [x] Cập nhật `frontend/src/services/api.js` và tích hợp vào `HomeroomTeacherDashboard.jsx`, `SubjectTeacherDashboard.jsx`, `TeacherHomeroomPage.jsx`.
- [x] Viết Unit & Integration Tests cho module phân tích giáo viên.

