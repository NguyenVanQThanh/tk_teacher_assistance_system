# Task — F-AUTH-01-TASK-002: User Auth Repository

> Path: `docs/tasks/f_auth_01/f_auth_01-task_002.md`
> Slice: `S02` · Type: `REPO` · Size: `S` · SP: `1`
> Depends on: `F-AUTH-01-TASK-001`
> Status: `ready to test`
> Created At: `2026-07-11`
> Updated At: `2026-07-16`
> Updated By: `Tam Khang`

---

## 1. Objective & Description
Xây dựng lớp Repository cho module Authentication (`UserRepository`) để truy vấn dữ liệu từ bảng `users` phục vụ cho luồng đăng nhập bằng email hoặc số điện thoại.

## 2. Input Context & Specs
- File đặc tả: [f_auth_01_spec.md](../../v_1/specs/f_auth_01_spec.md)
  - Section B.2.2: Critical data flow (login)
  - Section C.7: Business Rules (BR-01)
- Model `User` kế thừa từ `models/models.py` (hoặc `app/modules/foundation/models.py`).

## 3. Outputs
- **File tạo mới:** [repository.py](../../../app/modules/auth/repository.py)
- **Các hàm cần triển khai:**
  - `UserRepository.get_by_email(db: Session, email: str) -> Optional[User]`
  - `UserRepository.get_by_phone(db: Session, phone: str) -> Optional[User]`

## 4. Requirements & Acceptance Criteria
- **AC-01 (DB Queries):** Phải viết câu lệnh truy vấn chính xác để tìm kiếm User theo `email` hoặc `phone` một cách tối ưu.
- **AC-02 (Constraints):** Tuyệt đối không được sửa đổi schema của bảng `users` hay tự ý ghi đè các cấu trúc dữ liệu nền của module foundation.

## 5. Error Codes & Validation
- Không ném lỗi trực tiếp ở tầng Repository nếu không tìm thấy User (trả về `None`), tầng Service sẽ chịu trách nhiệm xử lý logic kiểm tra và ném lỗi phù hợp.
