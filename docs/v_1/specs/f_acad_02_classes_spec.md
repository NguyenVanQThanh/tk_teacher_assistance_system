# Feature Spec — `F-ACAD-02` Classes (CRUD lớp học)

> Path: `docs/v_1/specs/f_acad_02_classes_spec.md` · Sprint: [sprint_1_overview.md](../sprints/sprint_1_overview.md)

---

## Document Header

| Field | Giá trị |
|---|---|
| Feature ID | `F-ACAD-02` |
| Feature name | Classes — CRUD lớp học |
| Module(s) | `academic` |
| Sprint(s) allocated | `SPRINT-01` |
| Lane | `standard` |
| Spec version | `v1.0` |
| Last updated | `2026-07-18` |
| Source binding | SOP §12 · `docs/base_sql_erd.sql` v1.0 (bảng `classes`) · [f_acad_01_subjects_spec.md](f_acad_01_subjects_spec.md) (module `academic` golden pattern) · `f_auth_01_spec.md` (RBAC, current-user) · `.claude/rules/coding_rules.md` |

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

Cho phép **Admin** quản lý danh mục lớp học (`classes`), bao gồm gán giáo viên chủ nhiệm (`homeroom_teacher_id`). Lớp học là điều kiện tiên quyết để ghi danh học sinh (`F-ACAD-03`) và phân công giáo viên bộ môn (`F-ACAD-04`). Bảng `classes` đã tồn tại từ baseline migration Sprint 0 (`F-FND-01`) — feature này chỉ xây tầng nghiệp vụ, không migration mới. Phụ thuộc `F-ACAD-01` đã `approved` (dùng chung pattern module `academic`).

## A.2 User Stories

| Story ID | As (role) | I want (capability) | So that (value) |
|---|---|---|---|
| US-01 | Admin | tạo lớp học mới, có thể gán GVCN | có danh mục lớp để ghi danh HS/phân công GV |
| US-02 | Admin | xem danh sách/chi tiết lớp học | biết lớp nào đã tồn tại, ai là GVCN |
| US-03 | Admin | sửa tên lớp/năm học/GVCN | cập nhật khi có thay đổi tổ chức |
| US-04 | Admin | xóa lớp học không còn dùng | dọn dẹp danh mục |

## A.3 REQ Registry

| REQ ID | Mô tả ngắn | Priority | Status | Linked Story |
|---|---|---|---|---|
| REQ-ACAD-005 | Tạo lớp học (`class_name` unique trong năm học, validate GVCN) | P0 | `approved` | US-01 |
| REQ-ACAD-006 | Liệt kê + xem chi tiết lớp học | P0 | `approved` | US-02 |
| REQ-ACAD-007 | Sửa lớp học | P1 | `approved` | US-03 |
| REQ-ACAD-008 | Xóa lớp học | P1 | `approved` | US-04 |

## A.4 Acceptance Criteria (Feature-level)

| AC ID | REQ | Given | When | Then |
|---|---|---|---|---|
| AC-01 | REQ-ACAD-005 | Admin đã đăng nhập, tên lớp chưa tồn tại | `POST /api/v1/classes` | 201, trả về class vừa tạo |
| AC-02 | REQ-ACAD-005 | tên lớp đã tồn tại | `POST /api/v1/classes` | 409 `ERR-ACAD-CLASS_DUPLICATE_NAME` |
| AC-03 | REQ-ACAD-005 | `homeroom_teacher_id` không phải role Teacher hoặc không Active | `POST /api/v1/classes` | 400 `ERR-ACAD-INVALID_HOMEROOM_TEACHER` |
| AC-04 | REQ-ACAD-006 | có N lớp trong DB | `GET /api/v1/classes` | 200, danh sách N lớp |
| AC-05 | REQ-ACAD-006 | `class_id` không tồn tại | `GET /api/v1/classes/{id}` | 404 `ERR-ACAD-CLASS_NOT_FOUND` |
| AC-06 | REQ-ACAD-007 | lớp tồn tại, đổi GVCN sang Teacher Active khác | `PUT /api/v1/classes/{id}` | 200, thông tin cập nhật |
| AC-07 | REQ-ACAD-008 | lớp học tồn tại | `DELETE /api/v1/classes/{id}` | 200/204, lớp bị xóa |
| AC-08 | REQ-ACAD-005..008 | user không có permission `ACAD_CLASS_MANAGE`/`ACAD_CLASS_VIEW` | gọi endpoint tương ứng | 403 `ERR-AUTH-FORBIDDEN` |

