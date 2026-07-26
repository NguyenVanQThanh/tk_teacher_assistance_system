# Feature Spec — `F-ACAD-04` Teacher Assignment (Phân công & Restore GV bộ môn)

> Path: `docs/v_1/specs/f_acad_04_teacher_assignment_spec.md` · Sprint: [sprint_1_overview.md](../sprints/sprint_1_overview.md)
> Created At: `2026-07-18`
> Created By: `Tam Khang`
> Updated At: `2026-07-26`
> Updated By: `Tam Khang`

---

## Document Header

| Field | Giá trị |
|---|---|
| Feature ID | `F-ACAD-04` |
| Feature name | Teacher Assignment — Phân công & Restore giáo viên bộ môn |
| Module(s) | `academic` |
| Sprint(s) allocated | `SPRINT-01` |
| Lane | `standard` |
| Spec version | `v1.2` |
| Last updated | `2026-07-26` |
| Source binding | SOP §12 · `models/models.py` (bảng `teacher_subjects`) · `f_auth_01_spec.md` (RBAC, current-user) · `.claude/rules/coding_rules.md` |

---

# PART A — Business

> **Owner:** Tam Khang · **Gate:** G3

## A.1 Feature Summary

Cho phép **Admin** quản lý việc phân công giáo viên giảng dạy môn học tại từng lớp (`teacher_subjects`) — phân công mới, hủy phân công (xóa mềm `status = 'DELETED'`), và khôi phục phân công (`POST /api/v1/classes/{class_id}/teacher-subjects/{teacher_id}/{subject_id}/restore`). Danh sách phân công theo lớp áp dụng **RBAC Data Scoping** (chỉ xem được phân công của lớp thuộc quyền hạn truy cập của mình).

Validation bao gồm: kiểm tra `teacher_id` và `subject_id` tồn tại, role giáo viên `Teacher` và trạng thái `Active`, kiểm tra trùng phân công.

## A.2 User Stories

| Story ID | As (role) | I want (capability) | So that (value) |
|---|---|---|---|
| US-01 | Admin | phân công giáo viên dạy môn học ở lớp | gán nhiệm vụ giảng dạy cho giáo viên |
| US-02 | Admin/Teacher/Student | xem danh sách phân công GV theo lớp | biết giáo viên nào dạy môn gì ở lớp |
| US-03 | Admin | hủy phân công giáo viên (xóa mềm) | cập nhật khi thay đổi giáo viên bộ môn |
| US-04 | Admin | khôi phục phân công giáo viên | phục hồi phân công lỡ xóa |

## A.3 Business Workflow (Quy trình phân công giáo viên bộ môn)

```
[Client Request]
       │
       ▼
 1. Authentication & Permission Check
    ├── Yêu cầu quyền ACAD_TEACHER_ASSIGN_MANAGE cho Create/Delete/Restore
    └── Yêu cầu quyền ACAD_TEACHER_ASSIGN_VIEW & get_current_user cho List
       │
       ▼
 2. Pydantic Schema Validation
    └── Kiểm tra trạng thái thuộc AcademicStatusEnum
       │
       ▼
 3. Service Execution & Validation Steps
    ├── Assign Teacher:
    │     ├── 1. Kiểm tra class_id tồn tại -> Raise 404 ERR-ACAD-CLASS_NOT_FOUND nếu không thấy
    │     ├── 2. Kiểm tra subject_id tồn tại -> Raise 404 ERR-ACAD-SUBJECT_NOT_FOUND nếu không thấy
    │     ├── 3. Kiểm tra user teacher_id có role Teacher & status Active -> Raise 400 ERR-ACAD-INVALID_TEACHER_ROLE nếu sai
    │     └── 4. Kiểm tra phân công đã tồn tại chưa -> Raise 409 ERR-ACAD-ASSIGNMENT_EXISTS nếu trùng
    ├── List Assignments in Class (Data Scoping):
    │     ├── 1. Kiểm tra class_id tồn tại -> Raise 404 ERR-ACAD-CLASS_NOT_FOUND nếu không thấy
    │     ├── 2. Kiểm tra user có quyền truy cập lớp class_id -> Raise 403 ERR-ACAD-CLASS_ACCESS_DENIED nếu không có quyền
    │     └── 3. Lấy danh sách phân công theo status
    ├── Unassign Teacher: Đặt status = DELETED
    └── Restore Assignment: Tìm bản ghi phân công bao gồm DELETED -> Đặt status = ACTIVE
       │
       ▼
 4. Database Transaction & Output Serialization (TeacherAssignmentOut DTO)
```

## A.4 Acceptance Criteria

| AC ID | REQ | Given | When | Then |
|---|---|---|---|---|
| AC-01 | REQ-ACAD-031 | Admin đăng nhập, GV, môn và lớp hợp lệ | `POST /api/v1/classes/{class_id}/teacher-subjects` | 201, phân công thành công |
| AC-02 | REQ-ACAD-031 | Phân công đã tồn tại trước đó | `POST /api/v1/classes/{class_id}/teacher-subjects` | 409 `ERR-ACAD-ASSIGNMENT_EXISTS` |
| AC-03 | REQ-ACAD-032 | Teacher/Student xem phân công lớp không thuộc phạm vi | `GET /api/v1/classes/{class_id}/teacher-subjects` | 403 `ERR-ACAD-CLASS_ACCESS_DENIED` |
| AC-04 | REQ-ACAD-033 | Phân công tồn tại | `DELETE /api/v1/classes/{class_id}/teacher-subjects/...` | 204 |
| AC-05 | REQ-ACAD-034 | Phân công đang `DELETED` | `POST /api/v1/classes/{class_id}/teacher-subjects/.../restore` | 200, status về `ACTIVE` |

---

# PART B — Architecture & API Design

> **Owner:** Tam Khang · **Gate:** G4

### Endpoints
1. `POST /api/v1/classes/{class_id}/teacher-subjects`: Phân công giáo viên. Yêu cầu `ACAD_TEACHER_ASSIGN_MANAGE`.
2. `GET /api/v1/classes/{class_id}/teacher-subjects`: Danh sách phân công trong lớp (RBAC Data Scoping). Yêu cầu `ACAD_TEACHER_ASSIGN_VIEW`.
3. `DELETE /api/v1/classes/{class_id}/teacher-subjects/{teacher_id}/{subject_id}`: Hủy phân công (xóa mềm). Yêu cầu `ACAD_TEACHER_ASSIGN_MANAGE`.
4. `POST /api/v1/classes/{class_id}/teacher-subjects/{teacher_id}/{subject_id}/restore`: Khôi phục phân công. Yêu cầu `ACAD_TEACHER_ASSIGN_MANAGE`.
