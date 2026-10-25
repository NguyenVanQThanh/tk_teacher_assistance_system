> Path: `docs/tasks/f_acad_01/f_acad_01_subjects.md`
> Slice: `SL-ACAD-01` · Type: `feature` · Size: `medium` · SP: `3`
> Depends on: `F-AUTH-01`
> Status: `done`
> Created At: `2026-07-26`
> Updated At: `2026-07-26`

# Task — `F-ACAD-01` Subjects (CRUD & Restore môn học)

**Author:** Tam Khang  
**Updated By:** Tam Khang  

## Mô tả Task
Triển khai module quản lý danh mục Môn học (`Subject`) bao gồm:
1. Pydantic validation: tự động xóa khoảng trắng (`strip()`), không cho phép tên rỗng, validation status Enum (`AcademicStatusEnum`).
2. Repository layer: Optional filtering không hardcode `status = 'ACTIVE'`, hỗ trợ `exclude_status='DELETED'`, và bổ sung hàm `restore`.
3. Service layer: Kiểm tra trùng tên môn học, tạo, sửa, xóa mềm (`DELETED`), khôi phục (`RESTORE`).
4. API Routers: Khởi tạo các endpoint `POST/GET/PUT/DELETE/RESTORE /api/v1/subjects` bảo vệ bởi permission `ACAD_SUBJECT_MANAGE` và `ACAD_SUBJECT_VIEW`.
5. Unit & Integration tests pass 100%.

## Technical Workflow (Quy trình thực thi kỹ thuật)

```
Bước 1: Pydantic Validation & Schemas
  └── Cập nhật app/modules/academic/schemas.py: SubjectCreate, SubjectUpdate, AcademicStatusEnum (strip(), non-empty check)

Bước 2: Repository Layer Refactoring
  └── Cập nhật app/modules/academic/repository.py: SubjectRepository.filter_subjects (Optional Filter), SubjectRepository.restore

Bước 3: Service Layer Implementation
  └── Cập nhật app/modules/academic/services/subject_service.py: SubjectService (create, list_subjects, update, delete, restore_subject)

Bước 4: API Router & Dependency Injection
  └── Cập nhật app/modules/academic/routers/subjects.py: endpoints (POST, GET, PUT, DELETE, POST /restore) với require_perm & get_current_user

Bước 5: Automated Testing Verification
  └── Thực thi pytest tests/academic/integration/test_subjects.py & test_subject_service.py -> Pass 100%
```

## Kết quả kiểm thử
- `pytest tests/academic/integration/test_subjects.py` - Pass 100%.
- `pytest tests/academic/unit/test_subject_service.py` - Pass 100%.
