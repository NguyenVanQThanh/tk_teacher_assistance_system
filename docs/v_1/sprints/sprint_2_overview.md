# Sprint 2 — Bài tập lõi, Khảo thí & AI Gemini Vision OCR (Exercise Core & OCR)

> Path: `docs/v_1/sprints/sprint_2_overview.md` · Module(s): `exercise`
> Created At: `2026-07-28`
> Created By: `Tam Khang`
> Updated At: `2026-10-27`
> Updated By: `Tam Khang`

## Mục tiêu Sprint

Xây tầng nghiệp vụ **bài tập lõi, khảo thí và bóc tách đề thi bằng AI OCR** trên schema từ `docs/base_sql_erd.sql` nhóm 3 & 4 (`exercises`, `questions`, `answer_options`, `class_assignments`, `student_exercise_attempts`), làm nền dữ liệu cho các phân hệ Quản trị, Học liệu, Thời khóa biểu và Phân tích ở Sprint 3 & Sprint 4.

Kết thúc Sprint 2, hệ thống cho phép: Giáo viên tạo/sửa/xóa mềm/khôi phục đề bài tập kèm câu hỏi & đáp án; nhập hàng loạt câu hỏi từ file `.docx`/`.pdf` kết hợp **AI Google Gemini Multimodal Vision OCR (`F-EXE-06`)**; xuất đề thi ra PDF (`/export/pdf`); phân trang con trỏ (Keyset Cursor Pagination); Giáo viên giao bài tập cho lớp mình phụ trách kèm hạn nộp; Học sinh xem bài được giao, bắt đầu làm bài toàn màn hình và nộp bài; hệ thống tự động chấm điểm câu hỏi trắc nghiệm và hỗ trợ giáo viên cập nhật điểm/nhận xét (`/grade`).

| Field | Giá trị |
|---|---|
| Sprint | `SPRINT-02` |
| Status | `done` |
| Stack | FastAPI · SQLAlchemy 2.0 · PostgreSQL · Alembic · Google Gemini Vision (`google-genai`, `pypdfium2`) |
| Phụ thuộc | `F-ACAD-01..04` (Sprint 1 — cần `subjects`, `classes`, `teacher_subjects`, `student_class` để scoping quyền tạo/giao/làm bài) |

## Quyết định scope (assumptions)

| # | Quyết định | Lý do |
|---|---|---|
| AS-01 | Giáo viên chỉ được tạo/sửa đề bài tập (`exercises`) thuộc môn học mình được phân công dạy (`teacher_subjects`), không giới hạn theo lớp cụ thể — đề có thể tái sử dụng cho nhiều lớp. | Khớp thiết kế bảng `exercises.subject_id` + `class_assignments` là bảng giao bài riêng, tách khỏi đề. |
| AS-02 | `class_assignments` chỉ được tạo bởi giáo viên đang dạy môn đó ở đúng lớp đó (`teacher_subjects` match `class_id` + `subject_id` của đề). | Đảm bảo GV không giao bài ngoài phạm vi giảng dạy — nối tiếp RBAC Data Scoping của Sprint 1. |
| AS-03 | Một học sinh chỉ có **1 attempt đang mở** (`is_finished = false`) cho mỗi `assignment_id`; nộp bài xong không được làm lại (không hỗ trợ resubmit ở Sprint 2). | Đơn giản hóa nghiệp vụ, tránh xung đột dữ liệu chấm điểm; retry là out of scope. |
| AS-04 | Chấm điểm tự động cho câu trắc nghiệm và hỗ trợ giáo viên cập nhật điểm số & nhận xét qua `PUT /api/v1/attempts/{attempt_id}/grade`. | Kết hợp tự động hóa chấm điểm khách quan và quyền điều chỉnh của giáo viên. |
| AS-05 | Tái sử dụng field `status` (`ACTIVE`/`INACTIVE`/`DRAFT`/`DELETED`) cho `exercises`, `questions`, `class_assignments`, `student_exercise_attempts`. | Nhất quán soft-delete/restore pattern theo Quy tắc 6 (`Soft Delete Policy`). |
| AS-06 | Import câu hỏi (`F-EXE-05` & `F-EXE-06`) ưu tiên sử dụng **Gemini Multimodal Vision OCR** để bóc tách công thức LaTeX, bảng biến thiên, đồ thị và 3 phần câu hỏi; tự động fallback về bộ parser regex/pdfplumber khi không có API key. | Đạt độ chính xác cao với đề thi Toán/KHTN phức tạp đồng thời đảm bảo tính sẵn sàng. |
| AS-07 | Import là **all-or-nothing**: nếu có bất kỳ câu nào sai định dạng, toàn bộ file bị từ chối (không insert một phần), trả về danh sách lỗi kèm số dòng/số câu. | Tránh đề bài tập bị thiếu câu hỏi âm thầm. |

## Features trong Sprint

