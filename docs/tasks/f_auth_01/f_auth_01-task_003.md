# Task — F-AUTH-01-TASK-003: Login & Token Issuance Service

> Path: `docs/tasks/f_auth_01/f_auth_01-task_003.md`
> Slice: `S03` · Type: `SERVICE` · Size: `M` · SP: `3`
> Depends on: `F-AUTH-01-TASK-002`
> Status: `done`
> Created At: `2026-07-11`
> Updated At: `2026-07-16`
> Updated By: `Tam Khang`

---

## 1. Objective & Description
Xây dựng logic nghiệp vụ đăng nhập (`AuthService`), bao gồm: xác thực thông tin tài khoản (email/phone + password), kiểm tra trạng thái tài khoản, đếm số lần sai mật khẩu để hỗ trợ rate limit và phát hành JWT Access Token.

## 2. Input Context & Specs
- File đặc tả: [f_auth_01_spec.md](../../v_1/specs/f_auth_01_spec.md)
  - Section B.2.2: Critical data flow (login)
  - Section C.4: Main Flow
  - Section C.7: Business Rules (BR-01, BR-02, BR-04)
- Catalog lỗi: [error_codes.md](../../v_1/constraints/catalogs/error_codes.md)
- Utils bảo mật và JWT có sẵn từ foundation ([security.py](../../../app/core/security.py) hoặc [f_fnd_01_spec.md](../../v_1/specs/f_fnd_01_spec.md)).

## 3. Outputs
- **File tạo mới:** [auth_service.py](../../../app/modules/auth/services/auth_service.py)
- **Các hàm nghiệp vụ cần triển khai:**
  - `AuthService.authenticate_user(db: Session, identifier: str, password_plain: str) -> User`: Kiểm tra email trước, nếu không khớp thì kiểm tra phone. So sánh mật khẩu băm (`verify_password`).
  - `AuthService.issue_access_token(user: User) -> LoginResponse`: Tạo JWT token chứa claims: `sub` (User ID), `role` (tên Role hiện tại của User), `exp` (thời gian hết hạn dựa vào config `ACCESS_TOKEN_EXPIRE_MINUTES`).

## 4. Requirements & Acceptance Criteria
- **AC-01 (Mã lỗi đồng nhất):** Nếu không tìm thấy User hoặc sai mật khẩu, ném ra duy nhất lỗi `ERR-AUTH-INVALID_CREDENTIALS` (HTTP 401) để tránh bị rò rỉ sự tồn tại của tài khoản (User Enumeration).
- **AC-02 (Tài khoản bị khóa):** Nếu tài khoản có `status='Blocked'`, ném lỗi `ERR-AUTH-ACCOUNT_BLOCKED` (HTTP 403). Nếu tài khoản có `status='Inactive'`, ném lỗi `ERR-AUTH-ACCOUNT_INACTIVE` (HTTP 403).
- **AC-03 (Domain Events):** Ghi nhận hoặc phát đi các sự kiện (Domain Events) tương ứng:
  - Thành công: `EVT-AUTH-USER_LOGGED_IN`
  - Thất bại: `EVT-AUTH-LOGIN_FAILED`

## 5. Error Codes & Validation
- **`ERR-AUTH-INVALID_CREDENTIALS` (401):** Sai thông tin định danh hoặc mật khẩu.
- **`ERR-AUTH-ACCOUNT_BLOCKED` (403):** Tài khoản đã bị khóa.
- **`ERR-AUTH-ACCOUNT_INACTIVE` (403):** Tài khoản chưa được kích hoạt.
