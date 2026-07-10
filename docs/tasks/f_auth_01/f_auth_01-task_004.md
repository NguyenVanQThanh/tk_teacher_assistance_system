# Task — F-AUTH-01-TASK-004: FastAPI Dependencies & Effective Permission Resolver

> Path: `docs/tasks/f_auth_01/f_auth_01-task_004.md`
> Slice: `S04` · Type: `DEPENDENCY` · Size: `M` · SP: `3`
> Depends on: `F-AUTH-01-TASK-003` và `F-AUTH-01-TASK-010`
> Status: `draft`
> Created At: `2026-07-11`
> Updated At: `2026-07-11`

---

## 1. Objective & Description
Thiết lập các FastAPI dependency để trích xuất/xác thực user từ token (`get_current_user`), tính toán tập quyền hiệu lực (effective permissions) cho user và thực hiện phân quyền mịn đến mức usecase/endpoint (`require_perm`).

## 2. Input Context & Specs
- File đặc tả: [f_auth_01_spec.md](../../v_1/specs/f_auth_01_spec.md)
  - Section B.4: Core Invariants (INV-AUTH-04, INV-AUTH-05, INV-AUTH-06)
  - Section C.7: Business Rules (BR-07, BR-08, BR-09, BR-10)
- [permission_repository.py](../../../app/modules/auth/permission_repository.py)

## 3. Outputs
- **Các file tạo mới:**
  - [dependencies.py](../../../app/modules/auth/dependencies.py)
  - [permission_service.py](../../../app/modules/auth/services/permission_service.py)

## 4. Requirements & Acceptance Criteria
- **AC-01 (Token Authentication):**
  - Dependency `get_current_user` parse token từ header `Authorization: Bearer <token>`.
  - Nếu thiếu token, trả lỗi `ERR-AUTH-MISSING_TOKEN` (HTTP 401).
  - Nếu token hết hạn hoặc sai chữ ký, trả lỗi `ERR-AUTH-INVALID_TOKEN` (HTTP 401).
- **AC-02 (Effective Permissions Calculation):**
  - Tập quyền hiệu lực = Quyền của Role (`role_permissions`) ∪ Quyền được cấp riêng (`user_permissions(allow)`) − Quyền bị cấm riêng (`user_permissions(deny)`).
  - **Mức ưu tiên:** Quyền **Deny luôn thắng** mọi quyền Allow.
- **AC-03 (Role Cache):**
  - Nhằm tránh truy vấn lặp lại, danh sách quyền của Role phải được lưu trữ trong cache (ví dụ: redis hoặc in-memory dictionary). Khi mapping quyền của Role thay đổi, cache này phải được làm mới (invalidated).
  - Quyền override cá nhân (`user_permissions`) của User **không được cache** mà phải truy vấn trực tiếp từ DB cho mỗi request.
- **AC-04 (Fail-Closed Enforcement):**
  - Dependency `require_perm(permission_code: str)` kiểm tra xem user hiện tại có sở hữu permission_code đó trong tập quyền hiệu lực hay không.
  - Nếu user không có quyền, trả lỗi `ERR-AUTH-FORBIDDEN` (HTTP 403).

## 5. Error Codes & Validation
- **`ERR-AUTH-MISSING_TOKEN` (401):** Thiếu Bearer token trong header.
- **`ERR-AUTH-INVALID_TOKEN` (401):** Token không hợp lệ hoặc hết hạn.
- **`ERR-AUTH-FORBIDDEN` (403):** Không có quyền truy cập endpoint này.