| Feature ID | Tên | Module | Spec | Status |
|---|---|---|---|---|
| `F-EXE-01` | Exercise Bank (Đề bài tập, câu hỏi & đáp án, Keyset Pagination, PDF Export) | `exercise` | [f_exe_01_exercises_spec.md](../specs/f_exe_01_exercises_spec.md) | `done` |
| `F-EXE-02` | Class Assignments (Giao bài cho lớp) | `exercise` | [f_exe_02_assignments_spec.md](../specs/f_exe_02_assignments_spec.md) | `done` |
| `F-EXE-03` | Student Submission (Làm bài & nộp bài) | `exercise` | [f_exe_03_submission_spec.md](../specs/f_exe_03_submission_spec.md) | `done` |
| `F-EXE-04` | Auto Grading & Teacher Grade Update (Chấm điểm tự động & GV cập nhật điểm) | `exercise` | [f_exe_04_grading_spec.md](../specs/f_exe_04_grading_spec.md) | `done` |
| `F-EXE-05` | Question Import (Nhập câu hỏi từ file docx/pdf theo template) | `exercise` | [f_exe_05_question_import_spec.md](../specs/f_exe_05_question_import_spec.md) | `done` |
| `F-EXE-06` | AI Gemini Vision OCR (Bóc tách đề thi Toán/KHTN đa phương thức) | `exercise` | [f_exe_06_gemini_vision_ocr_spec.md](../specs/f_exe_06_gemini_vision_ocr_spec.md) | `done` |

## Thứ tự thực thi

```
F-EXE-01 (exercises + questions + answer_options CRUD & Restore + Keyset Pagination + PDF Export)
  ├── F-EXE-02 (class_assignments — giao bài, cần exercise tồn tại + teacher_subjects scoping)
  │     └── F-EXE-03 (student_exercise_attempts — start/submit, cần assignment tồn tại + student_class scoping)
  │           └── F-EXE-04 (auto grading + teacher grade override)
  └── F-EXE-05 & F-EXE-06 (question import + Gemini Multimodal Vision OCR)
```

## Definition of Done — Sprint 2

| ✓ | Tiêu chí | Status |
|---|---|---|
| [x] | Alembic migration mới thêm cột `status` cho `exercises` + bảng `answer_options` | `done` |
| [x] | `POST/GET/PUT/DELETE/RESTORE /api/v1/exercises` — CRUD & Restore đề bài tập, scoping theo `teacher_subjects`, Keyset Cursor Pagination & PDF Export (`/export/pdf`) | `done` |
| [x] | `POST /api/v1/exercises/{exercise_id}/questions` & `PUT/DELETE /api/v1/questions/{question_id}` — CRUD câu hỏi + đáp án lồng trong đề | `done` |
| [x] | `POST/GET /api/v1/classes/{class_id}/assignments` & `DELETE/RESTORE /api/v1/assignments/{assignment_id}` — giao/hủy/khôi phục giao bài tập cho lớp, validate GV đúng môn+lớp | `done` |
| [x] | `POST /api/v1/assignments/{assignment_id}/attempts` — HS bắt đầu làm bài, validate ghi danh lớp + role Student | `done` |
| [x] | `PUT /api/v1/attempts/{attempt_id}/submit` — HS nộp bài, trigger chấm điểm tự động trắc nghiệm | `done` |
| [x] | `GET /api/v1/attempts` & `GET /api/v1/attempts/{attempt_id}` & `PUT /api/v1/attempts/{attempt_id}/grade` — xem kết quả và GV chấm/sửa điểm theo RBAC Data Scoping | `done` |
| [x] | Seed permission mới `EXE_*` (`EXE_EXERCISE_MANAGE/VIEW`, `EXE_ASSIGNMENT_MANAGE/VIEW`, `EXE_ATTEMPT_SUBMIT/VIEW`, `EXE_QUESTION_IMPORT`), map cho role Teacher/Student tương ứng | `done` |
| [x] | `POST /api/v1/exercises/{exercise_id}/questions/import` — nhập hàng loạt câu hỏi từ file `.docx`/`.pdf` kết hợp AI Gemini Vision OCR (`F-EXE-06`) và parser fallback, all-or-nothing | `done` |
| [x] | `pytest tests` pass 100% cho module `exercise` | `done` |
| [x] | Specs `F-EXE-01..06` cập nhật theo thực tế triển khai | `done` |
| ☐ | Refactor: đồng bộ convention khai báo Service trong router — chuyển 4 router + 4 service của `academic` sang instance + `Depends(get_xxx_service)` để khớp `exercise` | `pending` |
| ☐ | Refactor: dịch toàn bộ comment/docstring tiếng Việt sang Standard English trong 4 router `academic` (`classes.py`, `enrollments.py`, `subjects.py`, `teacher_assignments.py`) | `pending` |

## Trạng thái Đồng bộ API Backend ↔ Frontend (`exercise`)