## A.5 In / Out of Scope

**In scope:**
- CRUD đầy đủ cho `classes`: create, list, get by id, update, delete.
- Validate `homeroom_teacher_id` (nếu cung cấp) phải là user role `Teacher` và status `Active` (AS-02, `sprint_1_overview.md`).
- Validate `class_name` unique.

**Out of scope (defer):**
- Ghi danh học sinh vào lớp — thuộc [f_acad_03_enrollment_spec.md](f_acad_03_enrollment_spec.md).
- Phân công giáo viên bộ môn — thuộc [f_acad_04_teacher_assignment_spec.md](f_acad_04_teacher_assignment_spec.md).
- Soft-delete / audit trail xóa lớp (hard delete theo constraint DB hiện tại).

## A.6 REQ → Task Type Map

| REQ ID | Task type(s) cần | Note |
|---|---|---|
| REQ-ACAD-005/006/007/008 | SCHEMA → REPO → SERVICE → API → TEST | CRUD chuẩn, không cần MIG (bảng đã có) |

## A.7 Feature DoD

| ✓ | Tiêu chí Feature Done |
|---|---|
| ☐ | Tất cả AC §A.4 verified qua test |
| ☐ | `pytest tests/academic -k class` pass |
| ☐ | Permission `ACAD_CLASS_MANAGE`, `ACAD_CLASS_VIEW` seed cho role Admin |
| ☐ | Sign-off §E.4 hoàn tất |

---

# PART B — Architecture

> **Owner:** Architect · **Approver:** CTO · **Gate:** G4

## B.1 Executive Summary (architectural)

Feature CRUD trên bảng `classes` đã tồn tại, tuân theo layering giống `F-ACAD-01`. Điểm khác biệt duy nhất so với Subjects: cần validate FK `homeroom_teacher_id` trỏ tới `users` (role Teacher, status Active) trước khi insert/update — tái dùng `UserRepository` (nếu có) hoặc query trực tiếp qua `User` model từ `models.models`.

## B.2 High-Level Architecture

### B.2.1 Layered diagram

```
Client → FastAPI Router (classes.py) → ClassService → ClassRepository → PostgreSQL (classes)
                                            │                │
                                            │                └─→ User model (validate homeroom_teacher_id)
                                            ▼
                                  require_perm("ACAD_CLASS_*")
```

### B.2.2 Critical data flow

1. Admin gọi `POST /api/v1/classes` kèm Bearer token, `{class_name, school_year, homeroom_teacher_id?}`.
2. `require_perm("ACAD_CLASS_MANAGE")` xác thực quyền.
3. Nếu `homeroom_teacher_id` được cung cấp, `ClassService` validate user đó tồn tại, role `Teacher`, status `Active` → nếu không, raise `ERR-ACAD-INVALID_HOMEROOM_TEACHER`.
4. `ClassService.create_class` kiểm tra trùng tên qua `ClassRepository.get_by_name`.
5. Insert bản ghi `classes`, log `EVT-ACAD-CLASS_CREATED`, trả về `ClassOut`.

## B.3 Domain Ownership Matrix

| Table / Resource | Owner module | Readers | Writers (cross-module) |
|---|---|---|---|
| `classes` | `academic` | `academic` (Enrollment, Teacher Assignment dùng làm FK reference) | (none) |
| `users` (read-only, validate homeroom) | `auth` | `academic` (chỉ SELECT, không ghi) | — |

