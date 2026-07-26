> Path: `docs/tasks/f_acad_02/f_acad_02_classes.md`
> Slice: `SL-ACAD-02` · Type: `feature` · Size: `medium` · SP: `5`
> Depends on: `F-ACAD-01`
> Status: `done`
> Created At: `2026-07-26`
> Updated At: `2026-07-26`

# Task — `F-ACAD-02` Classes (CRUD & Restore lớp học)

**Author:** Tam Khang  
**Updated By:** Tam Khang  

## Mô tả Task
Triển khai module quản lý Lớp học (`Class`) bao gồm:
1. Pydantic validation: tự động xóa khoảng trắng (`strip()`), regex kiểm tra năm học `school_year` dạng `YYYY-YYYY` (ví dụ `2025-2026`), validation status Enum (`AcademicStatusEnum`).
2. Repository layer: Optional filtering không hardcode `status = 'ACTIVE'`, hỗ trợ `exclude_status='DELETED'`, và bổ sung hàm `restore`.
3. RBAC Data Scoping (`scoping.py`):
   - Admin: Xem toàn bộ danh sách lớp và bản ghi bị xóa mềm (`DELETED`).
   - Teacher: Chỉ xem danh sách lớp làm Chủ nhiệm hoặc Phân công dạy.
   - Student: Chỉ xem danh sách lớp Đang ghi danh.
4. Service layer: Kiểm tra trùng tên lớp, validate Giáo viên chủ nhiệm (phải có vai trò `Teacher` và trạng thái `Active`), khôi phục (`RESTORE`).
5. API Routers: Khởi tạo các endpoint `POST/GET/PUT/DELETE/RESTORE /api/v1/classes` bảo vệ bởi `ACAD_CLASS_MANAGE` và `ACAD_CLASS_VIEW` & `get_current_user`.
6. Unit & Integration tests pass 100%.

## Technical Workflow (Quy trình thực thi kỹ thuật)

```
Bước 1: Pydantic Validation & Schemas
  └── Cập nhật app/modules/academic/schemas.py: ClassCreate, ClassUpdate (regex YYYY-YYYY, strip(), AcademicStatusEnum)

Bước 2: Repository Layer Refactoring
  └── Cập nhật app/modules/academic/repository.py: ClassRepository.filter_classes (Optional Filter), ClassRepository.restore

Bước 3: RBAC Data Scoping Layer
  └── Tạo app/modules/academic/scoping.py: get_user_role_name, get_accessible_class_ids, check_class_access

Bước 4: Service Layer Implementation
  └── Cập nhật app/modules/academic/services/class_service.py: validate_homeroom_teacher, list_classes (scoping), get_class, restore_class

Bước 5: API Router & Dependency Injection
  └── Cập nhật app/modules/academic/routers/classes.py: endpoints (POST, GET, PUT, DELETE, POST /restore) với current_user scoping

Bước 6: Automated Testing Verification
  └── Thực thi pytest tests/academic/integration/test_classes.py & test_class_service.py -> Pass 100%
```

## Kết quả kiểm thử
- `pytest tests/academic/integration/test_classes.py` - Pass 100%.
- `pytest tests/academic/unit/test_class_service.py` - Pass 100%.
