# Sprint 1 — Academic Org

> Path: `docs/v_1/sprints/sprint_1_overview.md` · Module(s): `academic`
> Created At: `2026-07-18`
> Created By: `Tam Khang`
> Updated At: `2026-07-26`
> Updated By: `Tam Khang`

## Mục tiêu Sprint

Xây tầng nghiệp vụ **cơ cấu tổ chức** (môn học, lớp học, ghi danh học sinh, phân công giáo viên bộ môn) trên schema đã nâng cấp từ Sprint 0 (`subjects`, `classes`, `student_class`, `teacher_subjects`), bao gồm quản lý trạng thái (`ACTIVE`, `INACTIVE`, `DRAFT`, `DELETED`), khôi phục dữ liệu (`Restore Data`), validation toàn diện, và phân quyền phạm vi dữ liệu (RBAC Data Scoping) theo 3 vai trò Admin, Teacher, Student.

Kết thúc Sprint 1, hệ thống cho phép Admin CRUD & Khôi phục môn học, lớp học, ghi danh/xóa học sinh khỏi lớp, phân công/hủy phân công giáo viên; Teacher và Student chỉ truy cập được dữ liệu thuộc phạm vi lớp học của mình.

| Field | Giá trị |
|---|---|
| Sprint | `SPRINT-01` |
| Status | `done` |
| Stack | FastAPI · SQLAlchemy 2.0 · PostgreSQL · Alembic · RBAC permission-based |
| SRS coverage | Tiền đề tổ chức cho 4 module nghiệp vụ; NFR RBAC §3 (GV chỉ quản lý lớp mình) |
| DB tables | `subjects`, `classes`, `student_class`, `teacher_subjects` |

## Quyết định scope (assumptions)

| # | Quyết định | Lý do |
|---|---|---|
| AS-01 | Admin có quyền ghi (tạo/sửa/xóa/khôi phục) cơ cấu tổ chức và xem toàn bộ dữ liệu (kể cả bản ghi xóa mềm `DELETED`). Teacher/Student chỉ truy cập dữ liệu thuộc phạm vi mình phụ trách/theo học. | Đảm bảo tính bảo mật và phân quyền dữ liệu (RBAC Data Scoping). |
| AS-02 | `homeroom_teacher_id` khi gán phải là user có role `Teacher` và status `Active`. | Tránh gán nhầm GVCN là học sinh/tài khoản khóa. |
| AS-03 | Ghi danh học sinh yêu cầu user đích có role `Student` và status `Active`; phân công giáo viên yêu cầu user đích có role `Teacher` và status `Active`. | Đảm bảo toàn vẹn nghiệp vụ, tránh dữ liệu rác. |
| AS-04 | Tạo Alembic migration mới `2ecce316b47f_add_status_replace_is_deleted.py` để bổ sung cột `status` (`ACTIVE`, `INACTIVE`, `DRAFT`, `DELETED`) và loại bỏ hoàn toàn `is_deleted`. | Tuân thủ quy tắc quản lý Alembic migration theo Section 7 coding rules. |
| AS-05 | Áp dụng Pydantic Field Validation toàn diện cho tất cả DTO Create/Update (tự động cắt khoảng trắng `strip()`, regex `school_year` dạng `YYYY-YYYY`, Enum validation cho `status`). | Ngăn chặn dữ liệu rác và khoảng trắng thừa. |

## Features trong Sprint

| Feature ID | Tên | Module | Spec | Status |
|---|---|---|---|---|
| `F-ACAD-01` | Subjects (CRUD & Restore môn học) | `academic` | [f_acad_01_subjects_spec.md](../specs/f_acad_01_subjects_spec.md) | `done` |
| `F-ACAD-02` | Classes (CRUD & Restore lớp học) | `academic` | [f_acad_02_classes_spec.md](../specs/f_acad_02_classes_spec.md) | `done` |
| `F-ACAD-03` | Enrollment (ghi danh & Restore học sinh) | `academic` | [f_acad_03_enrollment_spec.md](../specs/f_acad_03_enrollment_spec.md) | `done` |
| `F-ACAD-04` | Teacher Assignment (phân công & Restore GV) | `academic` | [f_acad_04_teacher_assignment_spec.md](../specs/f_acad_04_teacher_assignment_spec.md) | `done` |

## Thứ tự thực thi

```
F-AUTH-01 (RBAC, current-user dependency, JWT)
   └── F-ACAD-01 Subjects (schemas validation → repository optional filter → service → API restore → test)
        └── F-ACAD-02 Classes (schemas validation → repository optional filter → service scoping → API restore → test)
             ├── F-ACAD-03 Enrollment (schemas validation → service scoping → API restore → test)
             └── F-ACAD-04 Teacher Assignment (schemas validation → service scoping → API restore → test)
```

## Definition of Done — Sprint 1

| ✓ | Tiêu chí | Status |
|---|---|---|
| [x] | `POST/GET/PUT/DELETE/RESTORE /api/v1/subjects` hoạt động, validate trùng tên -> `ERR-ACAD-SUBJECT_DUPLICATE_NAME`, hỗ trợ status & restore | `done` |
| [x] | `POST/GET/PUT/DELETE/RESTORE /api/v1/classes` hoạt động, validate `homeroom_teacher_id` Teacher Active -> `ERR-ACAD-INVALID_HOMEROOM_TEACHER`, regex `school_year` `YYYY-YYYY`, RBAC Data Scoping & restore | `done` |
| [x] | `POST/GET/DELETE/RESTORE /api/v1/classes/{class_id}/students` ghi danh/hủy ghi danh/khôi phục học sinh, validate role Student + trùng ghi danh -> `ERR-ACAD-ALREADY_ENROLLED`, RBAC Data Scoping & restore | `done` |
| [x] | `POST/GET/DELETE/RESTORE /api/v1/classes/{class_id}/teacher-subjects` phân công/hủy phân công/khôi phục GV, validate role Teacher + trùng phân công -> `ERR-ACAD-ASSIGNMENT_EXISTS`, RBAC Data Scoping & restore | `done` |
| [x] | Mọi endpoint ghi/sửa/xóa/khôi phục bảo vệ bằng `require_perm("ACAD_*_MANAGE")`; endpoint xem bảo vệ bằng `require_perm("ACAD_*_VIEW")` & `get_current_user` | `done` |
| [x] | Seed 8 permission `ACAD_*` mới, map cho role Admin | `done` |
| [x] | `pytest tests` (115/115 unit & integration tests) pass 100% | `done` |
| [x] | Specs `F-ACAD-01`, `F-ACAD-02`, `F-ACAD-03`, `F-ACAD-04` cập nhật theo thực tế triển khai | `done` |

## Catalogs khởi tạo trong Sprint này

- Permission mới `ACAD_SUBJECT_MANAGE/VIEW`, `ACAD_CLASS_MANAGE/VIEW`, `ACAD_ENROLLMENT_MANAGE/VIEW`, `ACAD_TEACHER_ASSIGN_MANAGE/VIEW`.
- Error code mới `ERR-ACAD-*` và `ERR-ACAD-CLASS_ACCESS_DENIED`.
- Event mới `EVT-ACAD-*` bao gồm `EVT-ACAD-*-RESTORED`.