## B.4 Core Invariants (Feature-scope)

| ID | Invariant | Scope | Reference |
|---|---|---|---|
| `INV-ACAD-02-01` | `class_name` unique | feature | `docs/base_sql_erd.sql` `classes.class_name` |
| `INV-ACAD-02-02` | `homeroom_teacher_id` (nếu set) phải trỏ tới user role `Teacher` và status `Active` | feature | AS-02 `sprint_1_overview.md` |
| `INV-ACAD-02-03` | Không migration mới — bảng `classes` bất biến về cấu trúc | feature | baseline `d00f10e379e6_init_sprint_0_tables.py` |

## B.5 Architecture Decisions (ADR — Feature-scope)

| ADR ID | Title | Status | Approver | Date | Summary |
|---|---|---|---|---|---|
| `ADR-ACAD-02-001` | Validate `homeroom_teacher_id` ở Service layer (không dùng DB trigger/CHECK) | `approved` | CTO | 2026-07-18 | Giữ business rule ở tầng ứng dụng, nhất quán pattern hiện có (không dùng trigger DB) |
| `ADR-ACAD-02-002` | `academic` module chỉ SELECT trên `users`, không ghi | `approved` | CTO | 2026-07-18 | Tránh vi phạm domain ownership (`users` thuộc `auth`) |

## B.6 API Boundary

| Method | Path | Auth | OpenAPI tag |
|---|---|---|---|
| POST | `/api/v1/classes` | Bearer + `ACAD_CLASS_MANAGE` | `academic-classes` |
| GET | `/api/v1/classes` | Bearer + `ACAD_CLASS_VIEW` | `academic-classes` |
| GET | `/api/v1/classes/{class_id}` | Bearer + `ACAD_CLASS_VIEW` | `academic-classes` |
| PUT | `/api/v1/classes/{class_id}` | Bearer + `ACAD_CLASS_MANAGE` | `academic-classes` |
| DELETE | `/api/v1/classes/{class_id}` | Bearer + `ACAD_CLASS_MANAGE` | `academic-classes` |

## B.7 Database Boundary

| Table | Op | Table spec file | Migration |
|---|---|---|---|
| `classes` | SELECT/INSERT/UPDATE/DELETE (không đổi schema) | `docs/base_sql_erd.sql` §2.1 | không có (dùng baseline có sẵn) |
| `users` | SELECT only (validate `homeroom_teacher_id`) | `docs/base_sql_erd.sql` §1.1 | không có |

## B.8 Security & Privacy

| Aspect | Decision |
|---|---|
| AuthN | JWT bearer, tái dùng `get_current_user` |
| AuthZ | `Depends(require_perm("ACAD_CLASS_MANAGE"))` / `require_perm("ACAD_CLASS_VIEW")` |
| PII handling | `classes` không chứa PII trực tiếp; response chỉ trả `homeroom_teacher_id` (UUID), không trả thông tin cá nhân GV |
| Audit | Log `EVT-ACAD-CLASS_CREATED`/`UPDATED`/`DELETED` qua `logger.info` |
| Rate limit | Không cần |

## B.9 Observability & Operations

| Aspect | Plan |
|---|---|
| Structured log | `logger.info/warning("Domain Event: EVT-ACAD-...")`, theo pattern `auth_service.py` |
| Metrics | Chưa cần (Sprint 1 scope nhỏ) |
| Runbook | Không cần riêng |

## B.10 Risk Register

| Risk ID | Severity | Description | Mitigation | Owner |
|---|---|---|---|---|
| RISK-ACAD-02-01 | M | Xóa `classes` đang có `student_class`/`teacher_subjects` tham chiếu (`ON DELETE CASCADE`) làm mất dữ liệu ghi danh/phân công | Cảnh báo rõ trong response khi xóa; document trong C.8 Edge Cases | BE Lead |
| RISK-ACAD-02-02 | L | GVCN bị đổi role/status Inactive sau khi đã gán — dữ liệu cũ `homeroom_teacher_id` không tự động revalidate | Chấp nhận rủi ro Sprint 1 (không có background job); validate chỉ tại thời điểm ghi | BE Lead |