| Method & Endpoint | Backend | Khai báo `api.js` | Màn hình Frontend sử dụng | Trạng thái Sync |
|---|---|---|---|---|
| `GET /api/v1/exercises`<br>`GET /api/v1/exercises/{id}`<br>`POST /api/v1/exercises`<br>`PUT /api/v1/exercises/{id}`<br>`DELETE /api/v1/exercises/{id}` | ✅ Đã có | `exercisesApi.*` | `ExerciseRepositoryPage`, `CreateExerciseManualPage`, `CreateExerciseModal`, `ExercisePreviewModal`, `StudentExerciseTakingPage` | ⚠️ Đã đồng bộ; riêng nút "Sửa" trên thẻ ở `ExerciseRepositoryPage.jsx` đang mở `EditDocumentModal` (mock 5 câu) và chưa gọi `updateExercise` |
| `POST /api/v1/exercises/{id}/restore` | ✅ Đã có | ❌ Chưa khai báo | Chưa có nút khôi phục bài tập trên UI | ⚠️ Đã có BE, thiếu ở `api.js` & FE |
| `GET /api/v1/exercises/{id}/export/pdf` | ✅ Đã có | `exercisesApi.exportPdf` | `ExercisePreviewModal.jsx` | ✅ Đã đồng bộ |
| `POST /api/v1/exercises/{id}/questions/import` | ✅ Đã có | `exercisesApi.importQuestions` | `CreateExerciseModal.jsx` (Nhánh Upload file đề + đáp án) | ✅ Đã đồng bộ |
| `POST /api/v1/exercises/{id}/questions` | ✅ Đã có | `exercisesApi.addQuestion` | `CreateExerciseManualPage.jsx` | ✅ Đã đồng bộ |
| `PUT /api/v1/questions/{id}`<br>`DELETE /api/v1/questions/{id}` | ✅ Đã có | `questionsApi.updateQuestion`<br>`questionsApi.deleteQuestion` | `ExercisePreviewModal.jsx` | ✅ Đã đồng bộ |
| `POST /api/v1/classes/{id}/assignments`<br>`GET /api/v1/classes/{id}/assignments`<br>`DELETE /api/v1/assignments/{id}` | ✅ Đã có | `assignmentsApi.createAssignment`<br>`assignmentsApi.getClassAssignments`<br>`assignmentsApi.deleteAssignment` | `AssignExerciseModal.jsx`, `ExercisePreviewModal.jsx`, `TeacherClassDetailPage.jsx`, `StudentExercisesPage.jsx` | ✅ Đã đồng bộ |
| `POST /api/v1/assignments/{id}/restore` | ✅ Đã có | `assignmentsApi.restoreAssignment` | Đã có trong `api.js`, chưa gắn nút trên UI | ⚠️ Chưa gắn nút UI |
| `POST /api/v1/assignments/{id}/attempts`<br>`PUT /api/v1/attempts/{id}/submit`<br>`GET /api/v1/attempts`<br>`GET /api/v1/attempts/{id}`<br>`PUT /api/v1/attempts/{id}/grade` | ✅ Đã có | `attemptsApi.*` | `StudentExerciseTakingPage.jsx`, `StudentExercisesPage.jsx`, `TeacherGradingPage.jsx`, `GradingFeedbackModal.jsx` | ⚠️ Đã đồng bộ luồng chính; riêng `TeacherGradingPage` đang trộn thêm 15 bài nộp mock, và tính năng "Cascade Regrade" khi sửa đáp án gốc ở `GradingFeedbackModal` mới chỉ xử lý trên state FE |
| `POST /api/v1/exercises/generate-ai` *(Sinh câu hỏi từ Prompt / Tài liệu bằng AI)* | ❌ Chưa có ở BE | ❌ Chưa khai báo | `CreateExerciseModal.jsx` (nhánh AI) & `StudentExercisesPage.jsx` (AI Practice Generator) đang chạy `setTimeout` + `localStorage` | ❌ Thiếu API ở BE |

## Catalogs khởi tạo trong Sprint này

- Permission mới: `EXE_EXERCISE_MANAGE`, `EXE_EXERCISE_VIEW`, `EXE_ASSIGNMENT_MANAGE`, `EXE_ASSIGNMENT_VIEW`, `EXE_ATTEMPT_SUBMIT`, `EXE_ATTEMPT_VIEW`, `EXE_QUESTION_IMPORT`.
- Error code mới `ERR-EXE-*` (xem chi tiết từng spec §PART A workflow), gồm `ERR-EXE-EXERCISE_NOT_FOUND`, `ERR-EXE-QUESTION_NOT_FOUND`, `ERR-EXE-INVALID_SUBJECT_SCOPE`, `ERR-EXE-ASSIGNMENT_NOT_FOUND`, `ERR-EXE-CLASS_ACCESS_DENIED`, `ERR-EXE-DUPLICATE_ASSIGNMENT`, `ERR-EXE-ATTEMPT_ALREADY_OPEN`, `ERR-EXE-ATTEMPT_ALREADY_SUBMITTED`, `ERR-EXE-ATTEMPT_NOT_FOUND`, `ERR-EXE-STUDENT_NOT_ENROLLED`, `ERR-EXE-IMPORT_FILE_TYPE_UNSUPPORTED`, `ERR-EXE-IMPORT_PARSE_FAILED`, `ERR-EXE-IMPORT_INVALID_QUESTION`.
