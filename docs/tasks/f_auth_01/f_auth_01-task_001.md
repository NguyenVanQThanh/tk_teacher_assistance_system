# Task — F-AUTH-01-TASK-001: Auth Pydantic Schemas

> Path: `docs/tasks/f_auth_01/f_auth_01-task_001.md`
> Slice: `S01` · Type: `SCHEMA` · Size: `S` · SP: `1`
> Depends on: `F-FND-01`
> Status: `ready to test`
> Created At: `2026-07-11`
> Updated At: `2026-07-17`
> Updated By: `Tam Khang`

---

## 1. Objective & Description
Xây dựng các Pydantic schema cần thiết cho module Authentication để phục vụ validation dữ liệu đầu vào và định cấu trúc dữ liệu đầu ra cho các API đăng nhập, đổi mật khẩu và xem profile người dùng.

## 2. Input Context & Specs
- File đặc tả: [f_auth_01_spec.md](../../v_1/specs/f_auth_01_spec.md)
  - Section C.2: Input Specification (identifier, password, old_password, new_password)
  - Section C.3: Output Specification
  - Section C.5: API Contract
- File đặc tả foundation: [f_fnd_01_spec.md](../../v_1/specs/f_fnd_01_spec.md) (để tham khảo cấu trúc error envelope)

## 3. Outputs
- **File tạo mới:** [schemas.py](../../../app/modules/auth/schemas.py)
- **Các Pydantic model cần định nghĩa:**
  - `LoginRequest`:
    - `phone` (số điện thoại, bắt buộc) và có config regex validate cho phone number của Việt Nam (từ 10 số).
    - `password` (chuỗi dài từ 1..128 ký tự, bắt buộc).
  - `UserOut`:
    - `user_id` (UUID).
    - `full_name` (str).
    - `role` (str - tên vai trò).
    - `email_masked` (chuỗi đã được che giấu phần đầu để bảo mật PII, ví dụ: `u***@email.com`).
    - `phone_masked` (chuỗi đã được che giấu phần đầu để bảo mật PII, ví dụ: `0******123`).
  - `LoginResponse`:
    - `access_token` (str).
    - `token_type` (mặc định là `"bearer"`).
    - `expires_in` (int - số giây hiệu lực).
    - `user` (`UserOut`).
  - `ChangePasswordRequest`:
    - `old_password` (str, bắt buộc).
    - `new_password` (str, dài tối thiểu 8 ký tự, bắt buộc, khác `old_password`).

## 4. Requirements & Acceptance Criteria
- **AC-01 (Validation):** Khi dữ liệu đầu vào không hợp lệ (ví dụ: thiếu `identifier`, `password` rỗng, hoặc `new_password` ngắn hơn 8 ký tự), hệ thống phải tự động trả về mã lỗi validation mặc định của FastAPI (`422 Unprocessable Entity`) và phản hồi theo chuẩn error envelope.
- **AC-02 (Security):** `password_hash` và mật khẩu gốc tuyệt đối không bao giờ được định nghĩa trong schema đầu ra `UserOut` hay bất kỳ schema trả về client nào.

## 5. Error Codes & Validation
- Nếu validation lỗi, FastAPI tự động xử lý qua exception handler mặc định và trả về danh sách lỗi chi tiết trong envelope.