---

# PART C — Design

> **Owner:** Lead · **Gate:** G6

## C.1 User Roles & Permissions

| Role | Permission ID (catalog) | Scope |
|---|---|---|
| `Admin` | `ACAD_CLASS_MANAGE` | create/update/delete |
| `Admin` | `ACAD_CLASS_VIEW` | list/get |

## C.2 Input Specification

| Input | Required? | Validation | Source |
|---|---|---|---|
| `class_name` | ✓ | string, max 100, unique | Request body |
| `school_year` | ✓ | string, ví dụ `2026-2027` | Request body |
| `homeroom_teacher_id` | ✗ | UUID, phải là user role `Teacher` + status `Active` nếu cung cấp | Request body |

## C.3 Output Specification

| Success | Error |
|---|---|
| 201 `ClassOut {class_id, class_name, school_year, homeroom_teacher_id, created_at, updated_at}` | `ERR-ACAD-CLASS_NOT_FOUND` (404), `ERR-ACAD-CLASS_DUPLICATE_NAME` (409), `ERR-ACAD-INVALID_HOMEROOM_TEACHER` (400), `ERR-AUTH-FORBIDDEN` (403) |

## C.4 Main Flow (End-to-End)

```
Step 1: Admin gửi POST /api/v1/classes {class_name, school_year, homeroom_teacher_id?}
Step 2: require_perm("ACAD_CLASS_MANAGE") xác thực quyền
Step 3: Nếu có homeroom_teacher_id: ClassService validate role=Teacher, status=Active
Step 4: ClassService kiểm tra class_name chưa tồn tại (ClassRepository.get_by_name)
Step 5: Insert bản ghi mới, log EVT-ACAD-CLASS_CREATED
Step 6: Trả về 201 ClassOut
```

## C.5 API Contract

| Method | Path | Request shape | Response shape | OpenAPI ref |
|---|---|---|---|---|
| POST | `/api/v1/classes` | `{class_name, school_year, homeroom_teacher_id?}` | 201 `ClassOut` | tag `academic-classes` |
| GET | `/api/v1/classes` | — | 200 `ClassOut[]` | tag `academic-classes` |
| GET | `/api/v1/classes/{class_id}` | — | 200 `ClassOut` | tag `academic-classes` |
| PUT | `/api/v1/classes/{class_id}` | `{class_name?, school_year?, homeroom_teacher_id?}` | 200 `ClassOut` | tag `academic-classes` |
| DELETE | `/api/v1/classes/{class_id}` | — | 204 | tag `academic-classes` |

## C.6 State Machine

Không áp dụng (resource CRUD đơn giản, không có state machine).

## C.7 Business Rules

| BR ID | Rule | Source |
|---|---|---|
| BR-ACAD-02-01 | `class_name` phải unique trong toàn hệ thống | `docs/base_sql_erd.sql` `classes.class_name` |
| BR-ACAD-02-02 | `homeroom_teacher_id` (nếu set) phải là user role `Teacher` và status `Active` | AS-02 `sprint_1_overview.md` |
| BR-ACAD-02-03 | Update `class_name` phải kiểm tra trùng với lớp khác (loại trừ chính nó) | nghiệp vụ, tương tự BR-ACAD-01-02 |

## C.8 Edge Cases

