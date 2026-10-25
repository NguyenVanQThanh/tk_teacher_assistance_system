# Task — F-AUTH-01-TASK-005: Auth API Endpoints

> Path: `docs/tasks/f_auth_01/f_auth_01-task_005.md`
> Slice: `S05` · Type: `API` · Size: `M` · SP: `2`
> Depends on: `F-AUTH-01-TASK-003` và `F-AUTH-01-TASK-004`
> Status: `done`
> Created At: `2026-07-11`
> Updated At: `2026-07-17`
> Updated By: `Tam Khang`


---

## 1. Objective & Description
Xây dựng các router API endpoint để phục vụ cho các yêu cầu xác thực của client bao gồm Login, xem thông tin tài khoản hiện tại (/me), và Logout.

## 2. Input Context & Specs
- File đặc tả: [f_auth_01_spec.md](../../v_1/specs/f_auth_01_spec.md)
  - Section B.6: API Boundary
  - Section C.3: Output Specification
  - Section C.5: API Contract
  - Section C.7: Business Rules (BR-06)

## 3. Outputs
- **File tạo mới:** [auth.py](../../../app/modules/auth/routers/auth.py)
- **Các endpoints cần định nghĩa:**
  - `POST /api/v1/auth/login`:
    - Body: `LoginRequest`
    - Response (200): `LoginResponse`
  - `GET /api/v1/auth/me`:
    - Bảo vệ bởi: `Depends(get_current_user)` và yêu cầu quyền `AUTH_ME_VIEW`.
    - Response (200): `UserOut`
  - `POST /api/v1/auth/logout`:
    - Bảo vệ bởi: `Depends(get_current_user)`.
    - Phản hồi 200 `{status: "ok"}`. Vì là stateless logout nên client chịu trách nhiệm xóa token khỏi local storage.

## 4. Requirements & Acceptance Criteria
- **AC-01 (API Contract):** Response trả về từ API `/login` và `/me` phải khớp chính xác kiểu dữ liệu được mô tả trong Pydantic schemas (Task 001) và không rò rỉ các thông tin nhạy cảm.
- **AC-02 (Stateless Logout):** API logout không cần lưu trạng thái token bị hủy (Sprint 0), chỉ cần trả về thành công để client tự động xóa token của nó.

## 5. Error Codes & Validation
- **`ERR-AUTH-INVALID_CREDENTIALS` (401):** Sai credential khi đăng nhập.
- **`ERR-AUTH-MISSING_TOKEN` (401):** Không gửi kèm token khi gọi `/me` hoặc `/logout`.
- **`ERR-AUTH-INVALID_TOKEN` (401):** Token hết hạn hoặc không hợp lệ khi gọi `/me` hoặc `/logout`.
- **`ERR-AUTH-FORBIDDEN` (403):** User không có quyền `AUTH_ME_VIEW` (hiếm gặp vì mặc định mọi role đều có).
