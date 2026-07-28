> Path: `docs/tasks/f_exe_02/f_exe_02_assignments.md`
> Slice: `SL-EXE-02` · Type: `feature` · Size: `medium` · SP: `3`
> Depends on: `F-EXE-01`
> Status: `draft`
> Created At: `2026-07-28`
> Updated At: `2026-07-28`

# Task — `F-EXE-02` Class Assignments (Giao bài tập cho lớp)

**Author:** AI Agent
**Updated By:** AI Agent

## Mô tả Task
Triển khai module giao bài (`ClassAssignment`) bao gồm:
1. Alembic migration: tạo bảng `class_assignments` nếu chưa tồn tại (theo `base_sql_erd.sql` §4.1).
2. SQLAlchemy model: `ClassAssignment` trong `models/models.py`.
3. Pydantic validation: `AssignmentCreate` (`due_at` phải ở tương lai).
4. Repository layer: `AssignmentRepository` — filter theo `class_id`, kiểm tra tồn tại attempt liên kết (cho hard-delete guard).
5. Service layer: `AssignmentService` — validate `teacher_subjects` khớp (`class_id`, `exercise.subject_id`) trước khi giao (AS-02 sprint 2), chặn trùng giao bài, chặn xóa khi đã có attempt.
6. API Routers: `app/modules/exercise/routers/assignments.py` — tái sử dụng `check_class_access` từ `app/modules/academic/scoping.py` cho RBAC Data Scoping.
7. Seed permission mới `EXE_ASSIGNMENT_MANAGE`, `EXE_ASSIGNMENT_VIEW` — map Teacher/Admin (manage), Teacher/Student/Admin (view).
8. Unit & Integration tests pass 100%.

## Technical Workflow

```
Bước 1: Alembic Migration
  └── alembic revision --autogenerate -m "create class_assignments table"

Bước 2: SQLAlchemy Model
  └── models/models.py: ClassAssignment

Bước 3: Pydantic Schemas
  └── app/modules/exercise/schemas.py: AssignmentCreate, AssignmentOut

Bước 4: Repository Layer
  └── app/modules/exercise/repository.py: AssignmentRepository (filter by class_id, has_attempts check)

Bước 5: Service Layer & Scoping
  └── app/modules/exercise/services/assignment_service.py: create (teacher_subjects match check), list (reuse get_accessible_class_ids), delete (attempts guard)

Bước 6: API Router & Dependency Injection
  └── app/modules/exercise/routers/assignments.py: require_perm & get_current_user, import scoping từ academic module

Bước 7: Seed Permissions
  └── app/scripts/seed.py: thêm EXE_ASSIGNMENT_MANAGE/VIEW

Bước 8: Automated Testing Verification
  └── pytest tests/exercise/integration/test_assignments.py & test_assignment_service.py -> Pass 100%
```

## Kết quả kiểm thử
- (chưa thực thi — task ở trạng thái `draft`, cập nhật khi triển khai xong)
