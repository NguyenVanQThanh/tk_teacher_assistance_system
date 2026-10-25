# Feature Spec — `F-EXE-02` Class Assignments (Giao bài tập cho lớp)

> Path: `docs/v_1/specs/f_exe_02_assignments_spec.md` · Sprint: [sprint_2_overview.md](../sprints/sprint_2_overview.md)
> Created At: `2026-07-28`
> Created By: `Tam Khang`
> Updated At: `2026-07-31`
> Updated By: `Tam Khang`

---

## Document Header

| Field | Giá trị |
|---|---|
| Feature ID | `F-EXE-02` |
| Feature name | Class Assignments — Giao/hủy giao bài tập cho lớp |
| Module(s) | `exercise` |
| Sprint(s) allocated | `SPRINT-02` |
| Lane | `standard` |
| Spec version | `v1.0` |
| Last updated | `2026-07-31` |
| Source binding | `docs/base_sql_erd.sql` (bảng `class_assignments`) · `f_exe_01_exercises_spec.md` (đề phải tồn tại & thuộc quyền) · `f_acad_04_teacher_assignment_spec.md` (`teacher_subjects` scoping) · `.claude/rules/coding_rules.md` |

---

# PART A — Business

> **Owner:** Tam Khang · **Gate:** G3

## A.1 Feature Summary

Cho phép **Giáo viên** giao đề bài tập (`exercises`) cho lớp mình đang dạy đúng môn học của đề đó, kèm hạn nộp (`due_at`). **Học sinh** thuộc lớp xem được danh sách bài được giao. Hủy giao bài thực hiện **soft delete** (chuyển `status` sang `DELETED` theo quy chuẩn hệ thống) — chỉ cho phép khi chưa có học sinh nào bắt đầu làm bài (`student_exercise_attempts`), để bảo toàn toàn vẹn dữ liệu.


## A.2 User Stories

| Story ID | As (role) | I want (capability) | So that (value) |
|---|---|---|---|
| US-01 | Teacher | giao đề bài tập cho lớp mình dạy kèm hạn nộp | học sinh có bài để làm |
| US-02 | Teacher/Student | xem danh sách bài được giao của lớp | biết bài tập cần làm và hạn nộp |
| US-03 | Teacher | hủy giao bài nếu giao nhầm và chưa ai làm | sửa sai trước khi học sinh bắt đầu |

## A.3 Business Workflow

```
[Client Request]
       │
       ▼
 1. Authentication & Permission Check
    ├── Yêu cầu quyền EXE_ASSIGNMENT_MANAGE cho Create/Delete
    └── Yêu cầu quyền EXE_ASSIGNMENT_VIEW & get_current_user cho List
       │
       ▼
 2. Pydantic Schema Validation
    └── due_at phải là thời điểm trong tương lai (so với thời điểm tạo)
       │
       ▼
 3. Service Execution & Scoping
    ├── Create Assignment:
    │     ├── 1. Kiểm tra class_id tồn tại & ACTIVE -> Raise 404 ERR-ACAD-CLASS_NOT_FOUND nếu không
    │     ├── 2. Kiểm tra exercise_id tồn tại & thuộc quyền teacher (F-EXE-01 scoping) -> Raise 404 ERR-EXE-EXERCISE_NOT_FOUND nếu không
    │     ├── 3. Kiểm tra teacher có teacher_subjects ACTIVE khớp (class_id, exercise.subject_id) -> Raise 403 ERR-EXE-CLASS_ACCESS_DENIED nếu không
    │     └── 4. Kiểm tra đề đã giao cho lớp này chưa -> Raise 409 ERR-EXE-DUPLICATE_ASSIGNMENT nếu trùng
    ├── List (Data Scoping):
    │     ├── Admin: toàn bộ
    │     ├── Teacher: assignment của lớp mình dạy/chủ nhiệm (dùng get_accessible_class_ids)
    │     └── Student: assignment của lớp mình ghi danh
    └── Delete Assignment: Kiểm tra chưa có student_exercise_attempts nào liên kết -> Raise 409 ERR-EXE-ASSIGNMENT_HAS_ATTEMPTS nếu có -> Soft delete (`status = 'DELETED'`) nếu không
       │
       ▼
 4. Database Transaction & Output Serialization (AssignmentOut DTO)
```

## A.4 Acceptance Criteria

| AC ID | REQ | Given | When | Then |
|---|---|---|---|---|
| AC-01 | REQ-EXE-011 | Teacher dạy đúng môn ở đúng lớp, đề ACTIVE | `POST /api/v1/classes/{class_id}/assignments` | 201, trả về assignment vừa tạo |
| AC-02 | REQ-EXE-011 | Teacher không dạy môn của đề ở lớp đó | `POST /api/v1/classes/{class_id}/assignments` | 403 `ERR-EXE-CLASS_ACCESS_DENIED` |
| AC-03 | REQ-EXE-011 | Đề đã giao cho lớp này trước đó | `POST /api/v1/classes/{class_id}/assignments` | 409 `ERR-EXE-DUPLICATE_ASSIGNMENT` |
| AC-04 | REQ-EXE-012 | Student xem danh sách bài giao của lớp mình | `GET /api/v1/classes/{class_id}/assignments` | 200, danh sách assignment |
| AC-05 | REQ-EXE-012 | Student/Teacher truy cập lớp ngoài phạm vi | `GET /api/v1/classes/{class_id}/assignments` | 403 `ERR-ACAD-CLASS_ACCESS_DENIED` |
| AC-06 | REQ-EXE-013 | Assignment đã có học sinh attempt | `DELETE /api/v1/assignments/{assignment_id}` | 409 `ERR-EXE-ASSIGNMENT_HAS_ATTEMPTS` |
| AC-07 | REQ-EXE-013 | Assignment chưa có attempt nào | `DELETE /api/v1/assignments/{assignment_id}` | 204 (soft-deleted, status sang `DELETED`) |

## A.5 Out of Scope

- Sửa hạn nộp (`due_at`) sau khi tạo — chưa yêu cầu ở Sprint 2, thêm `PUT` khi có nhu cầu thực tế.
- Thông báo/nhắc hạn nộp (`notifications`) — Sprint 3 (Tracking).

---

# PART B — Architecture & API Design

> **Owner:** Tam Khang · **Gate:** G4

### Endpoints

1. `POST /api/v1/classes/{class_id}/assignments`: Giao bài. Yêu cầu `EXE_ASSIGNMENT_MANAGE`.
2. `GET /api/v1/classes/{class_id}/assignments`: Danh sách bài giao (RBAC Data Scoping, tái dùng `check_class_access` từ `app/modules/academic/scoping.py`). Yêu cầu `EXE_ASSIGNMENT_VIEW`.
3. `DELETE /api/v1/assignments/{assignment_id}`: Hủy giao bài (soft delete có điều kiện). Yêu cầu `EXE_ASSIGNMENT_MANAGE`.

### Database Boundary

| Table | Op | Migration |
|---|---|---|
| `class_assignments` | CREATE | Migration mới với cột `status` VARCHAR(20) DEFAULT 'ACTIVE' NOT NULL hỗ trợ Soft Delete |

