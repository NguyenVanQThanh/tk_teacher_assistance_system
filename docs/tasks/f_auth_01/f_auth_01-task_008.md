# Task — F-AUTH-01-TASK-008: Auth & RBAC Automated Tests

> Path: `docs/tasks/f_auth_01/f_auth_01-task_008.md`
> Slice: `S08` · Type: `TEST` · Size: `M` · SP: `2`
> Depends on: `F-AUTH-01-TASK-005`, `F-AUTH-01-TASK-006` và `F-AUTH-01-TASK-007`
> Status: `ready to test`
> Created At: `2026-07-11`
> Updated At: `2026-07-17`
> Updated By: `Tam Khang`

---

## 1. Objective & Description
Xây dựng bộ kiểm thử tự động (Unit, Integration và E2E tests) cho toàn bộ các chức năng thuộc module Authentication & RBAC nhằm đảm bảo tính đúng đắn của logic xác thực, phân quyền và khả năng bảo mật của hệ thống.

## 2. Input Context & Specs
- File đặc tả: [f_auth_01_spec.md](../../v_1/specs/f_auth_01_spec.md)
  - Section C.8: Edge Cases (từ EC-01 đến EC-08)
  - Section C.10: Test Strategy

## 3. Outputs
- **Các file test tạo mới trong thư mục [tests/auth/](../../../tests/auth):**
  - [test_security.py](../../../tests/auth/unit/test_security.py) (Mật khẩu, JWT token decode)
  - [test_login.py](../../../tests/auth/integration/test_login.py) (Login flow, DB query, error codes)
  - [test_password.py](../../../tests/auth/integration/test_password.py) (Đổi mật khẩu và các edge case)
  - [test_rbac.py](../../../tests/auth/integration/test_rbac.py) (Quyền hiệu lực, allow/deny override)
  - [test_auth_flow.py](../../../tests/auth/e2e/test_auth_flow.py) (Giả lập client gửi request đầy đủ)

## 4. Requirements & Acceptance Criteria
- **AC-01 (Unit Tests):** Đảm bảo test được logic băm mật khẩu, so khớp mật khẩu và mã hóa/giải mã JWT.
- **AC-02 (Integration Tests - Edge Cases):**
  - **EC-01:** Login với số điện thoại (`phone`) không tồn tại -> `ERR-AUTH-INVALID_CREDENTIALS` (401).
  - **EC-02:** Đúng password nhưng user bị Blocked -> `ERR-AUTH-ACCOUNT_BLOCKED` (403).
  - **EC-03:** Token hết hạn -> `ERR-AUTH-INVALID_TOKEN` (401).
  - **EC-04:** Chữ ký token sai hoặc bị sửa đổi -> `ERR-AUTH-INVALID_TOKEN` (401).
  - **EC-05:** Thiếu quyền -> `ERR-AUTH-FORBIDDEN` (403).
  - **EC-05b (Override Deny):** Role của user được phép nhưng user bị cấm riêng (`deny`) -> `ERR-AUTH-FORBIDDEN` (403).
  - **EC-05c (Override Allow):** Role của user không được phép nhưng user được cấp riêng (`allow`) -> Cho phép truy cập (200).
  - **EC-06:** Nhập sai mật khẩu liên tục 5 lần -> `ERR-AUTH-TOO_MANY_ATTEMPTS` (429).
  - **EC-07:** Đổi mật khẩu mới trùng mật khẩu cũ -> `ERR-AUTH-PASSWORD_REUSE` (400).
  - **EC-08:** Thiếu header Authorization khi gọi endpoint bảo mật -> `ERR-AUTH-MISSING_TOKEN` (401).
- **AC-03 (Coverage):** Đạt tối thiểu 80% coverage cho phần code của module Auth.

## 5. Verification Commands
```bash
# Run unit + service tests
pytest tests/auth -k "unit or service"

# Run integration + e2e tests
pytest tests/auth/integration tests/auth/e2e

# Run full gate lint and tests
ruff check . && mypy app && pytest --cov=app
```
