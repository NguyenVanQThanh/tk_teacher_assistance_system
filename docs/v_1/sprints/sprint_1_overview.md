# Sprint 1 — Academic Org

> Path: `docs/v_1/sprints/sprint_1_overview.md` · Module(s): `academic`

## Mục tiêu Sprint

Xây tầng nghiệp vụ **cơ cấu tổ chức** (môn học, lớp học, ghi danh học sinh, phân công giáo viên bộ môn) trên schema đã có sẵn từ Sprint 0 (`subjects`, `classes`, `student_class`, `teacher_subjects`). Đây là điều kiện tiên quyết cho 4 module nghiệp vụ chính của SRS (Tracking, AI Generation, Teacher Dashboard, Student Dashboard) — đặc biệt là NFR RBAC "Giáo viên chỉ quản lý học sinh thuộc lớp mình phụ trách" (SRS §3).

Kết thúc Sprint 1, hệ thống phải: cho phép Admin CRUD môn học và lớp học, ghi danh/xóa học sinh khỏi lớp, phân công/hủy phân công giáo viên dạy môn ở lớp — tất cả đều bảo vệ bằng RBAC permission-based kế thừa từ `F-AUTH-01`.

| Field | Giá trị |
|---|---|
| Sprint | `SPRINT-01` |
| Khoảng | (điền khi planning) |
| Stack | kế thừa Sprint 0: FastAPI · SQLAlchemy 2.0 · PostgreSQL · RBAC permission-based |
| SRS coverage | Tiền đề tổ chức cho 4 module nghiệp vụ; NFR RBAC §3 (GV chỉ quản lý lớp mình) |
| DB tables | `subjects`, `classes`, `student_class`, `teacher_subjects` (đã tồn tại từ baseline migration Sprint 0 — **không có migration mới**) |

## Quyết định scope (assumptions)

| # | Quyết định | Lý do |
|---|---|---|
| AS-01 | Chỉ **Admin** có quyền ghi (tạo/sửa/xóa) cơ cấu tổ chức ở Sprint 1. Teacher/Student chỉ có thể được cấp quyền view qua override sau nếu cần. | Giữ scope gọn; SRS không mô tả Teacher tự tạo lớp/môn. |
| AS-02 | `homeroom_teacher_id` khi gán phải là user có role `Teacher` và status `Active`. | Tránh gán nhầm GVCN là học sinh/tài khoản khóa. |
| AS-03 | Ghi danh học sinh yêu cầu user đích có role `Student` và status `Active`; phân công giáo viên yêu cầu user đích có role `Teacher` và status `Active`. | Đảm bảo toàn vẹn nghiệp vụ, tránh dữ liệu rác. |
| AS-04 | Không tạo migration mới — toàn bộ bảng đã có trong baseline `d00f10e379e6_init_sprint_0_tables.py`. | Tránh trùng lặp, giữ baseline immutable theo D.5 Forbidden Files của F-FND-01. |
| AS-05 | Không tạo file catalog rời (`error_codes.md`/`permissions.md`/`events.md`) vì Sprint 0 cũng chưa khởi tạo các file này — danh mục ID mới liệt kê trực tiếp trong spec PART E.1. | Nhất quán với hiện trạng repo; tránh tạo hạ tầng tài liệu ngoài phạm vi đã thống nhất. |

## Features trong Sprint

Feature `Academic Org` được breakdown thành 4 spec nhỏ theo từng nhóm chức năng, thực thi tuần tự vì có phụ thuộc dữ liệu (Class cần validate qua Subject/Teacher, Enrollment/Teacher Assignment cần Class đã tồn tại):

| Feature ID | Tên | Module | Spec | Phụ thuộc |
|---|---|---|---|---|
| `F-ACAD-01` | Subjects (CRUD môn học) | `academic` | [f_acad_01_subjects_spec.md](../specs/f_acad_01_subjects_spec.md) | `F-FND-01`, `F-AUTH-01` |
| `F-ACAD-02` | Classes (CRUD lớp học) | `academic` | [f_acad_02_classes_spec.md](../specs/f_acad_02_classes_spec.md) | `F-ACAD-01` |
| `F-ACAD-03` | Enrollment (ghi danh học sinh vào lớp) | `academic` | [f_acad_03_enrollment_spec.md](../specs/f_acad_03_enrollment_spec.md) | `F-ACAD-02` |
| `F-ACAD-04` | Teacher Assignment (phân công GV bộ môn) | `academic` | [f_acad_04_teacher_assignment_spec.md](../specs/f_acad_04_teacher_assignment_spec.md) | `F-ACAD-02` |

