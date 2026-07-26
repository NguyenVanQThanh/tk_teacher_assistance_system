# Feature Spec — `F-ACAD-03` Enrollment (Ghi danh & Restore học sinh)

> Path: `docs/v_1/specs/f_acad_03_enrollment_spec.md` · Sprint: [sprint_1_overview.md](../sprints/sprint_1_overview.md)
> Created At: `2026-07-18`
> Created By: `Tam Khang`
> Updated At: `2026-07-26`
> Updated By: `Tam Khang`

---

## Document Header

| Field | Giá trị |
|---|---|
| Feature ID | `F-ACAD-03` |
| Feature name | Enrollment — Ghi danh & Restore học sinh vào lớp |
| Module(s) | `academic` |
| Sprint(s) allocated | `SPRINT-01` |
| Lane | `standard` |
| Spec version | `v1.2` |
| Last updated | `2026-07-26` |
| Source binding | SOP §12 · `models/models.py` (bảng `student_class`) · `f_auth_01_spec.md` (RBAC, current-user) · `.claude/rules/coding_rules.md` |

---

# PART A — Business

> **Owner:** Tam Khang · **Gate:** G3

## A.1 Feature Summary

Cho phép **Admin** quản lý việc ghi danh học sinh vào lớp (`student_class`) — ghi danh mới, hủy ghi danh (xóa mềm `status = 'DELETED'`), và khôi phục ghi danh (`POST /api/v1/classes/{class_id}/students/{student_id}/restore`). Kiểm tra danh sách học sinh theo lớp áp dụng **RBAC Data Scoping** (chỉ xem được học sinh của lớp thuộc quyền hạn truy cập của mình).

Validation bao gồm: kiểm tra `student_id` tồn tại, role `Student` và trạng thái `Active`, kiểm tra trùng ghi danh, và tự động cắt khoảng trắng `student_code`.

## A.2 User Stories

| Story ID | As (role) | I want (capability) | So that (value) |
|---|---|---|---|
| US-01 | Admin | ghi danh học sinh vào lớp học | xếp học sinh vào lớp |
| US-02 | Admin/Teacher/Student | xem danh sách học sinh của lớp | biết danh sách học sinh thuộc lớp |
| US-03 | Admin | hủy ghi danh học sinh khỏi lớp (xóa mềm) | cập nhật khi học sinh chuyển lớp/thôi học |
| US-04 | Admin | khôi phục ghi danh học sinh | phục hồi bản ghi ghi danh lỡ xóa |

## A.3 Business Workflow (Quy trình ghi danh học sinh & Data Scoping)

```
[Client Request]
       │
       ▼
 1. Authentication & Permission Check
    ├── Yêu cầu quyền ACAD_ENROLLMENT_MANAGE cho Create/Delete/Restore
    └── Yêu cầu quyền ACAD_ENROLLMENT_VIEW & get_current_user cho List
       │
       ▼
 2. Pydantic Schema Validation
    ├── Tự động cắt khoảng trắng student_code
    └── Kiểm tra trạng thái thuộc AcademicStatusEnum
       │
       ▼
 3. Service Execution & Validation Steps
    ├── Enroll Student:
    │     ├── 1. Kiểm tra class_id tồn tại -> Raise 404 ERR-ACAD-CLASS_NOT_FOUND nếu không thấy
    │     ├── 2. Kiểm tra student_id tồn tại -> Raise 404 ERR-ACAD-STUDENT_NOT_FOUND nếu không thấy
    │     ├── 3. Kiểm tra user student_id có role Student & status Active -> Raise 400 ERR-ACAD-INVALID_STUDENT_ROLE nếu sai
    │     ├── 4. Kiểm tra đã ghi danh vào lớp chưa -> Raise 409 ERR-ACAD-ALREADY_ENROLLED nếu trùng
    │     └── 5. Kiểm tra mã học sinh (nếu có) -> Raise 409 ERR-ACAD-DUPLICATE_STUDENT_CODE nếu trùng
    ├── List Students in Class (Data Scoping):
    │     ├── 1. Kiểm tra class_id tồn tại -> Raise 404 ERR-ACAD-CLASS_NOT_FOUND nếu không thấy
    │     ├── 2. Kiểm tra user có quyền truy cập lớp class_id -> Raise 403 ERR-ACAD-CLASS_ACCESS_DENIED nếu không có quyền
    │     └── 3. Lấy danh sách học sinh theo status
    ├── Unenroll Student: Đặt status = DELETED
    └── Restore Enrollment: Tìm bản ghi ghi danh bao gồm DELETED -> Đặt status = ACTIVE
       │
       ▼
 4. Database Transaction & Output Serialization (EnrollmentOut DTO)
```

## A.4 Acceptance Criteria

| AC ID | REQ | Given | When | Then |
|---|---|---|---|---|
| AC-01 | REQ-ACAD-021 | Admin đăng nhập, HS và lớp hợp lệ | `POST /api/v1/classes/{class_id}/students` | 201, ghi danh thành công |
| AC-02 | REQ-ACAD-021 | Học sinh đã ghi danh vào lớp trước đó | `POST /api/v1/classes/{class_id}/students` | 409 `ERR-ACAD-ALREADY_ENROLLED` |
| AC-03 | REQ-ACAD-022 | Teacher/Student xem danh sách HS lớp không thuộc phạm vi | `GET /api/v1/classes/{class_id}/students` | 403 `ERR-ACAD-CLASS_ACCESS_DENIED` |
| AC-04 | REQ-ACAD-023 | Bản ghi ghi danh tồn tại | `DELETE /api/v1/classes/{class_id}/students/{student_id}` | 204 |
| AC-05 | REQ-ACAD-024 | Bản ghi ghi danh đang `DELETED` | `POST /api/v1/classes/{class_id}/students/{student_id}/restore` | 200, status về `ACTIVE` |

---

# PART B — Architecture & API Design

> **Owner:** Tam Khang · **Gate:** G4

### Endpoints
1. `POST /api/v1/classes/{class_id}/students`: Ghi danh học sinh. Yêu cầu `ACAD_ENROLLMENT_MANAGE`.
2. `GET /api/v1/classes/{class_id}/students`: Danh sách học sinh trong lớp (RBAC Data Scoping). Yêu cầu `ACAD_ENROLLMENT_VIEW`.
3. `DELETE /api/v1/classes/{class_id}/students/{student_id}`: Hủy ghi danh (xóa mềm). Yêu cầu `ACAD_ENROLLMENT_MANAGE`.
4. `POST /api/v1/classes/{class_id}/students/{student_id}/restore`: Khôi phục ghi danh. Yêu cầu `ACAD_ENROLLMENT_MANAGE`.
