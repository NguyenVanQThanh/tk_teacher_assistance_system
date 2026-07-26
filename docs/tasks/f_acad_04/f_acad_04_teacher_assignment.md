> Path: `docs/tasks/f_acad_04/f_acad_04_teacher_assignment.md`
> Slice: `SL-ACAD-04` · Type: `feature` · Size: `medium` · SP: `3`
> Depends on: `F-ACAD-02`
> Status: `done`
> Created At: `2026-07-26`
> Updated At: `2026-07-26`

# Task — `F-ACAD-04` Teacher Assignment (Phân công & Restore GV bộ môn)

**Author:** Tam Khang  
**Updated By:** Tam Khang  

## Mô tả Task
Triển khai module Phân công Giáo viên Bộ môn (`TeacherSubject`) bao gồm:
1. Pydantic validation: status Enum (`AcademicStatusEnum`).
2. Repository layer: Optional filtering không hardcode `status = 'ACTIVE'`, hỗ trợ `exclude_status='DELETED'`, và bổ sung hàm `restore`.
3. Service layer: Validate giáo viên có vai trò `Teacher` và trạng thái `Active`, môn học và lớp học tồn tại, kiểm tra trùng phân công, hủy phân công (xóa mềm `DELETED`), và khôi phục (`RESTORE`).
4. RBAC Data Scoping: Kiểm tra người dùng có quyền truy cập lớp học trước khi hiển thị phân công giáo viên.
5. API Routers: Khởi tạo các endpoint `POST/GET/DELETE/RESTORE /api/v1/classes/{class_id}/teacher-subjects` bảo vệ bởi `ACAD_TEACHER_ASSIGN_MANAGE` và `ACAD_TEACHER_ASSIGN_VIEW`.
6. Unit & Integration tests pass 100%.

## Technical Workflow (Quy trình thực thi kỹ thuật)

```
Bước 1: Pydantic Validation & Schemas
  └── Cập nhật app/modules/academic/schemas.py: TeacherAssignmentCreate (AcademicStatusEnum)

Bước 2: Repository Layer Refactoring
  └── Cập nhật app/modules/academic/repository.py: TeacherAssignmentRepository.filter_teacher_assignments (Optional Filter), TeacherAssignmentRepository.restore

Bước 3: Service Layer Implementation & Data Scoping
  └── Cập nhật app/modules/academic/services/teacher_assignment_service.py: assign_teacher, list_assignments_in_class (check_class_access), unassign_teacher, restore_assignment

Bước 4: API Router & Dependency Injection
  └── Cập nhật app/modules/academic/routers/teacher_assignments.py: endpoints (POST, GET, DELETE, POST /restore) với require_perm & get_current_user

Bước 5: Automated Testing Verification
  └── Thực thi pytest tests/academic/integration/test_teacher_assignments.py & test_teacher_assignment_service.py -> Pass 100%
```

## Kết quả kiểm thử
- `pytest tests/academic/integration/test_teacher_assignments.py` - Pass 100%.
- `pytest tests/academic/unit/test_teacher_assignment_service.py` - Pass 100%.
