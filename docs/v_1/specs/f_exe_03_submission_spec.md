# Feature Spec — `F-EXE-03` Student Submission (Làm bài & nộp bài)

> Path: `docs/v_1/specs/f_exe_03_submission_spec.md` · Sprint: [sprint_2_overview.md](../sprints/sprint_2_overview.md)
> Created At: `2026-07-28`
> Created By: `AI Agent`
> Updated At: `2026-07-28`
> Updated By: `AI Agent`

---

## Document Header

| Field | Giá trị |
|---|---|
| Feature ID | `F-EXE-03` |
| Feature name | Student Submission — Bắt đầu làm bài & nộp bài |
| Module(s) | `exercise` |
| Sprint(s) allocated | `SPRINT-02` |
| Lane | `standard` |
| Spec version | `v1.0` |
| Last updated | `2026-07-28` |
| Source binding | `docs/base_sql_erd.sql` (bảng `student_exercise_attempts`) · `f_exe_02_assignments_spec.md` (assignment phải tồn tại) · `f_exe_04_grading_spec.md` (chấm điểm khi submit) · `.claude/rules/coding_rules.md` |

---

# PART A — Business

> **Owner:** AI Agent · **Gate:** G3

## A.1 Feature Summary

Cho phép **Học sinh** thuộc lớp được giao bài bắt đầu một lượt làm bài (`student_exercise_attempts`), gửi câu trả lời và nộp bài. Mỗi học sinh chỉ có **1 attempt đang mở** cho mỗi assignment; sau khi nộp (`is_finished = true`) không được làm lại (AS-03 sprint 2). Ghi nhận `start_time`/`end_time`/`total_time_seconds` ở mức tối thiểu làm nền cho Tracking (Sprint 3).

## A.2 User Stories

| Story ID | As (role) | I want (capability) | So that (value) |
|---|---|---|---|
| US-01 | Student | bắt đầu làm bài được giao | tạo attempt để ghi nhận câu trả lời |
| US-02 | Student | nộp câu trả lời cho từng câu hỏi | hoàn thành bài làm |
| US-03 | Student | xem điểm/kết quả sau khi nộp | biết mình làm đúng/sai câu nào |
| US-04 | Teacher | xem kết quả làm bài của học sinh trong lớp mình dạy | theo dõi tiến độ/kết quả lớp |

## A.3 Business Workflow

```
[Client Request]
       │
       ▼
 1. Authentication & Permission Check
    ├── Yêu cầu quyền EXE_ATTEMPT_SUBMIT cho Start/Submit (chỉ role Student)
    └── Yêu cầu quyền EXE_ATTEMPT_VIEW cho Get Result
       │
       ▼
 2. Pydantic Schema Validation
    └── answers: list[{question_id, answer_option_id | answer_text}] — bắt buộc đúng 1 trong 2 field theo question_type
       │
       ▼
 3. Service Execution & Scoping
    ├── Start Attempt:
    │     ├── 1. Kiểm tra assignment_id tồn tại -> Raise 404 ERR-EXE-ASSIGNMENT_NOT_FOUND
    │     ├── 2. Kiểm tra student có student_class ACTIVE với assignment.class_id -> Raise 403 ERR-EXE-STUDENT_NOT_ENROLLED
    │     ├── 3. Kiểm tra chưa có attempt đang mở (is_finished=false) cho (student_id, assignment_id) -> Raise 409 ERR-EXE-ATTEMPT_ALREADY_OPEN
    │     └── 4. Tạo attempt: start_time = now(), is_finished = false
    ├── Submit Attempt:
    │     ├── 1. Kiểm tra attempt tồn tại & thuộc chính student -> Raise 404 ERR-EXE-ATTEMPT_NOT_FOUND
    │     ├── 2. Kiểm tra is_finished = false -> Raise 409 ERR-EXE-ATTEMPT_ALREADY_SUBMITTED nếu đã nộp
    │     ├── 3. Gọi GradingService (F-EXE-04) chấm điểm câu MultipleChoice, build detailed_results JSONB
    │     └── 4. Cập nhật end_time = now(), total_time_seconds = end_time - start_time, score, is_finished = true
    └── Get Result: Student xem attempt của chính mình; Teacher xem attempt của học sinh thuộc lớp mình dạy (check_class_access qua assignment.class_id)
       │
       ▼
 4. Database Transaction & Output Serialization (AttemptOut DTO)
```

## A.4 Acceptance Criteria

| AC ID | REQ | Given | When | Then |
|---|---|---|---|---|
| AC-01 | REQ-EXE-021 | Student ghi danh lớp có assignment, chưa có attempt mở | `POST /api/v1/assignments/{id}/attempts` | 201, attempt mới `is_finished=false` |
| AC-02 | REQ-EXE-021 | Student đã có attempt đang mở cho assignment đó | `POST /api/v1/assignments/{id}/attempts` | 409 `ERR-EXE-ATTEMPT_ALREADY_OPEN` |
| AC-03 | REQ-EXE-021 | Student không ghi danh lớp có assignment | `POST /api/v1/assignments/{id}/attempts` | 403 `ERR-EXE-STUDENT_NOT_ENROLLED` |
| AC-04 | REQ-EXE-022 | Attempt tồn tại, `is_finished=false`, đúng chủ attempt | `PUT /api/v1/attempts/{id}/submit` | 200, trả điểm + `is_finished=true` |
| AC-05 | REQ-EXE-022 | Attempt đã `is_finished=true` | `PUT /api/v1/attempts/{id}/submit` | 409 `ERR-EXE-ATTEMPT_ALREADY_SUBMITTED` |
| AC-06 | REQ-EXE-023 | Teacher xem attempt học sinh lớp không thuộc mình dạy | `GET /api/v1/attempts/{id}` | 403 `ERR-EXE-CLASS_ACCESS_DENIED` |

## A.5 Out of Scope

- Resubmit/làm lại sau khi nộp — AS-03, deferred.
- `behavior_logs` chi tiết (chuyển tab, dừng ở mỗi câu) — Sprint 3.

---

# PART B — Architecture & API Design

> **Owner:** AI Agent · **Gate:** G4

### Endpoints

1. `POST /api/v1/assignments/{assignment_id}/attempts`: Bắt đầu làm bài. Yêu cầu `EXE_ATTEMPT_SUBMIT`.
2. `PUT /api/v1/attempts/{attempt_id}/submit`: Nộp bài (kèm answers trong body) + trigger chấm điểm. Yêu cầu `EXE_ATTEMPT_SUBMIT`.
3. `GET /api/v1/attempts/{attempt_id}`: Xem kết quả (RBAC: chủ attempt hoặc GV dạy lớp đó). Yêu cầu `EXE_ATTEMPT_VIEW`.

### Database Boundary

| Table | Op | Migration |
|---|---|---|
| `student_exercise_attempts` | CREATE (nếu chưa có trong DB thực tế) | migration mới nếu cần |
