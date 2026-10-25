File Name: feature_seed_users.md
Created At: 2026-07-18
Created By: Tam Khang
Updated At: 2026-07-18
Updated By: Tam Khang

### Summary
Phát triển tính năng và script seed dữ liệu tài khoản mẫu (Admin, Teacher, Student) tương ứng với từng vai trò đang tồn tại trong cơ sở dữ liệu PostgreSQL.

### Feature Specifications
- Đọc thông tin vai trò trực tiếp từ bảng `roles` của DB PostgreSQL hiện tại để lấy `role_id` chính xác.
- Tạo tự động các tài khoản mẫu ở trạng thái kích hoạt (`Active`) với số điện thoại và email riêng biệt để tránh trùng lặp.
- Mật khẩu của tài khoản được mã hóa và băm bảo mật thông qua thư viện băm mật khẩu `bcrypt` của ứng dụng.
- Lưu lại thông tin các tài khoản đã băm thành công vào cấu trúc JSON để làm dữ liệu cấu hình/tham chiếu và hiển thị tài liệu hướng dẫn cho người dùng kiểm thử.

### Bug & Feature Context
- Khi chạy ứng dụng trên môi trường cục bộ, các vai trò (`Admin`, `Teacher`, `Student`) và các quyền/mối quan hệ đã được thiết lập qua script `seed.py`. Tuy nhiên, chưa có tài khoản người dùng mẫu nào được đăng ký sẵn trong DB PostgreSQL để kiểm thử luồng đăng nhập ngay lập tức.
- Yêu cầu đặt ra là khởi tạo các tài khoản đại diện cho từng vai trò trên để lập trình viên/người kiểm thử có thể đăng nhập ngay mà không cần qua quy trình đăng ký thủ công.

### Solution & Technical Details
- Viết script Python [seed_users.py](file:///c:/Users/LENOVO/tk_teacher_assistance_system/app/scripts/seed_users.py) sử dụng `SQLAlchemy` và nạp cấu hình cơ sở dữ liệu từ file `.env` qua `python-dotenv`.
- Thực hiện kiểm tra tính trùng lặp trước khi thêm mới dữ liệu bằng cách đối chiếu trường `phone` và `email`.
- Xuất kết quả sau khi thực thi ra file cấu hình [seed_accounts_info.json](file:///c:/Users/LENOVO/tk_teacher_assistance_system/app/scripts/seed_accounts_info.json) và trang tài liệu hướng dẫn kiểm thử [seed_accounts.md](file:///c:/Users/LENOVO/tk_teacher_assistance_system/docs/seed_accounts.md).