| EC ID | Scenario | Expected | Test ref |
|---|---|---|---|
| EC-01 | Tạo lớp với `homeroom_teacher_id` trỏ tới user role Student | 400 `ERR-ACAD-INVALID_HOMEROOM_TEACHER` | `ClassIntegrationTest.test_EC01` |
| EC-02 | Tạo lớp với `homeroom_teacher_id` trỏ tới Teacher nhưng status Inactive/Blocked | 400 `ERR-ACAD-INVALID_HOMEROOM_TEACHER` | `ClassIntegrationTest.test_EC02` |
| EC-03 | Tạo lớp không có `homeroom_teacher_id` (optional) | 201, `homeroom_teacher_id` = null | `ClassIntegrationTest.test_EC03` |
| EC-04 | Tạo lớp với tên đã tồn tại | 409 `ERR-ACAD-CLASS_DUPLICATE_NAME` | `ClassIntegrationTest.test_EC04` |
| EC-05 | Xem/sửa/xóa `class_id` không tồn tại | 404 `ERR-ACAD-CLASS_NOT_FOUND` | `ClassIntegrationTest.test_EC05` |
| EC-06 | User role Teacher gọi `POST /api/v1/classes` | 403 `ERR-AUTH-FORBIDDEN` | `ClassIntegrationTest.test_EC06` |

## C.9 UI States

Không áp dụng ở Sprint 1 (chưa có frontend trong scope repo hiện tại).

## C.10 Test Strategy

| Layer | Approach | Framework |
|---|---|---|
| Unit | Mock `ClassRepository` + user lookup, test `ClassService` (duplicate check, homeroom validation) | `pytest` + `pytest-mock` |
| Integration | `TestClient` + SQLite in-memory (`tests/conftest.py`), dùng sẵn `teacher@test.com`/`student@test.com` fixtures | `pytest` |

Coverage target: ≥ 80% unit cho `class_service.py`.

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
| 1 | `docs/v_1/specs/f_acad_02_classes_spec.md` (file này) | spec full |
| 2 | `docs/v_1/specs/f_acad_01_subjects_spec.md` | golden pattern module `academic` (đã code trước) |
| 3 | `app/modules/auth/` | pattern router/service/repository/schemas |
| 4 | `models/models.py` (class `Class`, `User`) | column spec đã định nghĩa sẵn, FK `homeroom_teacher_id` |
| 5 | `app/modules/auth/dependencies.py` | tái dùng `require_perm`, `get_current_user` |
| 6 | `app/scripts/seed.py` | pattern seed permission idempotent |

## D.4 Output Files (Union)

| File | Action | Slice | Note |
|---|---|---|---|
| `app/modules/academic/models.py` | modify | S01 | thêm re-export `Class` (file đã tồn tại từ F-ACAD-01) |
| `app/modules/academic/schemas.py` | modify | S01 | thêm `ClassCreate`, `ClassUpdate`, `ClassOut` |
| `app/modules/academic/repository.py` | modify | S02 | thêm `ClassRepository` |
| `app/modules/academic/services/class_service.py` | create | S03 | bao gồm validate homeroom teacher |
| `app/modules/academic/routers/classes.py` | create | S04 | |
| `app/main.py` | modify | S04 | `include_router` cho classes |
| `app/scripts/seed.py` | modify | S05 | thêm `ACAD_CLASS_MANAGE`/`ACAD_CLASS_VIEW` |
| `tests/conftest.py` | modify | S05 | seed permission mới cho Admin trong test fixture |
| `tests/academic/integration/test_classes.py` | create | S06 | |
| `tests/academic/unit/test_class_service.py` | create | S06 | |

## D.5 Forbidden Files

| Path | Lý do |
|---|---|
| `app/modules/auth/**` | cross-module ban — chỉ được SELECT `User` qua model import, không sửa auth module |
| `alembic/versions/d00f10e379e6_init_sprint_0_tables.py` | baseline immutable |
| `docs/base_sql_erd.sql` | freeze sau G4, không sửa schema |

## D.6 Constraints (Cross-cutting)

