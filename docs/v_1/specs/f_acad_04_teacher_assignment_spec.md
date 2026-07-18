# Feature Spec — `F-ACAD-04` Teacher Assignment (Phân công giáo viên bộ môn)

> Path: `docs/v_1/specs/f_acad_04_teacher_assignment_spec.md` · Sprint: [sprint_1_overview.md](../sprints/sprint_1_overview.md)

---

## Document Header

| Field | Giá trị |
|---|---|
| Feature ID | `F-ACAD-04` |
| Feature name | Teacher Assignment — Phân công giáo viên bộ môn |
| Module(s) | `academic` |
| Sprint(s) allocated | `SPRINT-01` |
| Lane | `standard` |
| Spec version | `v1.0` |
| Last updated | `2026-07-18` |
| Source binding | SOP §12 · `docs/base_sql_erd.sql` v1.0 (bảng `teacher_subjects`) · [f_acad_02_classes_spec.md](f_acad_02_classes_spec.md) (Classes phải tồn tại trước) · [f_acad_01_subjects_spec.md](f_acad_01_subjects_spec.md) (Subjects phải tồn tại trước) · `f_auth_01_spec.md` (RBAC, current-user) · `.claude/rules/coding_rules.md` |

### Gate status

| Gate | Bao trùm | Owner | Approver | Status | Date |
|---|---|---|---|---|---|
| G3 Business | PART A | BA/PM | Lead | `approved` | 2026-07-18 |
| G4 Architecture | PART B | Architect | CTO | `approved` | 2026-07-18 |
| G6 Design | PART C | Lead | Lead | `approved` | 2026-07-18 |
| G6.5 Coding | PART D | BE Lead | BE Lead | `approved` | 2026-07-18 |
| G7+ Tracking | PART E | PM | PM | `approved` | 2026-07-18 |

### Table of contents

