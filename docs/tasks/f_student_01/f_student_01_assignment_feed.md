> Path: `docs/tasks/f_student_01/f_student_01_assignment_feed.md`
> Slice: `SL-STUDENT-01` · Type: `feature` · Size: `medium` · SP: `3`
> Depends on: `F-EXE-02`, `F-EXE-03`
> Status: `ready to test`
> Created At: `2026-10-27`
> Updated At: `2026-10-28`

# Task — `F-STUDENT-01` Student Unified Assignment Feed (Cổng Bài tập Tập trung cho Học sinh)

**Created By:** Tam Khang  
**Updated By:** Tam Khang  

## Mô tả Task
Triển khai endpoint hợp nhất `GET /api/v1/student/assignments` giúp Học sinh tải toàn bộ danh sách bài tập từ tất cả các lớp đang theo học trong một truy vấn duy nhất (thay thế cơ chế gọi vòng N+1 ở `StudentExercisesPage.jsx`):
1. Pydantic Schemas: `StudentAssignmentFeedItemOut`, `PaginatedStudentAssignmentFeedOut`.
2. Query Service: Thực hiện SQL `JOIN` tối ưu giữa `student_class`, `class_assignments`, `exercises`, `subjects`, `classes`, `users` (giáo viên giao bài) và `student_exercise_attempts`.
3. Tính toán tự động trạng thái làm bài (`NOT_STARTED`, `IN_PROGRESS`, `SUBMITTED`, `GRADED`, `OVERDUE`), số lần làm (`attempts_count`), điểm cao nhất (`highest_score`) và `latest_attempt_id`.
4. Tích hợp Frontend: Khai báo `studentApi.getAssignments` trong `frontend/src/services/api.js` và kết nối vào `StudentExercisesPage.jsx` cùng `PendingStudentAssignmentsCard.jsx`.

## Checklist Thực Hiện
- [x] Seed permission `STUDENT_ASSIGNMENT_VIEW` cho role `Student`.
- [x] Xây dựng service và endpoint `GET /api/v1/student/assignments`.
- [x] Cập nhật `frontend/src/services/api.js` và refactor `StudentExercisesPage.jsx` + `PendingStudentAssignmentsCard.jsx`.
- [x] Viết Integration Tests kiểm tra lọc theo `status`, `subject_id` và phân trang.

