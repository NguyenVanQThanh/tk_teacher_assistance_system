# Feature Spec — `F-EXE-01` Exercise Bank (Đề bài tập, câu hỏi & đáp án)

> Path: `docs/v_1/specs/f_exe_01_exercises_spec.md` · Sprint: [sprint_2_overview.md](../sprints/sprint_2_overview.md)
> Created At: `2026-07-28`
> Created By: `Tam Khang`
> Updated At: `2026-08-15`
> Updated By: `Tam Khang`

---

## Document Header

| Field | Giá trị |
|---|---|
| Feature ID | `F-EXE-01` |
| Feature name | Exercise Bank — CRUD & Restore đề bài tập, câu hỏi, đáp án |
| Module(s) | `exercise` |
| Sprint(s) allocated | `SPRINT-02` |
| Lane | `standard` |
| Spec version | `v1.2` |
| Last updated | `2026-08-15` |
| Source binding | `docs/base_sql_erd.sql` (bảng `exercises`, `questions`, `answer_options`) · `f_auth_01_spec.md` (RBAC, current-user) · `f_acad_04_teacher_assignment_spec.md` (`teacher_subjects` scoping) · `.claude/rules/coding_rules.md` |

---

# PART A — Business

> **Owner:** Tam Khang · **Gate:** G3

## A.1 Feature Summary

Cho phép **Giáo viên** quản lý kho đề bài tập (`exercises`) thuộc môn học mình được phân công dạy — tạo đề, thêm/sửa/xóa câu hỏi (`questions`) và đáp án lựa chọn (`answer_options`), xóa mềm và khôi phục đề. **Admin** có toàn quyền xem/quản lý mọi đề. **Học sinh** không truy cập trực tiếp endpoint này (chỉ thấy đề qua giao bài ở `F-EXE-02`).

## A.2 User Stories

| Story ID | As (role) | I want (capability) | So that (value) |
|---|---|---|---|
| US-01 | Teacher | tạo đề bài tập mới cho môn mình dạy | có đề để giao cho lớp |
| US-02 | Teacher | thêm câu hỏi trắc nghiệm/tự luận kèm đáp án vào đề | xây dựng nội dung đề hoàn chỉnh |
| US-03 | Admin/Teacher | xem danh sách/chi tiết đề theo phạm vi môn dạy | quản lý kho đề của mình |
| US-04 | Teacher | sửa/xóa mềm đề hoặc câu hỏi không còn dùng | dọn dẹp kho đề mà không mất lịch sử (đề đã giao bài vẫn giữ dữ liệu) |
| US-05 | Teacher | khôi phục đề đã xóa mềm | phục hồi đề lỡ xóa |

## A.3 Business Workflow

```
[Client Request]
       │
       ▼
 1. Authentication & Permission Check
    ├── Yêu cầu quyền EXE_EXERCISE_MANAGE cho Create/Update/Delete/Restore/Question CRUD
    └── Yêu cầu quyền EXE_EXERCISE_VIEW cho List/Get Detail
       │
       ▼
 2. Pydantic Schema Validation
    ├── strip() title, bắt lỗi rỗng
    ├── question_type Enum (MultipleChoice, ShortAnswer), difficulty Enum (NhanBiet, ThongHieu, VanDung)
    └── MultipleChoice bắt buộc >= 2 answer_options và đúng 1 is_correct=true
       │
       ▼
 3. Service Execution & Scoping
    ├── Create Exercise: Kiểm tra subject_id tồn tại -> Kiểm tra teacher_id có teacher_subjects ACTIVE với subject_id đó (trừ Admin) -> Raise 403 ERR-EXE-INVALID_SUBJECT_SCOPE nếu không
    ├── List/Detail: Admin xem toàn bộ; Teacher chỉ xem đề created_by = mình hoặc subject thuộc teacher_subjects của mình
    ├── Add Question: Kiểm tra exercise tồn tại & thuộc quyền -> validate answer_options nếu MultipleChoice
    ├── Update/Delete Question: Kiểm tra question thuộc đúng exercise được phép sửa -> Delete Question chuyển status sang DELETED (soft-delete)
    ├── Delete Exercise: Chuyển status sang DELETED (giữ nguyên questions/answer_options — cascade không xóa cứng)
    └── Restore: Tìm đề bao gồm DELETED -> chuyển status về ACTIVE
       │
       ▼
 4. Database Transaction & Output Serialization (ExerciseOut / QuestionOut DTO)
```

## A.4 Acceptance Criteria

