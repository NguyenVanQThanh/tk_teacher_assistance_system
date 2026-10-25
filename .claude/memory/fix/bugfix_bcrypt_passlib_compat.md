File Name: bugfix_bcrypt_passlib_compat.md
Created At: 2026-07-18
Created By: Tam Khang
Updated At: 2026-07-18
Updated By: Tam Khang

### Summary
Sửa lỗi `ValueError` (độ dài mật khẩu băm vượt quá 72 bytes) và lỗi `AttributeError` (thiếu thuộc tính `__about__` trong module `bcrypt`) khi sử dụng thư viện `passlib` kết hợp với `bcrypt >= 4.0` trên môi trường Python 3.13.

### Feature Specifications
- Đăng ký tài khoản mới (`/register`).
- Đăng nhập hệ thống (`/login`).
- Xác thực mật khẩu và tạo mã băm mật khẩu bảo mật bằng bcrypt thông qua `passlib.context.CryptContext`.

### Bug & Feature Context
- **Lỗi 1 (`ValueError`)**: Thư viện `bcrypt >= 4.0` kiểm tra chặt chẽ độ dài chuỗi byte mật khẩu đầu vào (không vượt quá 72 bytes). Khi `passlib` băm mật khẩu, nếu không được cắt chuỗi thủ công, `bcrypt` sẽ quăng ra ngoại lệ `ValueError: password cannot be longer than 72 bytes, truncate manually if necessary`.
- **Lỗi 2 (`AttributeError`)**: Thư viện `passlib` phiên bản cũ cố gắng đọc phiên bản bcrypt qua `_bcrypt.__about__.__version__`. Trong phiên bản `bcrypt >= 4.0.0` (đặc biệt là 5.0.0), thuộc tính `__about__` bị loại bỏ, dẫn tới lỗi `AttributeError: module 'bcrypt' has no attribute '__about__'`.
- **Ảnh hưởng**: Lỗi này chỉ xảy ra khi chạy ứng dụng thực tế (`python -m app.main`) vì môi trường test đã cấu hình monkeypatch trong `conftest.py`, khiến lỗi không xuất hiện khi chạy pytest.

### Solution & Technical Details
Tôi đã thêm cấu hình monkeypatch trực tiếp vào đầu file [security.py](file:///c:/Users/LENOVO/tk_teacher_assistance_system/app/core/security.py) để áp dụng cho toàn bộ ứng dụng khi chạy thực tế:
1. Tạo lớp giả lập `DummyAbout` gán vào `bcrypt.__about__` để tránh lỗi `AttributeError` trong `passlib`.
2. Ghi đè phương thức `bcrypt.hashpw` để tự động cắt chuỗi byte mật khẩu về tối đa 72 bytes trước khi băm, loại bỏ lỗi `ValueError`.

Các file thay đổi:
- [security.py](file:///c:/Users/LENOVO/tk_teacher_assistance_system/app/core/security.py)
