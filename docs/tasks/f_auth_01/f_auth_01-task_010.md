# Task — F-AUTH-01-TASK-010: Permission Repository

> Path: `docs/tasks/f_auth_01/f_auth_01-task_010.md`
> Slice: `S10` · Type: `REPO` · Size: `S` · SP: `1`
> Depends on: `F-AUTH-01-TASK-009`
> Status: `done`
> Created At: `2026-07-11`
> Updated At: `2026-07-17`
> Updated By: `Tam Khang`

---

## 1. Objective & Description
Xây dựng Repository cho phần phân quyền (`PermissionRepository`) để thực hiện các truy vấn đọc danh sách quyền gắn liền với vai trò (Role Permissions) và các quyền được ghi đè ở mức người dùng (User Permission Overrides).

## 2. Input Context & Specs
- File đặc tả: [f_auth_01_spec.md](../../v_1/specs/f_auth_01_spec.md)
  - Section B.3: Domain Ownership Matrix
  - Section C.1: User Roles & Permissions
  - Section C.7: Business Rules (BR-07, BR-09, BR-10)

## 3. Outputs
- **File tạo mới:** [permission_repository.py](../../../app/modules/auth/permission_repository.py)
- **Các hàm cần triển khai:**
  - `PermissionRepository.get_permissions_by_role(db: Session, role_id: UUID) -> List[str]`: Lấy danh sách `permission_code` thuộc về vai trò `role_id` từ bảng `role_permissions` join `permissions`.
  - `PermissionRepository.get_user_permission_overrides(db: Session, user_id: UUID) -> List[Tuple[str, str]]`: Lấy danh sách các bản ghi đè (`permission_code`, `effect`) của người dùng `user_id` từ bảng `user_permissions` join `permissions`.

## 4. Requirements & Acceptance Criteria
- **AC-01 (DB Query):** Các câu truy vấn join DB phải chính xác, chỉ lấy các trường cần thiết (`permission_code` và `effect`).
- **AC-02 (SQL Injection):** Không dùng raw string SQL chắp vá bừa bãi, sử dụng SQLAlchemy ORM query hoặc select statement được tham số hóa đầy đủ.

## 5. Error Codes & Validation
- Trả về danh sách trống `[]` nếu vai trò hoặc người dùng không có bất kỳ cấu hình quyền / ghi đè nào.
