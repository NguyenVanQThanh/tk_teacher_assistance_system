# Seed Accounts Reference

> Path: `docs/seed_accounts.md`
> Created At: 2026-07-18
> Created By: Tam Khang
> Updated At: 2026-07-18
> Updated By: Tam Khang

Dưới đây là danh sách các tài khoản mẫu (seed accounts) đã được khởi tạo trong cơ sở dữ liệu PostgreSQL cho từng vai trò (role) phục vụ quá trình phát triển và kiểm thử hệ thống.

## Danh sách tài khoản

| Vai trò (Role) | Số điện thoại | Email | Họ và tên | Mật khẩu mặc định | Trạng thái |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Admin** | `0999000001` | `admin@school.com` | Quản trị viên Hệ thống | `Admin@1234` | `Active` |
| **Teacher** | `0999000002` | `teacher@school.com` | Giáo viên Mẫu | `Teacher@1234` | `Active` |
| **Student** | `0999000003` | `student@school.com` | Học sinh Mẫu | `Student@1234` | `Active` |

## Thông tin chi tiết UUID
- **Admin**: `933ec651-ecf2-4b43-9676-a987c29d2dad`
- **Teacher**: `808c8232-f550-4a89-abfe-5372ed77a36e`
- **Student**: `4f64cb51-9d51-4c12-aab4-1aa757cea9ba`

> [!NOTE]
> Tất cả các mật khẩu đều được băm bằng thuật toán `bcrypt` an toàn và lưu trữ trong bảng `users` của cơ sở dữ liệu.
