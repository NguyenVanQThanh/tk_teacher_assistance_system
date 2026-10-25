# Feature Spec — `F-ACAD-01` Subjects (CRUD & Restore môn học)

> Path: `docs/v_1/specs/f_acad_01_subjects_spec.md` · Sprint: [sprint_1_overview.md](../sprints/sprint_1_overview.md)
> Created At: `2026-07-18`
> Created By: `Tam Khang`
> Updated At: `2026-07-26`
> Updated By: `Tam Khang`

---

## Document Header

| Field | Giá trị |
|---|---|
| Feature ID | `F-ACAD-01` |
| Feature name | Subjects — CRUD & Restore môn học |
| Module(s) | `academic` |
| Sprint(s) allocated | `SPRINT-01` |
| Lane | `standard` |
| Spec version | `v1.2` |
| Last updated | `2026-07-26` |
| Source binding | SOP §12 · `models/models.py` (bảng `subjects`) · `f_auth_01_spec.md` (RBAC, current-user) · `.claude/rules/coding_rules.md` |

---

# PART A — Business

> **Owner:** Tam Khang · **Gate:** G3

## A.1 Feature Summary

Cho phép **Admin** quản lý danh mục môn học (`subjects`) — bao gồm tạo mới, cập nhật, xem danh sách/chi tiết, xóa mềm (chuyển `status = 'DELETED'`), và khôi phục môn học bị xóa mềm về `ACTIVE` (`POST /api/v1/subjects/{subject_id}/restore`). Hỗ trợ quản lý trạng thái (`ACTIVE`, `INACTIVE`, `DRAFT`, `DELETED`), validation đầu vào (tự động cắt khoảng trắng `strip()`, kiểm tra chuỗi rỗng), và lọc dữ liệu linh hoạt theo vai trò (Student chỉ xem các môn liên quan đến lớp học của mình).

## A.2 User Stories

| Story ID | As (role) | I want (capability) | So that (value) |
|---|---|---|---|
| US-01 | Admin | tạo môn học mới với trạng thái chỉ định | có danh mục môn học cho hệ thống dùng |
| US-02 | Admin/Teacher/Student | xem danh sách/chi tiết môn học theo phạm vi dữ liệu | xem môn học thuộc quyền hạn của mình |
| US-03 | Admin | sửa tên/mô tả/trạng thái môn học | cập nhật khi thông tin thay đổi |
| US-04 | Admin | xóa mềm môn học không còn dùng | dọn dẹp danh mục mà không mất lịch sử dữ liệu |
| US-05 | Admin | khôi phục môn học đã xóa mềm (`DELETED`) | phục hồi dữ liệu lỡ xóa của người dùng |

## A.3 Business Workflow (Quy trình nghiệp vụ môn học)

```
[Client Request]
       │
       ▼
 1. Authentication & Permission Check (JWT Bearer Token)
    ├── Yêu cầu quyền ACAD_SUBJECT_MANAGE cho Create/Update/Delete/Restore
    └── Yêu cầu quyền ACAD_SUBJECT_VIEW cho List/Get Detail
       │
       ▼
 2. Pydantic Schema Validation
    ├── Tự động cắt khoảng trắng đầu/cuối (strip) tên & mô tả môn học
    ├── Bắt lỗi nếu tên rỗng hoặc chứa toàn khoảng trắng -> 422 Unprocessable Entity
    └── Ép kiểu và kiểm tra trạng thái hợp lệ trong AcademicStatusEnum
       │
       ▼
 3. Service & Business Execution
    ├── Create: Kiểm tra trùng tên môn học -> Raise 409 ERR-ACAD-SUBJECT_DUPLICATE_NAME nếu trùng
    ├── List: Áp dụng RBAC Data Scoping (Student chỉ lọc các môn học trong lớp mình đang học)
    ├── Update: Kiểm tra tồn tại môn học -> Kiểm tra trùng tên với môn khác -> Cập nhật
    ├── Delete: Chuyển trạng thái status sang DELETED
    └── Restore: Tìm môn học ngầm (bao gồm DELETED) -> Chuyển trạng thái status về ACTIVE
       │
       ▼
 4. Database Transaction & Output Serialization (SubjectOut DTO)
```

## A.4 Acceptance Criteria

| AC ID | REQ | Given | When | Then |
|---|---|---|---|---|
| AC-01 | REQ-ACAD-001 | Admin đăng nhập, tên môn chưa tồn tại | `POST /api/v1/subjects` | 201, trả về subject vừa tạo |
| AC-02 | REQ-ACAD-001 | tên môn đã tồn tại | `POST /api/v1/subjects` | 409 `ERR-ACAD-SUBJECT_DUPLICATE_NAME` |
| AC-03 | REQ-ACAD-002 | danh sách môn học trong DB | `GET /api/v1/subjects?status=ACTIVE` | 200, danh sách môn theo trạng thái |
| AC-04 | REQ-ACAD-002 | `subject_id` không tồn tại hoặc đã xóa mềm | `GET /api/v1/subjects/{id}` | 404 `ERR-ACAD-SUBJECT_NOT_FOUND` |
| AC-05 | REQ-ACAD-003 | môn học tồn tại | `PUT /api/v1/subjects/{id}` | 200, thông tin cập nhật |
| AC-06 | REQ-ACAD-004 | môn học tồn tại | `DELETE /api/v1/subjects/{id}` | 204, môn bị chuyển sang `DELETED` |
| AC-07 | REQ-ACAD-005 | môn học đang `DELETED` | `POST /api/v1/subjects/{id}/restore` | 200, status chuyển về `ACTIVE` |

---

# PART B — Architecture & API Design

> **Owner:** Tam Khang · **Gate:** G4

### Endpoints
1. `POST /api/v1/subjects`: Tạo môn học. Yêu cầu `ACAD_SUBJECT_MANAGE`.
2. `GET /api/v1/subjects`: Danh sách môn học. Yêu cầu `ACAD_SUBJECT_VIEW`.
3. `GET /api/v1/subjects/{subject_id}`: Chi tiết môn học. Yêu cầu `ACAD_SUBJECT_VIEW`.
4. `PUT /api/v1/subjects/{subject_id}`: Cập nhật môn học. Yêu cầu `ACAD_SUBJECT_MANAGE`.
5. `DELETE /api/v1/subjects/{subject_id}`: Xóa mềm môn học. Yêu cầu `ACAD_SUBJECT_MANAGE`.
6. `POST /api/v1/subjects/{subject_id}/restore`: Khôi phục môn học. Yêu cầu `ACAD_SUBJECT_MANAGE`.
