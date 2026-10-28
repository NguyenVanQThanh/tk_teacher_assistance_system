> Path: `docs/tasks/f_dash_02/f_dash_02_student_dashboard.md`
> Slice: `SL-DASH-02` · Type: `feature` · Size: `medium` · SP: `5`
> Depends on: `F-EXE-03`, `F-STUDENT-01`
> Status: `ready to test`
> Created At: `2026-10-27`
> Updated At: `2026-10-28`

# Task — `F-DASH-02` Student Self-Evaluation Dashboard & AI Practice (Dashboard Tự đánh giá & Sinh đề AI)

**Created By:** Tam Khang  
**Updated By:** Tam Khang  

## Mô tả Task
Hoàn thiện đặc tả API (PART B của `f_dash_02_student_dashboard_spec.md`) và triển khai các API phục vụ `StudentDashboard.jsx` và công cụ sinh đề tự luyện AI:
1. API tổng hợp biểu đồ mạng nhện đa môn và 6 kỹ năng nhận thức theo từng môn học (`StudentRadarCard.jsx`, `StudentSubjectRadarModal.jsx`).
2. API lấy nhận xét đánh giá năng lực học tập của học sinh từ giáo viên và hệ thống (`TeacherFeedbackNoteCard.jsx`) cùng lịch học tập của học sinh (`StudentScheduleCard.jsx`, `StudentScheduleDetailCard.jsx`).
3. API `POST /api/v1/exercises/generate-ai` sử dụng Gemini để sinh câu hỏi tự luyện tập theo chủ đề và ma trận nhận thức (Nhận biết, Thông hiểu, Vận dụng) cho cả Học sinh (`StudentExercisesPage.jsx`) và Giáo viên (`CreateExerciseModal.jsx`).

## Checklist Thực Hiện
- [x] Bổ sung PART B (API Contracts) vào `docs/v_1/specs/f_dash_02_student_dashboard_spec.md`.
- [x] Xây dựng `StudentAnalyticsService` và `AiQuestionGeneratorService`.
- [x] Cập nhật `frontend/src/services/api.js` và tích hợp vào `StudentDashboard.jsx`, `StudentExercisesPage.jsx`, `CreateExerciseModal.jsx`.
- [x] Viết Unit & Integration Tests đạt 100% pass rate.