1. Mọi endpoint ghi (`POST`/`PUT`/`DELETE`) MUST bọc `Depends(require_perm("ACAD_CLASS_MANAGE"))`; endpoint đọc dùng `ACAD_CLASS_VIEW`.
2. Validate `homeroom_teacher_id` phải thực hiện trong Service layer trước khi gọi Repository insert/update.
3. Mọi ERR raise dùng ID đúng danh mục §E.1.
4. Pydantic schema cho request/response, không expose SQLAlchemy model trực tiếp.
5. File header theo `.claude/rules/coding_rules.md`.

## D.7 Test Commands (feature-level)

```bash
pytest tests/academic -k class
pytest tests -q   # đảm bảo không phá Sprint 0 và F-ACAD-01
```

## D.8 Stop Conditions (AI ask-back triggers — cấp feature)

| # | Trigger | Hành động |
|---|---|---|
| F1 | Cần touch bảng ngoài `classes`/`users` (read-only) | STOP, escalate Architect |
| F2 | Cần catalog ID mới ngoài danh sách §E.1 | STOP, bổ sung §E.1 cùng PR |
| F3 | Phát hiện BR/EC mới chưa có ở §C.7/§C.8 | STOP, update spec cùng PR |

---

# PART E — Tracking & Sign-off

> **Owner:** PM

## E.1 Catalog Dependencies

| Catalog | IDs used |
|---|---|
| Error codes | `ERR-ACAD-CLASS_NOT_FOUND`, `ERR-ACAD-CLASS_DUPLICATE_NAME`, `ERR-ACAD-INVALID_HOMEROOM_TEACHER` |
| Permissions | `ACAD_CLASS_MANAGE`, `ACAD_CLASS_VIEW` |
| Events | `EVT-ACAD-CLASS_CREATED`, `EVT-ACAD-CLASS_UPDATED`, `EVT-ACAD-CLASS_DELETED` |

## E.2 Task Breakdown

| Slice | Task ID | Type | Size | SP | Depends on | Owner | PR | Status |
|---|---|---|---|---|---|---|---|---|
| S01 | `F-ACAD-02-TASK-001` | SCHEMA | S | 1 | `F-ACAD-01` approved | BE | — | draft |
| S02 | `F-ACAD-02-TASK-002` | REPO | S | 1 | S01 | BE | — | draft |
| S03 | `F-ACAD-02-TASK-003` | SERVICE | M | 2 | S02 | BE | — | draft |
| S04 | `F-ACAD-02-TASK-004` | API | S | 1 | S03 | BE | — | draft |
| S05 | `F-ACAD-02-TASK-005` | SEED | S | 1 | S04 | BE | — | draft |
| S06 | `F-ACAD-02-TASK-006` | TEST | S | 2 | S05 | BE | — | draft |

## E.3 AI Session Plan Overview

| Slice | AI tier | Task file | AI session # |
|---|---|---|---|
| S01–S06 | T1 | (gộp 1 PR do scope nhỏ) | 2 |

## E.4 Sign-off Matrix

| PART | Gate | Owner | Approver | Status | Người ACK | Ngày |
|---|---|---|---|---|---|---|
| A Business | G3 | BA/PM | Lead | `approved` | | 2026-07-18 |
| B Architecture | G4 | Architect | CTO | `approved` | | 2026-07-18 |
| C Design | G6 | Lead | Lead | `approved` | | 2026-07-18 |
| D Coding | G6.5 | BE Lead | BE Lead | `approved` | | 2026-07-18 |
| E Tracking | G7+ | PM | PM | `approved` | | 2026-07-18 |

**Update rule:** task chỉ start khi PART A→D đều `approved` VÀ `F-ACAD-01` đã đạt G6.5 `approved`.

## E.5 PR Evidence Index

| PR # | Slice | Task ID | Merged date | Notes |
|---|---|---|---|---|
| | | | | (chưa code — spec-only tại thời điểm này) |

---

## Changelog

| Date | Version | Change | Author |
|---|---|---|---|
| 2026-07-18 | v1.0 | Initial spec — breakdown từ `sprint_1_overview.md` | AI Agent |
