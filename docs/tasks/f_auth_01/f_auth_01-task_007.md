# Task — F-AUTH-01-TASK-007: Login Rate Limit Middleware

> Path: `docs/tasks/f_auth_01/f_auth_01-task_007.md`
> Slice: `S07` · Type: `MIDDLEWARE` · Size: `S` · SP: `1`
> Depends on: `F-AUTH-01-TASK-005`
> Status: `ready to test`
> Created At: `2026-07-11`
> Updated At: `2026-07-17`
> Updated By: `Tam Khang`

---

## 1. Objective & Description
Triển khai cơ chế Rate Limiting cho API đăng nhập để chống brute-force mật khẩu. Khi người dùng nhập sai mật khẩu quá 5 lần trong vòng 5 phút, tài khoản hoặc IP/số điện thoại (`phone`) đăng nhập đó sẽ bị khóa tạm thời trong vòng 5 phút.

## 2. Input Context & Specs
- File đặc tả: [f_auth_01_spec.md](../../v_1/specs/f_auth_01_spec.md)
  - Section B.8: Security & Privacy (Rate limit: 5 lần sai / 5 phút / phone)
  - Section C.7: Business Rules (BR-05)
  - Section C.8: Edge Cases (EC-06)
- Thư viện giới hạn request: `slowapi` (hoặc custom middleware).

## 3. Outputs
- **File tạo mới / chỉnh sửa:**
  - [rate_limit.py](../../../app/core/rate_limit.py) (khởi tạo Limiter)
  - Áp dụng limiter lên route đăng nhập trong [auth.py](../../../app/modules/auth/routers/auth.py).

## 4. Requirements & Acceptance Criteria
- **AC-01 (Giới hạn Brute-force):** Nếu nhập sai mật khẩu quá 5 lần trong vòng 5 phút đối với cùng một số điện thoại (`phone`), hệ thống từ chối đăng nhập ngay từ bước middleware mà không cần kiểm tra password tiếp.
- **AC-02 (HTTP Response):** Khi bị giới hạn, trả về mã lỗi HTTP `429 Too Many Requests` và mã lỗi trong envelope là `ERR-AUTH-TOO_MANY_ATTEMPTS`.
- **AC-03 (Header):** Response trả về phải chứa header `Retry-After` biểu thị số giây còn lại cần chờ trước khi có thể thử lại.

## 5. Error Codes & Validation
- **`ERR-AUTH-TOO_MANY_ATTEMPTS` (429):** Quá số lần thử đăng nhập cho phép, tài khoản bị tạm khóa.
