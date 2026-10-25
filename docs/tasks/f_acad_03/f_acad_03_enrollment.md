> Path: `docs/tasks/f_acad_03/f_acad_03_enrollment.md`
> Slice: `SL-ACAD-03` · Type: `feature` · Size: `medium` · SP: `3`
> Depends on: `F-ACAD-02`
> Status: `done`
> Created At: `2026-07-26`
> Updated At: `2026-07-26`

# Task — `F-ACAD-03` Enrollment (Ghi danh & Restore học sinh vào lớp)

**Author:** Tam Khang  
**Updated By:** Tam Khang  

## Mô tả Task
Triển khai module Ghi danh Học sinh (`StudentClass`) bao gồm:
1. Pydantic validation: tự động xóa khoảng trắng (`student_code`), status Enum (`AcademicStatusEnum`).
2. Repository layer: Optional filtering không hardcode `status = 'ACTIVE'`, hỗ trợ `exclude_status='DELETED'`, và bổ sung hàm `restore`.
3. Service layer: Validate học sinh có vai trò `Student` và trạng thái `Active`, kiểm tra trùng ghi danh trong lớp, hủy ghi danh (xóa mềm `DELETED`), và khôi phục (`RESTORE`).
4. RBAC Data Scoping: Kiểm tra người dùng có quyền truy cập lớp học trước khi hiển thị danh sách học sinh.
5. API Routers: Khởi tạo các endpoint `POST/GET/DELETE/RESTORE /api/v1/classes/{class_id}/students` bảo vệ bởi `ACAD_ENROLLMENT_MANAGE` và `ACAD_ENROLLMENT_VIEW`.
6. Unit & Integration tests pass 100%.

## Technical Workflow (Quy trình thực thi kỹ thuật)

```
Bước 1: Pydantic Validation & Schemas
  └── Cập nhật app/modules/academic/schemas.py: EnrollmentCreate (strip student_code, AcademicStatusEnum)

Bước 2: Repository Layer Refactoring
  └── Cập nhật app/modules/academic/repository.py: EnrollmentRepository.filter_enrollments (Optional Filter), EnrollmentRepository.restore

Bước 3: Service Layer Implementation & Data Scoping
  └── Cập nhật app/modules/academic/services/enrollment_service.py: enroll_student, list_students_in_class (check_class_access), unenroll_student, restore_enrollment

Bước 4: API Router & Dependency Injection
  └── Cập nhật app/modules/academic/routers/enrollments.py: endpoints (POST, GET, DELETE, POST /restore) với require_perm & get_current_user

Bước 5: Automated Testing Verification
  └── Thực thi pytest tests/academic/integration/test_enrollments.py & test_enrollment_service.py -> Pass 100%
```

## Kết quả kiểm thử
- `pytest tests/academic/integration/test_enrollments.py` - Pass 100%.
- `pytest tests/academic/unit/test_enrollment_service.py` - Pass 100%.
