> Path: `docs/tasks/f_admin_02/f_admin_02_role_permissions.md`
> Slice: `SL-ADMIN-02` · Type: `feature` · Size: `medium` · SP: `5`
> Depends on: `F-AUTH-01`
> Status: `draft`
> Created At: `2026-10-27`
> Updated At: `2026-10-27`

# Task — `F-ADMIN-02` Admin Role & Permission Management (Quản lý Ma trận Phân quyền & Ghi đè Quyền)

**Created By:** Tam Khang  
**Updated By:** Tam Khang  

## Mô tả Task
Triển khai các API quản trị Ma trận Phân quyền theo Vai trò (`role_permissions`) và Ghi đè Quyền cá nhân (`user_permissions`) phục vụ màn hình `AdminRolesPage.jsx`:
1. Pydantic Schemas: `RoleWithStatsOut`, `PermissionCatalogItemOut`, `RolePermissionUpdateRequest`, `UserEffectivePermissionOut`, `UserPermissionOverrideRequest`.
2. Service Layer (`AdminRoleService`):
   - Liệt kê danh sách các `Role` kèm số lượng người dùng (`user_count`) và danh sách `permission_code`.
   - Liệt kê toàn bộ danh mục `Permission` gom nhóm theo `module`.
   - Cập nhật danh sách quyền của một `Role` (`PUT /api/v1/admin/roles/{role_id}/permissions`).
   - Xem và cấu hình ghi đè quyền cá nhân (`allow` / `deny`) trong bảng `user_permissions` với nguyên tắc **Deny Overrides Allow**.
3. API Router (`app/modules/admin/routers/roles.py`): 5 endpoints bảo vệ bởi `ADMIN_ROLE_MANAGE`.
4. Tích hợp Frontend: Khai báo `adminRolesApi` trong `frontend/src/services/api.js` và nối vào `AdminRolesPage.jsx`.

## Checklist Thực Hiện
- [ ] Seed permission `ADMIN_ROLE_MANAGE` cho role `Admin`.
- [ ] Xây dựng `AdminRoleService` và router `app/modules/admin/routers/roles.py`.
- [ ] Cập nhật `frontend/src/services/api.js` (`adminRolesApi`).
- [ ] Kết nối dữ liệu thật vào `AdminRolesPage.jsx`, loại bỏ state giả lập.
- [ ] Viết Unit & Integration Tests (`pytest tests/admin/test_roles.py`) đạt 100% pass rate.

