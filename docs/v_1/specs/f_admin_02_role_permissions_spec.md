# Feature Spec — `F-ADMIN-02` Role & Permission Management (Phân quyền & Ghi đè Quyền)

> Path: `docs/v_1/specs/f_admin_02_role_permissions_spec.md` · Sprint: [sprint_3_overview.md](../sprints/sprint_3_overview.md)  
> Created At: `2026-09-23`  
> Created By: `Tam Khang`  
> Updated At: `2026-09-23`  
> Updated By: `Tam Khang`  

---

## Document Header

| Field | Giá trị |
|---|---|
| **Feature ID** | `F-ADMIN-02` |
| **Feature Name** | Role & Permission Management — Quản lý Ma trận Phân quyền & Ghi đè Quyền cá nhân |
| **Module(s)** | `admin`, `auth` |
| **Sprint(s) Allocated** | `SPRINT-03` |
| **Spec Version** | `v1.0` |
| **Last Updated** | `2026-09-23` |
| **Source Binding** | `models/models.py` (`roles`, `permissions`, `role_permissions`, `user_permissions`) · `f_auth_01_spec.md` |

---

# PART A — Business & Requirements

> **Owner:** Tam Khang · **Gate:** G3

## A.1 Feature Summary

Cung cấp cho **Quản trị viên (Admin)** giao diện trực quan và hệ thống API để quản lý phân quyền theo mô hình **RBAC (Role-Based Access Control) mở rộng**:
1. Tra cứu danh mục toàn bộ quyền hạn trong hệ thống theo từng nhóm module (`academic`, `exercise`, `admin`, `tracking`).
2. Tùy chỉnh danh sách quyền hạn gán cho từng vai trò (`Admin`, `Teacher`, `Student`, `HomeroomTeacher`).
3. Cơ chế **Ghi đè quyền cá nhân (Individual Permission Override)**: Cho phép cấp bổ sung quyền hoặc thu hồi/chặn quyền cụ thể của một tài khoản (`user_permissions`), với nguyên tắc **Quyền bị từ chối (Deny) luôn luôn phủ quyết quyền được phép (Allow)**.

## A.2 User Stories

| Story ID | As (Role) | I Want (Capability) | So That (Value) |
|---|---|---|---|
| **US-01** | Admin | Xem danh mục toàn bộ quyền (Permissions) và số lượng người dùng theo từng vai trò | Nắm bắt tổng quan cấu trúc phân quyền hệ thống |
| **US-02** | Admin | Bật/tắt các quyền hạn được gán cho một vai trò | Linh hoạt điều chỉnh chính sách phân quyền trường học |
| **US-03** | Admin | Cấp thêm quyền đặc biệt cho một giáo viên cụ thể (vd: GV chủ nhiệm được quyền tạo đề thi chung) | Không cần tạo thêm vai trò mới phức tạp |
| **US-04** | Admin | Thu hồi/chặn một quyền cụ thể của một người dùng | Kiểm soát rủi ro an ninh khi người dùng vi phạm quy chế |

---

# PART B — Technical Specifications & API Contracts

## B.1 API Endpoints

### 1. `GET /api/v1/admin/roles`
* **Permission**: `ADMIN_ROLE_MANAGE`
* **Response `200 OK`**:
```json
[
  {
    "id": "role-uuid-1",
    "name": "Teacher",
    "description": "Giáo viên bộ môn và giáo viên chủ nhiệm",
    "user_count": 48,
    "permissions": ["ACAD_CLASS_VIEW", "EXE_EXERCISE_MANAGE", "EXE_ASSIGNMENT_MANAGE", "EXE_ATTEMPT_VIEW"]
  }
]
```

### 2. `GET /api/v1/admin/permissions`
* **Permission**: `ADMIN_ROLE_MANAGE`
* **Response `200 OK`**: Danh sách tất cả các quyền được gom nhóm theo module (`module`, `code`, `name`, `description`).

### 3. `PUT /api/v1/admin/roles/{role_id}/permissions`
* **Permission**: `ADMIN_ROLE_MANAGE`
* **Request Body**:
```json
{
  "permission_codes": [
    "ACAD_CLASS_VIEW",
    "EXE_EXERCISE_MANAGE",
    "EXE_ASSIGNMENT_MANAGE",
    "EXE_ATTEMPT_VIEW"
  ]
}
```
* **Response `200 OK`**: Role Object kèm danh sách quyền mới.

### 4. `GET /api/v1/admin/users/{user_id}/permissions`
* **Permission**: `ADMIN_ROLE_MANAGE`
* **Response `200 OK`**: Bảng tổng hợp quyền hiệu lực của người dùng (`effective_permissions`), gồm các quyền từ Role gốc và danh sách ghi đè (`granted_overrides`, `revoked_overrides`).

### 5. `PUT /api/v1/admin/users/{user_id}/permissions`
* **Permission**: `ADMIN_ROLE_MANAGE`
* **Request Body**:
```json
{
  "granted_permissions": ["EXE_QUESTION_IMPORT"],
  "revoked_permissions": ["ACAD_TEACHER_ASSIGN_VIEW"]
}
```
* **Response `200 OK`**: Bảng quyền hiệu lực sau khi cập nhật.
