File Name: feature_rbac_baseline_and_dependencies.md
Created At: 2026-07-17
Created By: Tam Khang
Updated At: 2026-07-17
Updated By: Tam Khang

### Summary
Hoàn thành thiết lập cơ sở dữ liệu phân quyền RBAC, cơ chế seed dữ liệu Việt hóa và các FastAPI dependency phục vụ xác thực người dùng cũng như phân quyền mịn đến mức usecase/endpoint.

### Feature Specifications
- **AC-01 (Database Models)**: Tích hợp định nghĩa các bảng `permissions`, `role_permissions`, và `user_permissions` (có CheckConstraint `'effect IN ('allow', 'deny')'`) và ánh xạ sang SQLAlchemy models.
- **AC-02 (Seeding Idempotent)**: Hỗ trợ seed dữ liệu mặc định gồm 3 permissions: `AUTH_ME_VIEW`, `AUTH_PASSWORD_CHANGE`, `AUTH_PERM_MANAGE` và ánh xạ vai trò (`Admin`, `Teacher`, `Student`) bằng Tiếng Việt. Script tự động cập nhật bản ghi trong DB nếu mô tả thay đổi mà không tạo trùng.
- **AC-03 (Permission calculation)**: Giải quyết quyền hiệu lực của người dùng theo công thức: (Quyền vai trò + Quyền allow riêng) - Quyền deny riêng. Quyền deny luôn có mức ưu tiên cao nhất.
- **AC-04 (Role Cache)**: Cache in-memory tập quyền của các role để tối ưu hiệu năng. Hỗ trợ cơ chế làm trống cache khi cấu hình thay đổi. Không cache các ghi đè cá nhân (`user_permissions`).
- **AC-05 (Authentication & Authorization dependencies)**:
  - `get_current_user`: Trích xuất token từ header, giải mã và xác thực chữ ký JWT, kiểm tra trạng thái người dùng (Blocked/Inactive) và trả về lỗi chuẩn hóa Tiếng Việt.
  - `require_perm`: Fail-closed check chặn request nếu người dùng không sở hữu quyền cần thiết.

### Solution & Technical Details
- **Database Helper**: [database.py](file:///c:/Users/LENOVO/tk_teacher_assistance_system/app/core/database.py) cung cấp engine và dependency `get_db`.
- **Permission Repository**: [permission_repository.py](file:///c:/Users/LENOVO/tk_teacher_assistance_system/app/modules/auth/permission_repository.py) cung cấp các truy vấn DB tham số hóa chống SQL Injection.
- **Permission Service**: [permission_service.py](file:///c:/Users/LENOVO/tk_teacher_assistance_system/app/modules/auth/services/permission_service.py) giải quyết logic cache in-memory và tính toán quyền hiệu lực.
- **Dependencies**: [dependencies.py](file:///c:/Users/LENOVO/tk_teacher_assistance_system/app/modules/auth/dependencies.py) thực thi xác thực JWT và phân quyền fail-closed.
- **Seed Script**: [seed.py](file:///c:/Users/LENOVO/tk_teacher_assistance_system/app/scripts/seed.py) seed dữ liệu idempotent có Việt hóa.
