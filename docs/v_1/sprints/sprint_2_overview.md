# Sprint 2 — Bài tập lõi (Exercise Core)

Path: `docs/v_1/sprints/sprint_2_overview.md` · Module(s): `exercise`
Created At: `2026-07-28`
Created By: `AI Agent`
Updated At: `2026-07-28`
Updated By: `AI Agent`

## Mục tiêu Sprint

Xây tầng nghiệp vụ **bài tập lõi** trên schema đã có từ `docs/base_sql_erd.sql` nhóm 3 & 4 (`exercises`, `questions`, `answer_options`, `class_assignments`, `student_exercise_attempts`), làm nền dữ liệu cho Module 1 (Tracking, Sprint 3) và Module 2 (AI Generation, Sprint 4).

Kết thúc Sprint 2, hệ thống cho phép: Giáo viên tạo/sửa/xóa mềm/khôi phục đề bài tập kèm câu hỏi & đáp án; Giáo viên giao bài tập cho lớp mình phụ trách kèm hạn nộp; Học sinh xem bài được giao, bắt đầu làm bài và nộp bài; hệ thống tự động chấm điểm câu hỏi trắc nghiệm (`MultipleChoice`) ngay khi nộp bài. Câu hỏi tự luận (`ShortAnswer`) được lưu nhưng **chưa** chấm tự động (out of scope Sprint 2 — cần AI/GV chấm, thuộc Sprint 4/5).

**Không thuộc phạm vi Sprint 2** (deferred):
- `documents` (upload tài liệu nguồn) — thuộc Module 2 AI Generation, Sprint 4.
- `behavior_logs`, `focus_score`, thống kê tần suất truy cập — thuộc Module 1 Tracking, Sprint 3. Sprint 2 chỉ ghi `start_time`/`end_time`/`total_time_seconds` ở mức tối thiểu để Sprint 3 có cột sẵn dùng.
- Chấm điểm tự luận bằng AI hoặc GV — thuộc Sprint 4/5.

| Field | Giá trị |
|---|---|
| Sprint | `SPRINT-02` |
| Status | `planning` |
| Stack | FastAPI · SQLAlchemy 2.0 · PostgreSQL · Alembic |
| Phụ thuộc | `F-ACAD-01..04` (Sprint 1 — cần `subjects`, `classes`, `teacher_subjects`, `student_class` để scoping quyền tạo/giao/làm bài) |

## Quyết định scope (assumptions)

| # | Quyết định | Lý do |
|---|---|---|
| AS-01 | Giáo viên chỉ được tạo/sửa đề bài tập (`exercises`) thuộc môn học mình được phân công dạy (`teacher_subjects`), không giới hạn theo lớp cụ thể — đề có thể tái sử dụng cho nhiều lớp. | Khớp thiết kế bảng `exercises.subject_id` + `class_assignments` là bảng giao bài riêng, tách khỏi đề. |
| AS-02 | `class_assignments` chỉ được tạo bởi giáo viên đang dạy môn đó ở đúng lớp đó (`teacher_subjects` match `class_id` + `subject_id` của đề). | Đảm bảo GV không giao bài ngoài phạm vi giảng dạy — nối tiếp RBAC Data Scoping của Sprint 1. |
| AS-03 | Một học sinh chỉ có **1 attempt đang mở** (`is_finished = false`) cho mỗi `assignment_id`; nộp bài xong không được làm lại (không hỗ trợ resubmit ở Sprint 2). | Đơn giản hóa nghiệp vụ, tránh xung đột dữ liệu chấm điểm; retry là out of scope. |
| AS-04 | Chấm điểm tự động chỉ áp dụng cho `question_type = 'MultipleChoice'` bằng so khớp `answer_options.is_correct`. Câu `ShortAnswer` lưu `correct_answer` nhưng field `score` của attempt chỉ tính trên phần trắc nghiệm đã chấm được, `detailed_results` đánh dấu câu tự luận `pending_manual_grade: true`. | Chấm tự luận cần AI/GV, chưa có ở Sprint 2 — tránh chấm sai/chấm giả. |
| AS-05 | Tái sử dụng field `status` (`ACTIVE`/`INACTIVE`/`DRAFT`/`DELETED`) cho `exercises` giống pattern `AcademicStatusEnum` của Sprint 1 (cột `status` chưa có trong `base_sql_erd.sql` gốc cho `exercises` → bổ sung qua Alembic migration mới theo Section 7 coding rules). `DRAFT` dùng khi GV đang soạn câu hỏi chưa hoàn chỉnh, chưa thể giao bài. | Nhất quán soft-delete/restore pattern đã dùng ở `academic` module. |
| AS-06 | Import câu hỏi (`F-EXE-05`) chỉ hỗ trợ file theo **template cố định** (docx: mỗi câu bắt đầu `Câu N.`, đáp án đúng đánh dấu `*` đầu dòng; pdf: cùng cú pháp, parse text thuần). Không dùng AI/NLP để hiểu file tự do. | File tự do (giáo án, PDF phức tạp) cần AI trích xuất ngữ nghĩa — thuộc Module 2 AI Generation (Sprint 4), không lặp lại phạm vi đó ở Sprint 2. |
| AS-07 | Import là **all-or-nothing**: nếu có bất kỳ câu nào sai template (thiếu đáp án đúng, sai định dạng), toàn bộ file bị từ chối (không insert một phần), trả về danh sách lỗi kèm số dòng/số câu. | Tránh đề bài tập bị thiếu câu hỏi âm thầm; GV sửa file rồi import lại dễ hơn phải dò xóa câu lỗi giữa chừng. |

