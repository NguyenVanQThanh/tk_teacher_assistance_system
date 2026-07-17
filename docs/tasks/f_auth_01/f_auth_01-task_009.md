# Task — F-AUTH-01-TASK-009: Alembic Migration & Seed Permissions & Roles

> Path: `docs/tasks/f_auth_01/f_auth_01-task_009.md`
> Slice: `S09` · Type: `MIG+SEED` · Size: `M` · SP: `2`
> Depends on: `F-FND-01`
> Status: `ready to test`
> Created At: `2026-07-11`
> Updated At: `2026-07-17`
> Updated By: `Tam Khang`

---

## 1. Objective & Description
Thiết lập cơ sở dữ liệu cho hệ thống phân quyền RBAC (Role-Based Access Control) mịn theo permission và override user. Tạo migration DB cho 3 bảng phân quyền mới và thực hiện seed dữ liệu mặc định ban đầu đảm bảo tính idempotent.

## 2. Input Context & Specs
- File đặc tả: [f_auth_01_spec.md](../../v_1/specs/f_auth_01_spec.md)
  - Section B.3: Domain Ownership Matrix
  - Section B.7: Database Boundary
  - Section C.1: User Roles & Permissions
  - Section C.7: Business Rules (BR-07, BR-08, BR-09, BR-10)

## 3. Outputs
- **SQLAlchemy Models:** [models.py](../../../app/modules/auth/models.py) (Định nghĩa `Permission`, `RolePermission`, `UserPermission`)
- **Alembic Migration Script:** `alembic/versions/{rev}_create_rbac_tables.py`
- **Seed Script:** [seed.py](../../../app/scripts/seed.py) (hoặc cập nhật file seed.py hiện tại)

## 4. Requirements & Acceptance Criteria
- **AC-01 (Database Tables & Columns):**
  - Bảng `permissions`:
    - `permission_id` (UUID, primary key)
    - `permission_code` (VARCHAR, unique, ví dụ: `AUTH_ME_VIEW`)
    - `name` (VARCHAR)
    - `description` (TEXT)
  - Bảng `role_permissions`:
    - `role_id` (UUID, foreign key tham chiếu đến `roles`, CASCADE on delete)
    - `permission_id` (UUID, foreign key tham chiếu đến `permissions`, CASCADE on delete)
    - Primary key constraint: (`role_id`, `permission_id`)
  - Bảng `user_permissions`:
    - `user_id` (UUID, foreign key tham chiếu đến `users`, CASCADE on delete)
    - `permission_id` (UUID, foreign key tham chiếu đến `permissions`, CASCADE on delete)
    - `effect` (VARCHAR, chỉ cho phép nhận giá trị `'allow'` hoặc `'deny'`)
    - Primary key constraint: (`user_id`, `permission_id`)
- **AC-02 (Seed Data Idempotent):**
  - Phải seed 3 permission code: `AUTH_ME_VIEW`, `AUTH_PASSWORD_CHANGE`, `AUTH_PERM_MANAGE`.
  - Thiết lập mapping role-permission mặc định:
    - **Admin:** `AUTH_ME_VIEW`, `AUTH_PASSWORD_CHANGE`, `AUTH_PERM_MANAGE`.
    - **Teacher (GiaoVien):** `AUTH_ME_VIEW`, `AUTH_PASSWORD_CHANGE`.
    - **Student (HocSinh):** `AUTH_ME_VIEW`, `AUTH_PASSWORD_CHANGE`.
  - Script seed có thể chạy lại nhiều lần mà không bị duplicate bản ghi hoặc crash (Sử dụng lệnh kiểm tra hoặc `ON CONFLICT DO NOTHING`).

## 5. Error Codes & Validation
- Nếu chạy migration hoặc seed lỗi, quá trình deploy sẽ dừng lại.
- Dữ liệu `effect` trong bảng `user_permissions` bắt buộc phải được giới hạn bằng `CheckConstraint("effect IN ('allow', 'deny')", name='chk_user_perm_effect')` ở DB level.