- [PART A — Business](#part-a--business)
- [PART B — Architecture](#part-b--architecture)
- [PART C — Design](#part-c--design)
- [PART D — Coding context](#part-d--coding-context)
- [PART E — Tracking & Sign-off](#part-e--tracking--sign-off)

---

# PART A — Business

> **Owner:** BA/PM · **Gate:** G3

## A.1 Feature Summary

Cho phép **Admin** phân công giáo viên dạy một môn học cụ thể ở một lớp cụ thể (bảng `teacher_subjects`, composite key `teacher_id` + `class_id` + `subject_id`), và hủy phân công. Đây là điều kiện tiên quyết cho NFR RBAC "GV chỉ quản lý HS thuộc lớp mình phụ trách" (SRS §3) và cho S2 (giao bài tập — cần biết GV nào được phép giao bài cho lớp/môn nào). Bảng `teacher_subjects` đã tồn tại từ baseline migration Sprint 0 — feature này chỉ xây tầng nghiệp vụ, không migration mới. Phụ thuộc `F-ACAD-02` (Classes) và `F-ACAD-01` (Subjects) đã `approved`.

## A.2 User Stories

| Story ID | As (role) | I want (capability) | So that (value) |
|---|---|---|---|
| US-01 | Admin | phân công một giáo viên dạy một môn ở một lớp | xác định rõ ai dạy môn nào ở lớp nào |
| US-02 | Admin | xem danh sách phân công giáo viên theo lớp | biết lớp có những GV/môn nào đang dạy |
| US-03 | Admin | hủy phân công giáo viên | điều chỉnh khi GV đổi lớp/nghỉ dạy môn đó |

## A.3 REQ Registry

| REQ ID | Mô tả ngắn | Priority | Status | Linked Story |
|---|---|---|---|---|
| REQ-ACAD-012 | Phân công GV dạy môn ở lớp (validate role Teacher + Active, chống trùng) | P0 | `approved` | US-01 |
| REQ-ACAD-013 | Liệt kê phân công GV theo lớp | P0 | `approved` | US-02 |
| REQ-ACAD-014 | Hủy phân công GV | P1 | `approved` | US-03 |

## A.4 Acceptance Criteria (Feature-level)

| AC ID | REQ | Given | When | Then |
|---|---|---|---|---|
| AC-01 | REQ-ACAD-012 | `class_id`, `subject_id` tồn tại, `teacher_id` là user role Teacher + Active, chưa được phân công (teacher_id, class_id, subject_id) này | `POST /api/v1/classes/{class_id}/teacher-subjects` | 201, trả về bản ghi phân công |
| AC-02 | REQ-ACAD-012 | phân công (teacher_id, class_id, subject_id) đã tồn tại | `POST /api/v1/classes/{class_id}/teacher-subjects` | 409 `ERR-ACAD-ASSIGNMENT_EXISTS` |
| AC-03 | REQ-ACAD-012 | `teacher_id` không phải role Teacher hoặc không Active | `POST /api/v1/classes/{class_id}/teacher-subjects` | 400 `ERR-ACAD-INVALID_TEACHER_ROLE` |
| AC-04 | REQ-ACAD-012 | `class_id` không tồn tại | `POST /api/v1/classes/{class_id}/teacher-subjects` | 404 `ERR-ACAD-CLASS_NOT_FOUND` |
| AC-05 | REQ-ACAD-012 | `subject_id` không tồn tại | `POST /api/v1/classes/{class_id}/teacher-subjects` | 404 `ERR-ACAD-SUBJECT_NOT_FOUND` |
| AC-06 | REQ-ACAD-013 | `class_id` tồn tại, có N phân công | `GET /api/v1/classes/{class_id}/teacher-subjects` | 200, danh sách N phân công |
| AC-07 | REQ-ACAD-014 | phân công (teacher_id, subject_id) tồn tại ở lớp | `DELETE /api/v1/classes/{class_id}/teacher-subjects/{teacher_id}/{subject_id}` | 200/204, hủy phân công |
| AC-08 | REQ-ACAD-014 | phân công không tồn tại | `DELETE /api/v1/classes/{class_id}/teacher-subjects/{teacher_id}/{subject_id}` | 404 `ERR-ACAD-ASSIGNMENT_NOT_FOUND` |
| AC-09 | REQ-ACAD-012..014 | user không có permission `ACAD_TEACHER_ASSIGN_MANAGE`/`ACAD_TEACHER_ASSIGN_VIEW` | gọi endpoint tương ứng | 403 `ERR-AUTH-FORBIDDEN` |

## A.5 In / Out of Scope

**In scope:**
- Phân công GV dạy môn ở lớp (`POST`), liệt kê phân công theo lớp (`GET`), hủy phân công (`DELETE`).
- Validate GV phải role `Teacher` và status `Active` (AS-03, `sprint_1_overview.md`).
- Validate `class_id`, `subject_id` tồn tại trước khi phân công.
- Chống phân công trùng (composite key `teacher_id` + `class_id` + `subject_id`).

**Out of scope (defer):**
- Giới hạn số môn/lớp tối đa một GV được dạy — không có trong SRS.
- Lịch dạy (thời khóa biểu) — không có trong SRS Sprint 1.
- Phân công hàng loạt (bulk assign) nhiều GV/môn một lúc.

## A.6 REQ → Task Type Map

| REQ ID | Task type(s) cần | Note |
|---|---|---|
| REQ-ACAD-012/013/014 | SCHEMA → REPO → SERVICE → API → TEST | CRUD trên bảng liên kết, không cần MIG (bảng đã có) |

## A.7 Feature DoD

| ✓ | Tiêu chí Feature Done |
|---|---|
| ☐ | Tất cả AC §A.4 verified qua test |
| ☐ | `pytest tests/academic -k teacher_assignment` pass |
| ☐ | Permission `ACAD_TEACHER_ASSIGN_MANAGE`, `ACAD_TEACHER_ASSIGN_VIEW` seed cho role Admin |
| ☐ | Sign-off §E.4 hoàn tất |

---

# PART B — Architecture

> **Owner:** Architect · **Approver:** CTO · **Gate:** G4

## B.1 Executive Summary (architectural)

Feature quản lý bảng liên kết ba chiều `teacher_subjects` (composite PK `teacher_id` + `class_id` + `subject_id`). Endpoint lồng dưới resource `classes` (`/api/v1/classes/{class_id}/teacher-subjects`), tương tự pattern nested resource của `F-ACAD-03` Enrollment. Cần validate 3 FK: `class_id` (từ `F-ACAD-02`), `subject_id` (từ `F-ACAD-01`), và `teacher_id` (user role Teacher, Active — read-only từ `auth`).

## B.2 High-Level Architecture

### B.2.1 Layered diagram

```
Client → FastAPI Router (teacher_assignments.py) → TeacherAssignmentService → TeacherAssignmentRepository → PostgreSQL (teacher_subjects)
                                                          │                          │
                                                          │                          ├─→ ClassRepository (validate class_id)
                                                          │                          └─→ SubjectRepository (validate subject_id)
                                                          │                          └─→ User model (validate teacher role/status)
                                                          ▼
                                               require_perm("ACAD_TEACHER_ASSIGN_*")
```

### B.2.2 Critical data flow

1. Admin gọi `POST /api/v1/classes/{class_id}/teacher-subjects` kèm Bearer token, `{teacher_id, subject_id}`.
2. `require_perm("ACAD_TEACHER_ASSIGN_MANAGE")` xác thực quyền.
3. `TeacherAssignmentService` validate `class_id` tồn tại (tái dùng `ClassRepository`).
4. Validate `subject_id` tồn tại (tái dùng `SubjectRepository`).
5. Validate `teacher_id` là user tồn tại, role `Teacher`, status `Active`.
6. Validate chưa có bản ghi `teacher_subjects(teacher_id, class_id, subject_id)` trùng.
7. Insert bản ghi, log `EVT-ACAD-TEACHER_ASSIGNED`, trả về `TeacherAssignmentOut`.

## B.3 Domain Ownership Matrix

| Table / Resource | Owner module | Readers | Writers (cross-module) |
|---|---|---|---|
| `teacher_subjects` | `academic` | `academic` (S2 giao bài, S5 Teacher Dashboard dùng để xác định GV phụ trách môn/lớp) | (none) |
| `classes`, `subjects` (read, validate FK) | `academic` | `academic` (nội bộ, không cross-module) | — |
| `users` (read-only, validate teacher) | `auth` | `academic` (chỉ SELECT) | — |

## B.4 Core Invariants (Feature-scope)

| ID | Invariant | Scope | Reference |
|---|---|---|---|
| `INV-ACAD-04-01` | Composite key `(teacher_id, class_id, subject_id)` unique — không phân công trùng | feature | `docs/base_sql_erd.sql` `teacher_subjects` PK |
| `INV-ACAD-04-02` | GV được phân công phải role `Teacher` và status `Active` | feature | AS-03 `sprint_1_overview.md` |
| `INV-ACAD-04-03` | `class_id`, `subject_id` phải tồn tại trước khi phân công | feature | FK constraint `teacher_subjects` |
| `INV-ACAD-04-04` | Không migration mới — bảng `teacher_subjects` bất biến về cấu trúc | feature | baseline `d00f10e379e6_init_sprint_0_tables.py` |

## B.5 Architecture Decisions (ADR — Feature-scope)

| ADR ID | Title | Status | Approver | Date | Summary |
|---|---|---|---|---|---|
| `ADR-ACAD-04-001` | Endpoint nested dưới `/classes/{class_id}/teacher-subjects` thay vì resource độc lập | `approved` | CTO | 2026-07-18 | Nhất quán với pattern nested của `F-ACAD-03` Enrollment |
| `ADR-ACAD-04-002` | Hard delete khi hủy phân công (không giữ lịch sử) | `approved` | CTO | 2026-07-18 | SRS không yêu cầu lịch sử phân công; giữ đơn giản Sprint 1 |

## B.6 API Boundary

| Method | Path | Auth | OpenAPI tag |
|---|---|---|---|
| POST | `/api/v1/classes/{class_id}/teacher-subjects` | Bearer + `ACAD_TEACHER_ASSIGN_MANAGE` | `academic-teacher-assignment` |
| GET | `/api/v1/classes/{class_id}/teacher-subjects` | Bearer + `ACAD_TEACHER_ASSIGN_VIEW` | `academic-teacher-assignment` |
| DELETE | `/api/v1/classes/{class_id}/teacher-subjects/{teacher_id}/{subject_id}` | Bearer + `ACAD_TEACHER_ASSIGN_MANAGE` | `academic-teacher-assignment` |

## B.7 Database Boundary

| Table | Op | Table spec file | Migration |
|---|---|---|---|
| `teacher_subjects` | SELECT/INSERT/DELETE (không đổi schema) | `docs/base_sql_erd.sql` §2.1 | không có (dùng baseline có sẵn) |
| `classes`, `subjects` | SELECT only (validate FK) | `docs/base_sql_erd.sql` §2.1 | không có |
| `users` | SELECT only (validate teacher role/status) | `docs/base_sql_erd.sql` §1.1 | không có |

## B.8 Security & Privacy

| Aspect | Decision |
|---|---|
| AuthN | JWT bearer, tái dùng `get_current_user` |
| AuthZ | `Depends(require_perm("ACAD_TEACHER_ASSIGN_MANAGE"))` / `require_perm("ACAD_TEACHER_ASSIGN_VIEW")` |
| PII handling | Response chỉ trả `teacher_id`, `subject_id`, `class_id` (UUID/reference), không trả thông tin cá nhân GV |
| Audit | Log `EVT-ACAD-TEACHER_ASSIGNED`/`UNASSIGNED` qua `logger.info` |
| Rate limit | Không cần |

## B.9 Observability & Operations

| Aspect | Plan |
|---|---|
| Structured log | `logger.info/warning("Domain Event: EVT-ACAD-...")` |
| Metrics | Chưa cần (Sprint 1 scope nhỏ) |
| Runbook | Không cần riêng |

## B.10 Risk Register

| Risk ID | Severity | Description | Mitigation | Owner |
|---|---|---|---|---|
| RISK-ACAD-04-01 | M | GV bị đổi role/status Inactive sau khi đã phân công — dữ liệu `teacher_subjects` không tự động dọn, ảnh hưởng enforcement RBAC "GV chỉ quản lý lớp mình" ở sprint sau | Chấp nhận rủi ro Sprint 1; validate chỉ tại thời điểm phân công; ghi chú cho S3/S5 khi enforce RBAC cần join thêm điều kiện `users.status = Active` | BE Lead |
| RISK-ACAD-04-02 | L | Xóa `classes`/`subjects` cascade xóa `teacher_subjects` liên quan | Đã document ở spec Classes (RISK-ACAD-02-01) và Subjects (RISK-ACAD-01-01) | BE Lead |

---

# PART C — Design

> **Owner:** Lead · **Gate:** G6

## C.1 User Roles & Permissions

| Role | Permission ID (catalog) | Scope |
|---|---|---|
| `Admin` | `ACAD_TEACHER_ASSIGN_MANAGE` | phân công/hủy phân công |
| `Admin` | `ACAD_TEACHER_ASSIGN_VIEW` | xem danh sách phân công theo lớp |

## C.2 Input Specification

| Input | Required? | Validation | Source |
|---|---|---|---|
| `class_id` | ✓ | UUID, phải tồn tại trong `classes` | Path param |
| `teacher_id` | ✓ | UUID, phải là user role `Teacher` + status `Active` | Request body |
| `subject_id` | ✓ | UUID, phải tồn tại trong `subjects` | Request body |

## C.3 Output Specification

| Success | Error |
|---|---|
| 201 `TeacherAssignmentOut {teacher_id, class_id, subject_id, assigned_at}` | `ERR-ACAD-CLASS_NOT_FOUND` (404), `ERR-ACAD-SUBJECT_NOT_FOUND` (404), `ERR-ACAD-INVALID_TEACHER_ROLE` (400), `ERR-ACAD-ASSIGNMENT_EXISTS` (409), `ERR-ACAD-ASSIGNMENT_NOT_FOUND` (404), `ERR-AUTH-FORBIDDEN` (403) |

## C.4 Main Flow (End-to-End)

```
Step 1: Admin gửi POST /api/v1/classes/{class_id}/teacher-subjects {teacher_id, subject_id}
Step 2: require_perm("ACAD_TEACHER_ASSIGN_MANAGE") xác thực quyền
Step 3: TeacherAssignmentService validate class_id tồn tại
Step 4: TeacherAssignmentService validate subject_id tồn tại
Step 5: TeacherAssignmentService validate teacher_id là user role Teacher, status Active
Step 6: TeacherAssignmentService kiểm tra (teacher_id, class_id, subject_id) chưa tồn tại
Step 7: Insert bản ghi mới, log EVT-ACAD-TEACHER_ASSIGNED
Step 8: Trả về 201 TeacherAssignmentOut
```

## C.5 API Contract

| Method | Path | Request shape | Response shape | OpenAPI ref |
|---|---|---|---|---|
| POST | `/api/v1/classes/{class_id}/teacher-subjects` | `{teacher_id, subject_id}` | 201 `TeacherAssignmentOut` | tag `academic-teacher-assignment` |
| GET | `/api/v1/classes/{class_id}/teacher-subjects` | — | 200 `TeacherAssignmentOut[]` | tag `academic-teacher-assignment` |
| DELETE | `/api/v1/classes/{class_id}/teacher-subjects/{teacher_id}/{subject_id}` | — | 204 | tag `academic-teacher-assignment` |

## C.6 State Machine

Không áp dụng (quan hệ phân công chỉ có 2 trạng thái ngầm định: tồn tại / không tồn tại, không có state machine tường minh).

## C.7 Business Rules

| BR ID | Rule | Source |
|---|---|---|
| BR-ACAD-04-01 | Một GV chỉ được phân công 1 lần cho cùng (lớp, môn) — trùng `(teacher_id, class_id, subject_id)` bị chặn | `docs/base_sql_erd.sql` `teacher_subjects` composite PK |
| BR-ACAD-04-02 | Chỉ user role `Teacher` + status `Active` mới được phân công | AS-03 `sprint_1_overview.md` |
| BR-ACAD-04-03 | `class_id`, `subject_id` phải tồn tại trước khi tạo phân công | FK constraint |

## C.8 Edge Cases

| EC ID | Scenario | Expected | Test ref |
|---|---|---|---|
| EC-01 | Phân công vào `class_id` không tồn tại | 404 `ERR-ACAD-CLASS_NOT_FOUND` | `TeacherAssignmentIntegrationTest.test_EC01` |
| EC-02 | Phân công với `subject_id` không tồn tại | 404 `ERR-ACAD-SUBJECT_NOT_FOUND` | `TeacherAssignmentIntegrationTest.test_EC02` |
| EC-03 | Phân công `teacher_id` là role Student | 400 `ERR-ACAD-INVALID_TEACHER_ROLE` | `TeacherAssignmentIntegrationTest.test_EC03` |
| EC-04 | Phân công `teacher_id` role Teacher nhưng status Blocked | 400 `ERR-ACAD-INVALID_TEACHER_ROLE` | `TeacherAssignmentIntegrationTest.test_EC04` |
| EC-05 | Phân công (teacher, class, subject) đã tồn tại | 409 `ERR-ACAD-ASSIGNMENT_EXISTS` | `TeacherAssignmentIntegrationTest.test_EC05` |
| EC-06 | Một GV được phân công 2 môn khác nhau ở cùng 1 lớp | 201 cho cả 2 (không vi phạm composite key vì `subject_id` khác) | `TeacherAssignmentIntegrationTest.test_EC06` |
| EC-07 | Hủy phân công không tồn tại | 404 `ERR-ACAD-ASSIGNMENT_NOT_FOUND` | `TeacherAssignmentIntegrationTest.test_EC07` |
| EC-08 | User role Teacher gọi `POST .../teacher-subjects` | 403 `ERR-AUTH-FORBIDDEN` | `TeacherAssignmentIntegrationTest.test_EC08` |

## C.9 UI States

Không áp dụng ở Sprint 1 (chưa có frontend trong scope repo hiện tại).

## C.10 Test Strategy

| Layer | Approach | Framework |
|---|---|---|
| Unit | Mock `TeacherAssignmentRepository` + `ClassRepository` + `SubjectRepository` + user lookup, test `TeacherAssignmentService` (duplicate, role validation) | `pytest` + `pytest-mock` |
| Integration | `TestClient` + SQLite in-memory (`tests/conftest.py`), dùng sẵn `teacher@test.com`/`student@test.com` fixtures + 1 class/subject fixture | `pytest` |

Coverage target: ≥ 80% unit cho `teacher_assignment_service.py`.

---

# PART D — Coding context

> **Owner:** BE Lead · **Gate:** G6.5

## D.1 Task Types Inventory

| Slice ID | Task type | Size | SP | Task file | Status |
|---|---|---|---|---|---|
| S01 | SCHEMA | S | 1 | (inline trong PR, không tách task file riêng) | draft |
| S02 | REPO | S | 1 | ” | draft |
| S03 | SERVICE | M | 2 | ” | draft |
| S04 | API | S | 1 | ” | draft |
| S05 | SEED | S | 1 | ” | draft |
| S06 | TEST | S | 2 | ” | draft |

## D.2 Source of Truth (anchor map)

| Concept | Section anchor |
|---|---|
| API contract | [#c5-api-contract](#c5-api-contract) |
| BR rules | [#c7-business-rules](#c7-business-rules) |
| EC list | [#c8-edge-cases](#c8-edge-cases) |
| ADR | [#b5-architecture-decisions-adr--feature-scope](#b5-architecture-decisions-adr--feature-scope) |
| INV | [#b4-core-invariants-feature-scope](#b4-core-invariants-feature-scope) |
| Table spec | `docs/base_sql_erd.sql` §2.1 |

## D.3 Input Context Pack

| Order | Path | Lý do đọc |
|---|---|---|
| 1 | `docs/v_1/specs/f_acad_04_teacher_assignment_spec.md` (file này) | spec full |
| 2 | `docs/v_1/specs/f_acad_02_classes_spec.md` | Classes phải tồn tại trước, tái dùng `ClassRepository` |
| 3 | `docs/v_1/specs/f_acad_01_subjects_spec.md` | Subjects phải tồn tại trước, tái dùng `SubjectRepository` |
| 4 | `app/modules/auth/` | pattern router/service/repository/schemas |
| 5 | `models/models.py` (class `TeacherSubject`, `User`) | column spec đã định nghĩa sẵn, composite PK 3 cột |
| 6 | `app/modules/auth/dependencies.py` | tái dùng `require_perm`, `get_current_user` |
| 7 | `app/scripts/seed.py` | pattern seed permission idempotent |

## D.4 Output Files (Union)

| File | Action | Slice | Note |
|---|---|---|---|
| `app/modules/academic/models.py` | modify | S01 | thêm re-export `TeacherSubject` |
| `app/modules/academic/schemas.py` | modify | S01 | thêm `TeacherAssignmentCreate`, `TeacherAssignmentOut` |
| `app/modules/academic/repository.py` | modify | S02 | thêm `TeacherAssignmentRepository` |
| `app/modules/academic/services/teacher_assignment_service.py` | create | S03 | |
| `app/modules/academic/routers/teacher_assignments.py` | create | S04 | nested route `/classes/{class_id}/teacher-subjects` |
| `app/main.py` | modify | S04 | `include_router` cho teacher_assignments |
| `app/scripts/seed.py` | modify | S05 | thêm `ACAD_TEACHER_ASSIGN_MANAGE`/`ACAD_TEACHER_ASSIGN_VIEW` |
| `tests/conftest.py` | modify | S05 | seed permission mới cho Admin trong test fixture |
| `tests/academic/integration/test_teacher_assignments.py` | create | S06 | |
| `tests/academic/unit/test_teacher_assignment_service.py` | create | S06 | |

## D.5 Forbidden Files

| Path | Lý do |
|---|---|
| `app/modules/auth/**` | cross-module ban — chỉ được SELECT `User` qua model import |
| `alembic/versions/d00f10e379e6_init_sprint_0_tables.py` | baseline immutable |
| `docs/base_sql_erd.sql` | freeze sau G4, không sửa schema |

## D.6 Constraints (Cross-cutting)

1. Mọi endpoint ghi (`POST`/`DELETE`) MUST bọc `Depends(require_perm("ACAD_TEACHER_ASSIGN_MANAGE"))`; endpoint đọc dùng `ACAD_TEACHER_ASSIGN_VIEW`.
2. Validate thứ tự: `class_id` tồn tại → `subject_id` tồn tại → `teacher_id` hợp lệ (role+status) → check trùng phân công.
3. Mọi ERR raise dùng ID đúng danh mục §E.1.
4. Pydantic schema cho request/response, không expose SQLAlchemy model trực tiếp.
5. File header theo `.claude/rules/coding_rules.md`.

## D.7 Test Commands (feature-level)

```bash
pytest tests/academic -k teacher_assignment
pytest tests -q   # đảm bảo không phá Sprint 0, F-ACAD-01, F-ACAD-02, F-ACAD-03
```

## D.8 Stop Conditions (AI ask-back triggers — cấp feature)

| # | Trigger | Hành động |
|---|---|---|
| F1 | Cần touch bảng ngoài `teacher_subjects`/`classes`/`subjects`/`users` (read-only) | STOP, escalate Architect |
| F2 | Cần catalog ID mới ngoài danh sách §E.1 | STOP, bổ sung §E.1 cùng PR |
| F3 | Phát hiện BR/EC mới chưa có ở §C.7/§C.8 | STOP, update spec cùng PR |

---

# PART E — Tracking & Sign-off

> **Owner:** PM

## E.1 Catalog Dependencies

| Catalog | IDs used |
|---|---|
| Error codes | `ERR-ACAD-INVALID_TEACHER_ROLE`, `ERR-ACAD-ASSIGNMENT_EXISTS`, `ERR-ACAD-ASSIGNMENT_NOT_FOUND` |
| Permissions | `ACAD_TEACHER_ASSIGN_MANAGE`, `ACAD_TEACHER_ASSIGN_VIEW` |
| Events | `EVT-ACAD-TEACHER_ASSIGNED`, `EVT-ACAD-TEACHER_UNASSIGNED` |

## E.2 Task Breakdown

| Slice | Task ID | Type | Size | SP | Depends on | Owner | PR | Status |
|---|---|---|---|---|---|---|---|---|
| S01 | `F-ACAD-04-TASK-001` | SCHEMA | S | 1 | `F-ACAD-02` approved | BE | — | draft |
| S02 | `F-ACAD-04-TASK-002` | REPO | S | 1 | S01 | BE | — | draft |
| S03 | `F-ACAD-04-TASK-003` | SERVICE | M | 2 | S02 | BE | — | draft |
| S04 | `F-ACAD-04-TASK-004` | API | S | 1 | S03 | BE | — | draft |
| S05 | `F-ACAD-04-TASK-005` | SEED | S | 1 | S04 | BE | — | draft |
| S06 | `F-ACAD-04-TASK-006` | TEST | S | 2 | S05 | BE | — | draft |

## E.3 AI Session Plan Overview

| Slice | AI tier | Task file | AI session # |
|---|---|---|---|
| S01–S06 | T1 | (gộp 1 PR do scope nhỏ) | 4 |

## E.4 Sign-off Matrix

| PART | Gate | Owner | Approver | Status | Người ACK | Ngày |
|---|---|---|---|---|---|---|
| A Business | G3 | BA/PM | Lead | `approved` | | 2026-07-18 |
| B Architecture | G4 | Architect | CTO | `approved` | | 2026-07-18 |
| C Design | G6 | Lead | Lead | `approved` | | 2026-07-18 |
| D Coding | G6.5 | BE Lead | BE Lead | `approved` | | 2026-07-18 |
| E Tracking | G7+ | PM | PM | `approved` | | 2026-07-18 |

**Update rule:** task chỉ start khi PART A→D đều `approved` VÀ `F-ACAD-02` đã đạt G6.5 `approved`.

## E.5 PR Evidence Index

| PR # | Slice | Task ID | Merged date | Notes |
|---|---|---|---|---|
| | | | | (chưa code — spec-only tại thời điểm này) |

---

## Changelog

| Date | Version | Change | Author |
|---|---|---|---|
| 2026-07-18 | v1.0 | Initial spec — breakdown từ `sprint_1_overview.md` | AI Agent |