## Features trong Sprint

| Feature ID | Tên | Module | Spec | Status |
|---|---|---|---|---|
| `F-EXE-01` | Exercise Bank (Đề bài tập, câu hỏi & đáp án) | `exercise` | [f_exe_01_exercises_spec.md](../specs/f_exe_01_exercises_spec.md) | `draft` |
| `F-EXE-02` | Class Assignments (Giao bài cho lớp) | `exercise` | [f_exe_02_assignments_spec.md](../specs/f_exe_02_assignments_spec.md) | `draft` |
| `F-EXE-03` | Student Submission (Làm bài & nộp bài) | `exercise` | [f_exe_03_submission_spec.md](../specs/f_exe_03_submission_spec.md) | `draft` |
| `F-EXE-04` | Auto Grading (Chấm điểm tự động trắc nghiệm) | `exercise` | [f_exe_04_grading_spec.md](../specs/f_exe_04_grading_spec.md) | `draft` |
| `F-EXE-05` | Question Import (Nhập câu hỏi từ file docx/pdf theo template) | `exercise` | [f_exe_05_question_import_spec.md](../specs/f_exe_05_question_import_spec.md) | `draft` |

## Thứ tự thực thi

```
F-EXE-01 (exercises + questions + answer_options CRUD & Restore)
  ├── F-EXE-02 (class_assignments — giao bài, cần exercise tồn tại + teacher_subjects scoping)
  │     └── F-EXE-03 (student_exercise_attempts — start/submit, cần assignment tồn tại + student_class scoping)
  │           └── F-EXE-04 (auto grading — chấm ngay khi submit, cần attempt + questions + answer_options)
  └── F-EXE-05 (question import — nạp hàng loạt câu hỏi vào exercise đã tạo, dùng lại QuestionService của F-EXE-01)
```

F-EXE-02 không được start trước khi F-EXE-01 đạt gate G6.5 `approved`. F-EXE-04 gắn liền luồng submit của F-EXE-03 (chấm điểm là bước cuối trong cùng transaction nộp bài, không phải feature độc lập vận hành song song). F-EXE-05 độc lập với F-EXE-02/03/04, chỉ phụ thuộc F-EXE-01 (tái dùng `QuestionService.add_question`), có thể làm song song với F-EXE-02.

## Definition Done — Sprint 2

| ✓ | Tiêu chí |
|---|---|
| ☐ | Alembic migration mới thêm cột `status` cho `exercises` + bảng `answer_options` (nếu chưa có trong baseline) |
| ☐ | `POST/GET/PUT/DELETE/RESTORE /api/v1/exercises` — CRUD & Restore đề bài tập, scoping theo `teacher_subjects` |
| ☐ | `POST/GET/PUT/DELETE /api/v1/exercises/{exercise_id}/questions` — CRUD câu hỏi + đáp án lồng trong đề |
| ☐ | `POST/GET/DELETE /api/v1/classes/{class_id}/assignments` — giao/hủy giao bài tập cho lớp, validate GV đúng môn+lớp |
| ☐ | `POST /api/v1/assignments/{assignment_id}/attempts` — HS bắt đầu làm bài, validate ghi danh lớp + role Student |
| ☐ | `PUT /api/v1/attempts/{attempt_id}/submit` — HS nộp bài, trigger chấm điểm tự động trắc nghiệm |
| ☐ | `GET /api/v1/attempts/{attempt_id}` — xem kết quả (điểm, đáp án đúng/sai từng câu) theo RBAC Data Scoping |
| ☐ | Seed permission mới `EXE_*` (`EXE_EXERCISE_MANAGE/VIEW`, `EXE_ASSIGNMENT_MANAGE/VIEW`, `EXE_ATTEMPT_SUBMIT/VIEW`, `EXE_QUESTION_IMPORT`), map cho role Teacher/Student tương ứng |
| ☐ | `POST /api/v1/exercises/{exercise_id}/questions/import` — nhập hàng loạt câu hỏi từ file `.docx`/`.pdf` theo template cố định, all-or-nothing |
| ☐ | `pytest tests` pass 100% cho module `exercise` |
| ☐ | Specs `F-EXE-01..05` cập nhật theo thực tế triển khai, status `done` |

## Catalogs khởi tạo trong Sprint này

- Permission mới: `EXE_EXERCISE_MANAGE`, `EXE_EXERCISE_VIEW`, `EXE_ASSIGNMENT_MANAGE`, `EXE_ASSIGNMENT_VIEW`, `EXE_ATTEMPT_SUBMIT`, `EXE_ATTEMPT_VIEW`, `EXE_QUESTION_IMPORT`.
- Error code mới `ERR-EXE-*` (xem chi tiết từng spec §PART A workflow), gồm `ERR-EXE-EXERCISE_NOT_FOUND`, `ERR-EXE-QUESTION_NOT_FOUND`, `ERR-EXE-INVALID_SUBJECT_SCOPE`, `ERR-EXE-ASSIGNMENT_NOT_FOUND`, `ERR-EXE-CLASS_ACCESS_DENIED`, `ERR-EXE-DUPLICATE_ASSIGNMENT`, `ERR-EXE-ATTEMPT_ALREADY_OPEN`, `ERR-EXE-ATTEMPT_ALREADY_SUBMITTED`, `ERR-EXE-ATTEMPT_NOT_FOUND`, `ERR-EXE-STUDENT_NOT_ENROLLED`, `ERR-EXE-IMPORT_FILE_TYPE_UNSUPPORTED`, `ERR-EXE-IMPORT_PARSE_FAILED`, `ERR-EXE-IMPORT_INVALID_QUESTION`.