## Thứ tự thực thi

```
F-AUTH-01 (đã done — RBAC, current-user dependency, JWT)
   └── F-ACAD-01 Subjects (schemas → repository → service → API → seed permission → test)
        └── F-ACAD-02 Classes (phụ thuộc Subjects cho validate FK gián tiếp qua teacher_subjects)
             ├── F-ACAD-03 Enrollment (phụ thuộc Classes + users role Student)
             └── F-ACAD-04 Teacher Assignment (phụ thuộc Classes + Subjects + users role Teacher)
```

Không feature con nào được start trước khi `F-AUTH-01` đạt gate G6.5 `approved` (đã approved từ Sprint 0), vì dùng lại: `get_current_user`, `require_perm`, error response pattern, `models.models` (Subject/Class/StudentClass/TeacherSubject đã định nghĩa sẵn). `F-ACAD-03`/`F-ACAD-04` không start trước khi `F-ACAD-02` đạt G6.5 `approved`.

## Definition of Done — Sprint 1

| ✓ | Tiêu chí |
|---|---|
| ☐ | `POST/GET/PUT/DELETE /api/v1/subjects` hoạt động, validate trùng tên → `ERR-ACAD-SUBJECT_DUPLICATE_NAME` |
| ☐ | `POST/GET/PUT/DELETE /api/v1/classes` hoạt động, validate `homeroom_teacher_id` phải là Teacher Active → `ERR-ACAD-INVALID_HOMEROOM_TEACHER` |
| ☐ | `POST/GET/DELETE /api/v1/classes/{class_id}/students` ghi danh/hủy ghi danh học sinh, validate role Student + trùng ghi danh → `ERR-ACAD-ALREADY_ENROLLED` |
| ☐ | `POST/GET/DELETE /api/v1/classes/{class_id}/teacher-subjects` phân công/hủy phân công GV, validate role Teacher + trùng phân công → `ERR-ACAD-ASSIGNMENT_EXISTS` |
| ☐ | Mọi endpoint ghi/sửa/xóa bảo vệ bằng `require_perm("ACAD_*_MANAGE")`; endpoint xem bảo vệ bằng `require_perm("ACAD_*_VIEW")` |
| ☐ | Seed 8 permission `ACAD_*` mới, map cho role Admin (idempotent) |
| ☐ | `pytest tests/academic` pass; `pytest tests` (toàn bộ, gồm Sprint 0) vẫn pass |
| ☐ | Spec `F-ACAD-01`, `F-ACAD-02`, `F-ACAD-03`, `F-ACAD-04` sign-off PART A→D `approved` |

## Catalogs khởi tạo trong Sprint này

- Permission mới `ACAD_SUBJECT_MANAGE/VIEW` ([f_acad_01_subjects_spec.md](../specs/f_acad_01_subjects_spec.md) §E.1), `ACAD_CLASS_MANAGE/VIEW` ([f_acad_02_classes_spec.md](../specs/f_acad_02_classes_spec.md) §E.1), `ACAD_ENROLLMENT_MANAGE/VIEW` ([f_acad_03_enrollment_spec.md](../specs/f_acad_03_enrollment_spec.md) §E.1), `ACAD_TEACHER_ASSIGN_MANAGE/VIEW` ([f_acad_04_teacher_assignment_spec.md](../specs/f_acad_04_teacher_assignment_spec.md) §E.1) — chưa có file `catalogs/permissions.md` riêng, kế thừa hiện trạng Sprint 0.
- Error code mới `ERR-ACAD-*` — liệt kê rải rác ở §E.1 của từng spec tương ứng ở trên.
- Event mới `EVT-ACAD-*` — liệt kê rải rác ở §E.1 của từng spec tương ứng ở trên.
