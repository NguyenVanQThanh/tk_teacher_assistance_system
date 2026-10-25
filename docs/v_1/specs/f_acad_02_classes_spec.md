# Feature Spec — `F-ACAD-02` Classes (CRUD & Restore lớp học)

> Path: `docs/v_1/specs/f_acad_02_classes_spec.md` · Sprint: [sprint_1_overview.md](../sprints/sprint_1_overview.md)
> Created At: `2026-07-18`
> Created By: `Tam Khang`
> Updated At: `2026-07-26`
> Updated By: `Tam Khang`

---

## Document Header

| Field | Giá trị |
|---|---|
| Feature ID | `F-ACAD-02` |
| Feature name | Classes — CRUD & Restore lớp học |
| Module(s) | `academic` |
| Sprint(s) allocated | `SPRINT-01` |
| Lane | `standard` |
| Spec version | `v1.2` |
| Last updated | `2026-07-26` |
| Source binding | SOP §12 · `models/models.py` (bảng `classes`) · `f_auth_01_spec.md` (RBAC, current-user) · `.claude/rules/coding_rules.md` |

---

# PART A — Business

> **Owner:** Tam Khang · **Gate:** G3

## A.1 Feature Summary

Cho phép **Admin** quản lý danh mục lớp học (`classes`) — tạo mới, cập nhật, xóa mềm (`status = 'DELETED'`), và khôi phục (`POST /api/v1/classes/{class_id}/restore`). Đồng thời áp dụng **RBAC Data Scoping** nâng cao:
- **`Admin`**: Xem được toàn bộ danh sách lớp học và bản ghi bị xóa mềm (`status=DELETED`).
- **`Teacher`**: Chỉ xem danh sách lớp mà mình làm Giáo viên chủ nhiệm hoặc được Phân công giảng dạy.
- **`Student`**: Chỉ xem danh sách lớp mà mình Đang ghi danh theo học.

Validation bao gồm: tự động cắt khoảng trắng `strip()`, regex kiểm tra năm học `school_year` dạng `YYYY-YYYY`, kiểm tra giáo viên chủ nhiệm có vai trò `Teacher` và trạng thái `Active`.

## A.2 User Stories

| Story ID | As (role) | I want (capability) | So that (value) |
|---|---|---|---|
| US-01 | Admin | tạo lớp học mới với năm học và GVCN | thiết lập cơ cấu lớp cho trường |
| US-02 | Admin/Teacher/Student | xem danh sách/chi tiết lớp học theo phân quyền dữ liệu | xem đúng các lớp học thuộc phạm vi quản lý/theo học |
| US-03 | Admin | sửa tên/năm học/GVCN/trạng thái lớp học | cập nhật khi có thay đổi |
| US-04 | Admin | xóa mềm lớp học | chuyển trạng thái sang DELETED |
| US-05 | Admin | khôi phục lớp học đã xóa mềm | phục hồi lớp học lỡ xóa |

## A.3 Business Workflow (Quy trình nghiệp vụ lớp học & RBAC Data Scoping)

```
[Client Request]
       │
       ▼
 1. Authentication & RBAC Permission Check
    ├── Yêu cầu quyền ACAD_CLASS_MANAGE cho Create/Update/Delete/Restore
    └── Yêu cầu quyền ACAD_CLASS_VIEW & get_current_user cho List/Get Detail
       │
       ▼
 2. Pydantic Schema Validation
    ├── Tự động cắt khoảng trắng (strip) tên lớp học & năm học
    ├── Bắt lỗi regex school_year dạng YYYY-YYYY (e.g. 2025-2026) -> 422 Unprocessable Entity
    └── Ép kiểu và kiểm tra trạng thái hợp lệ trong AcademicStatusEnum
       │
       ▼
 3. Service Execution & RBAC Data Scoping Workflow
    ├── Create: Validate homeroom_teacher_id (phải có vai trò Teacher & Active) -> Raise 400 ERR-ACAD-INVALID_HOMEROOM_TEACHER nếu sai
    │           Kiểm tra trùng tên lớp -> Raise 409 ERR-ACAD-CLASS_DUPLICATE_NAME nếu trùng
    ├── List (Data Scoping):
    │     ├── Role Admin: Lấy toàn bộ lớp học trong DB (kể cả DELETED nếu có query param status)
    │     ├── Role Teacher: Tìm danh sách class_ids lớp chủ nhiệm + lớp phân công dạy -> Filter theo class_ids
    │     └── Role Student: Tìm danh sách class_ids lớp ghi danh -> Filter theo class_ids
    ├── Detail (Access Check): Kiểm tra class_id có nằm trong danh sách được phép của user -> Raise 403 ERR-ACAD-CLASS_ACCESS_DENIED nếu trái phép
    ├── Delete: Chuyển trạng thái status sang DELETED
    └── Restore: Tìm lớp học (bao gồm DELETED) -> Chuyển trạng thái status về ACTIVE
       │
       ▼
 4. Database Transaction & Output Serialization (ClassOut DTO)
```

## A.4 Acceptance Criteria

| AC ID | REQ | Given | When | Then |
|---|---|---|---|---|
| AC-01 | REQ-ACAD-011 | Admin đăng nhập, dữ liệu hợp lệ | `POST /api/v1/classes` | 201, trả về lớp vừa tạo |
| AC-02 | REQ-ACAD-011 | `school_year` không đúng định dạng `YYYY-YYYY` | `POST /api/v1/classes` | 422 Unprocessable Entity |
| AC-03 | REQ-ACAD-011 | `homeroom_teacher_id` không phải Teacher Active | `POST /api/v1/classes` | 400 `ERR-ACAD-INVALID_HOMEROOM_TEACHER` |
| AC-04 | REQ-ACAD-012 | Teacher/Student truy cập chi tiết lớp không thuộc phạm vi | `GET /api/v1/classes/{id}` | 403 `ERR-ACAD-CLASS_ACCESS_DENIED` |
| AC-05 | REQ-ACAD-014 | Lớp học tồn tại | `DELETE /api/v1/classes/{id}` | 204 |
| AC-06 | REQ-ACAD-015 | Lớp học đang `DELETED` | `POST /api/v1/classes/{id}/restore` | 200, status về `ACTIVE` |

---

# PART B — Architecture & API Design

> **Owner:** Tam Khang · **Gate:** G4

### Endpoints
1. `POST /api/v1/classes`: Tạo lớp học. Yêu cầu `ACAD_CLASS_MANAGE`.
2. `GET /api/v1/classes`: Danh sách lớp học (RBAC Data Scoping). Yêu cầu `ACAD_CLASS_VIEW`.
3. `GET /api/v1/classes/{class_id}`: Chi tiết lớp học (RBAC Data Scoping). Yêu cầu `ACAD_CLASS_VIEW`.
4. `PUT /api/v1/classes/{class_id}`: Cập nhật lớp học. Yêu cầu `ACAD_CLASS_MANAGE`.
5. `DELETE /api/v1/classes/{class_id}`: Xóa mềm lớp học. Yêu cầu `ACAD_CLASS_MANAGE`.
6. `POST /api/v1/classes/{class_id}/restore`: Khôi phục lớp học. Yêu cầu `ACAD_CLASS_MANAGE`.
