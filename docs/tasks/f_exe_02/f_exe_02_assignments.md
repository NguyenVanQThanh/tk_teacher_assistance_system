> Path: `docs/tasks/f_exe_02/f_exe_02_assignments.md`
> Slice: `SL-EXE-02` · Type: `feature` · Size: `medium` · SP: `3`
> Depends on: `F-EXE-01`
> Status: `ready to test`
> Created At: `2026-07-28`
> Updated At: `2026-08-04`

# Task — `F-EXE-02` Class Assignments (Giao bài tập cho lớp)

**Author:** Tam Khang
**Updated By:** Tam Khang

## Mô tả Task
Triển khai module giao bài (`ClassAssignment`) bao gồm:
1. Alembic migration: tạo bảng `class_assignments` với cột `status` (VARCHAR(20) DEFAULT 'ACTIVE') hỗ trợ Soft Delete theo quy chuẩn hệ thống.
2. SQLAlchemy model: `ClassAssignment` trong `models/models.py` (hỗ trợ cột `status` cho soft-delete).
3. Pydantic validation: `AssignmentCreate` (`due_at` phải ở tương lai).
4. Repository layer: `AssignmentRepository` — filter theo `class_id` & `status` (mặc định chỉ lấy `ACTIVE`), hỗ trợ hàm `restore`.
5. Service layer: `AssignmentService` — validate `teacher_subjects` khớp (`class_id`, `exercise.subject_id`) trước khi giao (AS-02 sprint 2), chặn trùng giao bài, xóa mềm (soft-delete chuyển `status` sang `DELETED`) và khôi phục (restore).
6. API Routers: `app/modules/exercise/routers/assignments.py` — tái sử dụng `check_class_access` từ `app/modules/academic/scoping.py` cho RBAC Data Scoping.
7. Seed permission mới `EXE_ASSIGNMENT_MANAGE`, `EXE_ASSIGNMENT_VIEW` — map Teacher/Admin (manage), Teacher/Student/Admin (view).
8. Unit & Integration tests pass 100%.

## Technical Workflow

```
Bước 1: Alembic Migration
  └── alembic revision --autogenerate -m "create class_assignments table with soft delete status"

Bước 2: SQLAlchemy Model
  └── models/models.py: ClassAssignment (với status VARCHAR(20) DEFAULT 'ACTIVE')

Bước 3: Pydantic Schemas
  └── app/modules/exercise/schemas.py: AssignmentCreate, AssignmentOut

Bước 4: Repository Layer
  └── app/modules/exercise/repository.py: AssignmentRepository (filter by class_id & status, soft delete & restore support)

Bước 5: Service Layer & Scoping
  └── app/modules/exercise/services/assignment_service.py: create (teacher_subjects match check), list (reuse get_accessible_class_ids), delete (soft-delete sang DELETED) & restore

Bước 6: API Router & Dependency Injection
  └── app/modules/exercise/routers/assignments.py: require_perm & get_current_user, import scoping từ academic module


Bước 7: Seed Permissions
  └── app/scripts/seed.py: thêm EXE_ASSIGNMENT_MANAGE/VIEW

Bước 8: Automated Testing Verification
  └── pytest tests/exercise/integration/test_assignments.py & test_assignment_service.py -> Pass 100%
```

## Kết quả kiểm thử
- `pytest tests/exercise/test_assignments.py -v` -> PASSED 100% (2/2 integration test scenarios passed).
- `pytest tests/exercise/ -v` -> PASSED 100% (4/4 tests passed).
- `pytest tests/ -v` -> PASSED 100% (119/119 tests passed across all system modules).

## Các đầu việc bổ sung & Refactor (Pending Items)
- [ ] **Refactor Dependency Injection**: Cập nhật router `app/modules/exercise/routers/assignments.py` sử dụng provider `get_assignment_service` với `Depends(get_assignment_service)` thay cho khởi tạo thủ công `AssignmentService(db)` bên trong route handler.
- [ ] **Chuẩn hóa Ngôn ngữ**: Rà soát các docstrings/comments trong `assignments.py` và `assignment_service.py` đảm bảo tuân thủ 100% Standard English.
- [ ] **Nghiệm thu kiểm thử người dùng (UAT)**: Tiến hành kiểm thử các API giao bài, xem danh sách bài giao và hủy giao bài trên Postman/Swagger UI.
- [ ] **Hoàn tất Task & Lưu vết Memory**: Đổi `Status` sang `done` và khởi tạo file ghi nhớ tại `.claude/memory/feature/f_exe_02_assignments_complete.md` sau khi User nghiệm thu thành công.


