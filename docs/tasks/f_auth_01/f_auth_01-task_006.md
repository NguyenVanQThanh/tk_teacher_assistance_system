# Task — F-AUTH-01-TASK-006: Change Password Feature

> Path: `docs/tasks/f_auth_01/f_auth_01-task_006.md`
> Slice: `S06` · Type: `SERVICE+API` · Size: `S` · SP: `1`
> Depends on: `F-AUTH-01-TASK-004`
> Status: `done`
> Created At: `2026-07-11`
> Updated At: `2026-07-17`
> Updated By: `Tam Khang`

---

## 1. Objective & Description
Xây dựng tính năng đổi mật khẩu cho người dùng hiện tại, bao gồm cả tầng Service logic và định nghĩa API Endpoint tương ứng.

## 2. Input Context & Specs
- File đặc tả: [f_auth_01_spec.md](../../v_1/specs/f_auth_01_spec.md)
  - Section C.7: Business Rules (BR-03)
  - Section C.8: Edge Cases (EC-07)
- Pydantic schema `ChangePasswordRequest` (Task 001).

## 3. Outputs
- **Các file tạo mới / chỉnh sửa:**
  - [password_service.py](../../../app/modules/auth/services/password_service.py) (hoặc gộp chung vào `AuthService`)
  - Tích hợp thêm route vào [auth.py](../../../app/modules/auth/routers/auth.py):
    - `POST /api/v1/auth/change-password`
    - Bảo vệ bởi: `Depends(get_current_user)` và yêu cầu quyền `AUTH_PASSWORD_CHANGE`.
    - Body: `ChangePasswordRequest`
    - Response (200): `{status: "ok"}`

## 4. Requirements & Acceptance Criteria
- **AC-01 (Mật khẩu cũ):** Phải xác thực mật khẩu cũ (`old_password`) trùng khớp với mật khẩu đang lưu trong DB qua hash. Nếu sai, ném lỗi `ERR-AUTH-INVALID_CREDENTIALS` (hoặc `ERR-AUTH-WRONG_OLD_PASSWORD` nếu catalog cho phép).
- **AC-02 (Trùng mật khẩu mới):** Kiểm tra xem mật khẩu mới có trùng với mật khẩu cũ hay không. Nếu trùng, trả lỗi `ERR-AUTH-PASSWORD_REUSE` (HTTP 400).
- **AC-03 (Lưu hash mới):** Tiến hành băm mật khẩu mới bằng thuật toán bcrypt và lưu vào cơ sở dữ liệu.
- **AC-04 (Event):** Phát sinh sự kiện `EVT-AUTH-PASSWORD_CHANGED`.

## 5. Error Codes & Validation
- **`ERR-AUTH-INVALID_CREDENTIALS` (401):** Nhập sai mật khẩu cũ.
- **`ERR-AUTH-PASSWORD_REUSE` (400):** Mật khẩu mới trùng với mật khẩu cũ.