| AC ID | REQ | Given | When | Then |
|---|---|---|---|---|
| AC-01 | REQ-EXE-001 | Teacher đăng nhập, có `teacher_subjects` ACTIVE với `subject_id` | `POST /api/v1/exercises` | 201, trả về đề vừa tạo |
| AC-02 | REQ-EXE-001 | Teacher không dạy môn `subject_id` đó | `POST /api/v1/exercises` | 403 `ERR-EXE-INVALID_SUBJECT_SCOPE` |
| AC-03 | REQ-EXE-002 | Câu hỏi `MultipleChoice` không có đáp án đúng nào | `POST /api/v1/exercises/{id}/questions` | 422 Unprocessable Entity |
| AC-04 | REQ-EXE-002 | Câu hỏi `MultipleChoice` có >1 đáp án đúng | `POST /api/v1/exercises/{id}/questions` | 422 Unprocessable Entity |
| AC-05 | REQ-EXE-003 | Teacher xem đề không thuộc mình tạo/không dạy môn đó | `GET /api/v1/exercises/{id}` | 404 `ERR-EXE-EXERCISE_NOT_FOUND` (ẩn tồn tại thay vì 403) |
| AC-06 | REQ-EXE-004 | Đề tồn tại, thuộc quyền | `DELETE /api/v1/exercises/{id}` | 204, status chuyển `DELETED` |
| AC-07 | REQ-EXE-005 | Đề đang `DELETED` | `POST /api/v1/exercises/{id}/restore` | 200, status về `ACTIVE` |

## A.5 Out of Scope

- Upload tài liệu nguồn (`documents`) / AI sinh câu hỏi tự động — Sprint 4.
- Chấm điểm — xem `F-EXE-04`.

---

# PART B — Architecture & API Design

> **Owner:** Tam Khang · **Gate:** G4

### Endpoints

1. `POST /api/v1/exercises`: Tạo đề. Yêu cầu `EXE_EXERCISE_MANAGE`.
2. `GET /api/v1/exercises`: Danh sách đề (scoping theo subject dạy). Yêu cầu `EXE_EXERCISE_VIEW`.
3. `GET /api/v1/exercises/{exercise_id}`: Chi tiết đề kèm questions + answer_options. Yêu cầu `EXE_EXERCISE_VIEW`.
4. `PUT /api/v1/exercises/{exercise_id}`: Cập nhật đề (title, ai_metadata). Yêu cầu `EXE_EXERCISE_MANAGE`.
5. `DELETE /api/v1/exercises/{exercise_id}`: Xóa mềm đề. Yêu cầu `EXE_EXERCISE_MANAGE`.
6. `POST /api/v1/exercises/{exercise_id}/restore`: Khôi phục đề. Yêu cầu `EXE_EXERCISE_MANAGE`.
7. `POST /api/v1/exercises/{exercise_id}/questions`: Thêm câu hỏi (+ answer_options lồng trong body). Yêu cầu `EXE_EXERCISE_MANAGE`.
8. `PUT /api/v1/questions/{question_id}`: Sửa câu hỏi. Yêu cầu `EXE_EXERCISE_MANAGE`.
9. `DELETE /api/v1/questions/{question_id}`: Xóa mềm câu hỏi (chuyển status sang DELETED). Yêu cầu `EXE_EXERCISE_MANAGE`.

### Database Boundary

| Table | Op | Migration |
|---|---|---|
| `exercises` | ALTER (add `status VARCHAR(20) DEFAULT 'ACTIVE'`) | migration mới, Section 7 coding rules |
| `questions` | CREATE / ALTER (add `status VARCHAR(20) DEFAULT 'ACTIVE'`, `content_markdown TEXT`, `content_latex TEXT`) | migration mới |
| `answer_options` | CREATE (nếu chưa có) | migration mới nếu cần |

> Ghi chú: kiểm tra state DB hiện tại trước khi viết migration — nếu bảng đã tồn tại từ baseline thì chỉ cần ALTER thêm `status`, `content_markdown`, `content_latex`.

---

## Changelog

| Version | Date | Author | Thay đổi |
|---|---|---|---|
| v1.0 | 2026-07-31 | Tam Khang | Khởi tạo spec, implement CRUD + soft delete/restore cho exercises/questions/answer_options |
| v1.1 | 2026-08-03 | Thanh Nguyen | Ghi nhận đề xuất refactor: khai báo `ExerciseService`/`QuestionService` qua dependency injection chung (`Depends(get_exercise_service)` / `Depends(get_question_service)`) thay vì khởi tạo `Service(db)` lặp lại trong từng route handler của `exercises.py` và `questions.py` — chưa áp dụng vào code, cần schedule riêng. |
| v1.2 | 2026-08-15 | Tam Khang | Thêm hai trường `content_markdown` (Markdown quy đổi Unicode) và `content_latex` (LaTeX nguyên bản) cho `Question` model & schema |
