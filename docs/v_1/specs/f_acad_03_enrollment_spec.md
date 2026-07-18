# Feature Spec — `F-ACAD-03` Enrollment (Ghi danh học sinh vào lớp)

> Path: `docs/v_1/specs/f_acad_03_enrollment_spec.md` · Sprint: [sprint_1_overview.md](../sprints/sprint_1_overview.md)

---

## Document Header

| Field | Giá trị |
|---|---|
| Feature ID | `F-ACAD-03` |
| Feature name | Enrollment — Ghi danh học sinh vào lớp |
| Module(s) | `academic` |
| Sprint(s) allocated | `SPRINT-01` |
| Lane | `standard` |
| Spec version | `v1.0` |
| Last updated | `2026-07-18` |
| Source binding | SOP §12 · `docs/base_sql_erd.sql` v1.0 (bảng `student_class`) · [f_acad_02_classes_spec.md](f_acad_02_classes_spec.md) (Classes phải tồn tại trước) · `f_auth_01_spec.md` (RBAC, current-user) · `.claude/rules/coding_rules.md` |

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

Cho phép **Admin** ghi danh (enroll) học sinh vào lớp học và hủy ghi danh, quản lý bảng liên kết `student_class`. Đây là điều kiện tiên quyết trực tiếp cho NFR RBAC "GV chỉ quản lý HS thuộc lớp mình phụ trách" (SRS §3) — dữ liệu `student_class` sẽ được dùng để filter ở các sprint sau (Tracking, Teacher Dashboard). Bảng `student_class` đã tồn tại từ baseline migration Sprint 0 — feature này chỉ xây tầng nghiệp vụ, không migration mới. Phụ thuộc `F-ACAD-02` (Classes) đã `approved`.

## A.2 User Stories

| Story ID | As (role) | I want (capability) | So that (value) |
|---|---|---|---|
| US-01 | Admin | ghi danh học sinh vào một lớp | học sinh được gắn với lớp học cụ thể |
| US-02 | Admin | xem danh sách học sinh trong một lớp | biết lớp có bao nhiêu HS, ai đã ghi danh |
| US-03 | Admin | hủy ghi danh học sinh khỏi lớp | điều chỉnh khi HS chuyển lớp/nghỉ học |

## A.3 REQ Registry

| REQ ID | Mô tả ngắn | Priority | Status | Linked Story |
|---|---|---|---|---|
| REQ-ACAD-009 | Ghi danh học sinh vào lớp (validate role Student + Active, chống trùng) | P0 | `approved` | US-01 |
| REQ-ACAD-010 | Liệt kê học sinh trong một lớp | P0 | `approved` | US-02 |
| REQ-ACAD-011 | Hủy ghi danh học sinh khỏi lớp | P1 | `approved` | US-03 |

## A.4 Acceptance Criteria (Feature-level)

| AC ID | REQ | Given | When | Then |
|---|---|---|---|---|
| AC-01 | REQ-ACAD-009 | `class_id` tồn tại, `student_id` là user role Student + Active, chưa ghi danh lớp này | `POST /api/v1/classes/{class_id}/students` | 201, trả về bản ghi ghi danh |
| AC-02 | REQ-ACAD-009 | học sinh đã ghi danh lớp này rồi | `POST /api/v1/classes/{class_id}/students` | 409 `ERR-ACAD-ALREADY_ENROLLED` |
| AC-03 | REQ-ACAD-009 | `student_id` không phải role Student hoặc không Active | `POST /api/v1/classes/{class_id}/students` | 400 `ERR-ACAD-INVALID_STUDENT_ROLE` |
| AC-04 | REQ-ACAD-009 | `student_id` không tồn tại | `POST /api/v1/classes/{class_id}/students` | 404 `ERR-ACAD-STUDENT_NOT_FOUND` |
| AC-05 | REQ-ACAD-009 | `student_code` cung cấp đã dùng cho HS khác | `POST /api/v1/classes/{class_id}/students` | 409 `ERR-ACAD-DUPLICATE_STUDENT_CODE` |
| AC-06 | REQ-ACAD-010 | `class_id` tồn tại, có N học sinh đã ghi danh | `GET /api/v1/classes/{class_id}/students` | 200, danh sách N học sinh |
| AC-07 | REQ-ACAD-011 | học sinh đã ghi danh lớp | `DELETE /api/v1/classes/{class_id}/students/{student_id}` | 200/204, hủy ghi danh |
| AC-08 | REQ-ACAD-011 | học sinh chưa ghi danh lớp này | `DELETE /api/v1/classes/{class_id}/students/{student_id}` | 404 `ERR-ACAD-ENROLLMENT_NOT_FOUND` |
| AC-09 | REQ-ACAD-009..011 | user không có permission `ACAD_ENROLLMENT_MANAGE`/`ACAD_ENROLLMENT_VIEW` | gọi endpoint tương ứng | 403 `ERR-AUTH-FORBIDDEN` |
| AC-10 | REQ-ACAD-009 | `class_id` không tồn tại | `POST /api/v1/classes/{class_id}/students` | 404 `ERR-ACAD-CLASS_NOT_FOUND` |

## A.5 In / Out of Scope

**In scope:**
- Ghi danh học sinh vào lớp (`POST`), liệt kê học sinh trong lớp (`GET`), hủy ghi danh (`DELETE`).
- Validate học sinh phải role `Student` và status `Active` (AS-03, `sprint_1_overview.md`).
- Validate `student_code` unique nếu được cung cấp (theo constraint DB `student_class.student_code`).
- Chống ghi danh trùng (composite key `student_id` + `class_id`).

**Out of scope (defer):**
- Chuyển lớp tự động (transfer) — Admin thực hiện bằng cách hủy ghi danh cũ + ghi danh mới (2 API call riêng biệt), không có API "move" gộp.
- Lịch sử ghi danh (audit trail qua các năm học) — hard delete khi hủy ghi danh.
- Ghi danh hàng loạt (bulk enroll) nhiều học sinh một lúc.

## A.6 REQ → Task Type Map

| REQ ID | Task type(s) cần | Note |
|---|---|---|
| REQ-ACAD-009/010/011 | SCHEMA → REPO → SERVICE → API → TEST | CRUD trên bảng liên kết, không cần MIG (bảng đã có) |

## A.7 Feature DoD

| ✓ | Tiêu chí Feature Done |
|---|---|
| ☐ | Tất cả AC §A.4 verified qua test |
| ☐ | `pytest tests/academic -k enrollment` pass |
| ☐ | Permission `ACAD_ENROLLMENT_MANAGE`, `ACAD_ENROLLMENT_VIEW` seed cho role Admin |
| ☐ | Sign-off §E.4 hoàn tất |

---

# PART B — Architecture

> **Owner:** Architect · **Approver:** CTO · **Gate:** G4

## B.1 Executive Summary (architectural)

Feature quản lý bảng liên kết nhiều-nhiều `student_class` (composite PK `student_id` + `class_id`, cột phụ `student_code` unique). Endpoint lồng dưới resource `classes` (`/api/v1/classes/{class_id}/students`) theo REST nested-resource convention. Cần validate 2 chiều: `class_id` tồn tại (từ `F-ACAD-02`) và `student_id` là user hợp lệ (role Student, Active — read-only từ `auth`/`users`).

## B.2 High-Level Architecture

### B.2.1 Layered diagram

```
Client → FastAPI Router (enrollments.py) → EnrollmentService → EnrollmentRepository → PostgreSQL (student_class)
                                                  │                     │
                                                  │                     └─→ ClassRepository (validate class_id tồn tại)
                                                  │                     └─→ User model (validate student role/status)
                                                  ▼
                                       require_perm("ACAD_ENROLLMENT_*")
```

### B.2.2 Critical data flow

1. Admin gọi `POST /api/v1/classes/{class_id}/students` kèm Bearer token, `{student_id, student_code?}`.
2. `require_perm("ACAD_ENROLLMENT_MANAGE")` xác thực quyền.
3. `EnrollmentService` validate `class_id` tồn tại (dùng `ClassRepository.get_by_id` từ module `academic` — tái dùng nội bộ, không cross-module).
4. Validate `student_id` là user tồn tại, role `Student`, status `Active`.
5. Validate chưa có bản ghi `student_class(student_id, class_id)` trùng.
6. Validate `student_code` (nếu có) chưa dùng bởi HS khác.
7. Insert bản ghi, log `EVT-ACAD-STUDENT_ENROLLED`, trả về `EnrollmentOut`.

## B.3 Domain Ownership Matrix

| Table / Resource | Owner module | Readers | Writers (cross-module) |
|---|---|---|---|
| `student_class` | `academic` | `academic` (S3 Tracking, S5 Teacher Dashboard dùng để filter HS theo lớp) | (none) |
| `classes` (read, validate `class_id`) | `academic` | `academic` (nội bộ, không cross-module) | — |
| `users` (read-only, validate student) | `auth` | `academic` (chỉ SELECT) | — |

## B.4 Core Invariants (Feature-scope)

| ID | Invariant | Scope | Reference |
|---|---|---|---|
| `INV-ACAD-03-01` | Composite key `(student_id, class_id)` unique — một HS chỉ ghi danh 1 lần / lớp | feature | `docs/base_sql_erd.sql` `student_class` PK |
| `INV-ACAD-03-02` | `student_code` (nếu set) unique toàn hệ thống | feature | `docs/base_sql_erd.sql` `student_class.student_code UNIQUE` |
| `INV-ACAD-03-03` | Học sinh ghi danh phải role `Student` và status `Active` | feature | AS-03 `sprint_1_overview.md` |
| `INV-ACAD-03-04` | Không migration mới — bảng `student_class` bất biến về cấu trúc | feature | baseline `d00f10e379e6_init_sprint_0_tables.py` |

## B.5 Architecture Decisions (ADR — Feature-scope)

| ADR ID | Title | Status | Approver | Date | Summary |
|---|---|---|---|---|---|
| `ADR-ACAD-03-001` | Endpoint nested dưới `/classes/{class_id}/students` thay vì resource độc lập `/enrollments` | `approved` | CTO | 2026-07-18 | Phản ánh đúng quan hệ phụ thuộc (ghi danh luôn gắn với 1 lớp cụ thể), URL rõ ràng hơn |
| `ADR-ACAD-03-002` | Hard delete khi hủy ghi danh (không giữ lịch sử) | `approved` | CTO | 2026-07-18 | SRS không yêu cầu lịch sử ghi danh qua các năm; giữ đơn giản Sprint 1 |

## B.6 API Boundary

| Method | Path | Auth | OpenAPI tag |
|---|---|---|---|
| POST | `/api/v1/classes/{class_id}/students` | Bearer + `ACAD_ENROLLMENT_MANAGE` | `academic-enrollment` |
| GET | `/api/v1/classes/{class_id}/students` | Bearer + `ACAD_ENROLLMENT_VIEW` | `academic-enrollment` |
| DELETE | `/api/v1/classes/{class_id}/students/{student_id}` | Bearer + `ACAD_ENROLLMENT_MANAGE` | `academic-enrollment` |

## B.7 Database Boundary

| Table | Op | Table spec file | Migration |
|---|---|---|---|
| `student_class` | SELECT/INSERT/DELETE (không đổi schema) | `docs/base_sql_erd.sql` §2.1 | không có (dùng baseline có sẵn) |
| `classes` | SELECT only (validate `class_id`) | `docs/base_sql_erd.sql` §2.1 | không có |
| `users` | SELECT only (validate student role/status) | `docs/base_sql_erd.sql` §1.1 | không có |

## B.8 Security & Privacy

| Aspect | Decision |
|---|---|
| AuthN | JWT bearer, tái dùng `get_current_user` |
| AuthZ | `Depends(require_perm("ACAD_ENROLLMENT_MANAGE"))` / `require_perm("ACAD_ENROLLMENT_VIEW")` |
| PII handling | Response `GET .../students` chỉ trả `student_id`, `student_code`, không trả thông tin cá nhân khác của HS (email/phone thuộc `users`, không expose ở đây) |
| Audit | Log `EVT-ACAD-STUDENT_ENROLLED`/`UNENROLLED` qua `logger.info` |
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
| RISK-ACAD-03-01 | M | HS bị đổi role/status Inactive sau khi đã ghi danh — dữ liệu `student_class` không tự động dọn | Chấp nhận rủi ro Sprint 1; validate chỉ tại thời điểm ghi danh, không có background job | BE Lead |
| RISK-ACAD-03-02 | L | Xóa `classes` cascade xóa toàn bộ `student_class` liên quan (đã cảnh báo ở `F-ACAD-02` RISK-ACAD-02-01) | Đã document ở spec Classes; không cần mitigation thêm ở feature này | BE Lead |

---

# PART C — Design

> **Owner:** Lead · **Gate:** G6

## C.1 User Roles & Permissions

| Role | Permission ID (catalog) | Scope |
|---|---|---|
| `Admin` | `ACAD_ENROLLMENT_MANAGE` | ghi danh/hủy ghi danh |
| `Admin` | `ACAD_ENROLLMENT_VIEW` | xem danh sách học sinh trong lớp |

## C.2 Input Specification

| Input | Required? | Validation | Source |
|---|---|---|---|
| `class_id` | ✓ | UUID, phải tồn tại trong `classes` | Path param |
| `student_id` | ✓ | UUID, phải là user role `Student` + status `Active` | Request body |
| `student_code` | ✗ | string, unique nếu cung cấp | Request body |

## C.3 Output Specification

| Success | Error |
|---|---|
| 201 `EnrollmentOut {student_id, class_id, student_code, enrolled_at}` | `ERR-ACAD-CLASS_NOT_FOUND` (404), `ERR-ACAD-STUDENT_NOT_FOUND` (404), `ERR-ACAD-INVALID_STUDENT_ROLE` (400), `ERR-ACAD-ALREADY_ENROLLED` (409), `ERR-ACAD-DUPLICATE_STUDENT_CODE` (409), `ERR-ACAD-ENROLLMENT_NOT_FOUND` (404), `ERR-AUTH-FORBIDDEN` (403) |

## C.4 Main Flow (End-to-End)

```
Step 1: Admin gửi POST /api/v1/classes/{class_id}/students {student_id, student_code?}
Step 2: require_perm("ACAD_ENROLLMENT_MANAGE") xác thực quyền
Step 3: EnrollmentService validate class_id tồn tại
Step 4: EnrollmentService validate student_id là user role Student, status Active
Step 5: EnrollmentService kiểm tra (student_id, class_id) chưa ghi danh
Step 6: EnrollmentService kiểm tra student_code (nếu có) chưa dùng
Step 7: Insert bản ghi mới, log EVT-ACAD-STUDENT_ENROLLED
Step 8: Trả về 201 EnrollmentOut
```

## C.5 API Contract

| Method | Path | Request shape | Response shape | OpenAPI ref |
|---|---|---|---|---|
| POST | `/api/v1/classes/{class_id}/students` | `{student_id, student_code?}` | 201 `EnrollmentOut` | tag `academic-enrollment` |
| GET | `/api/v1/classes/{class_id}/students` | — | 200 `EnrollmentOut[]` | tag `academic-enrollment` |
| DELETE | `/api/v1/classes/{class_id}/students/{student_id}` | — | 204 | tag `academic-enrollment` |

## C.6 State Machine

Không áp dụng (quan hệ ghi danh chỉ có 2 trạng thái ngầm định: tồn tại / không tồn tại, không có state machine tường minh).

## C.7 Business Rules

| BR ID | Rule | Source |
|---|---|---|
| BR-ACAD-03-01 | Một học sinh chỉ ghi danh 1 lần vào cùng 1 lớp | `docs/base_sql_erd.sql` `student_class` composite PK |
| BR-ACAD-03-02 | `student_code` (nếu cung cấp) phải unique toàn hệ thống | `docs/base_sql_erd.sql` `student_class.student_code UNIQUE` |
| BR-ACAD-03-03 | Chỉ user role `Student` + status `Active` mới được ghi danh | AS-03 `sprint_1_overview.md` |

## C.8 Edge Cases

| EC ID | Scenario | Expected | Test ref |
|---|---|---|---|
| EC-01 | Ghi danh học sinh vào `class_id` không tồn tại | 404 `ERR-ACAD-CLASS_NOT_FOUND` | `EnrollmentIntegrationTest.test_EC01` |
| EC-02 | Ghi danh `student_id` không tồn tại | 404 `ERR-ACAD-STUDENT_NOT_FOUND` | `EnrollmentIntegrationTest.test_EC02` |
| EC-03 | Ghi danh `student_id` là role Teacher | 400 `ERR-ACAD-INVALID_STUDENT_ROLE` | `EnrollmentIntegrationTest.test_EC03` |
| EC-04 | Ghi danh `student_id` role Student nhưng status Blocked | 400 `ERR-ACAD-INVALID_STUDENT_ROLE` | `EnrollmentIntegrationTest.test_EC04` |
| EC-05 | Ghi danh học sinh đã ghi danh lớp này rồi | 409 `ERR-ACAD-ALREADY_ENROLLED` | `EnrollmentIntegrationTest.test_EC05` |
| EC-06 | Ghi danh với `student_code` đã dùng bởi HS khác | 409 `ERR-ACAD-DUPLICATE_STUDENT_CODE` | `EnrollmentIntegrationTest.test_EC06` |
| EC-07 | Hủy ghi danh học sinh chưa từng ghi danh lớp | 404 `ERR-ACAD-ENROLLMENT_NOT_FOUND` | `EnrollmentIntegrationTest.test_EC07` |
| EC-08 | User role Teacher gọi `POST .../students` | 403 `ERR-AUTH-FORBIDDEN` | `EnrollmentIntegrationTest.test_EC08` |

## C.9 UI States

Không áp dụng ở Sprint 1 (chưa có frontend trong scope repo hiện tại).

## C.10 Test Strategy

| Layer | Approach | Framework |
|---|---|---|
| Unit | Mock `EnrollmentRepository` + `ClassRepository` + user lookup, test `EnrollmentService` (duplicate, role validation) | `pytest` + `pytest-mock` |
| Integration | `TestClient` + SQLite in-memory (`tests/conftest.py`), dùng sẵn `student@test.com`/`teacher@test.com` fixtures + 1 class fixture mới | `pytest` |

Coverage target: ≥ 80% unit cho `enrollment_service.py`.

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
| 1 | `docs/v_1/specs/f_acad_03_enrollment_spec.md` (file này) | spec full |
| 2 | `docs/v_1/specs/f_acad_02_classes_spec.md` | Classes phải tồn tại trước, tái dùng `ClassRepository` |
| 3 | `app/modules/auth/` | pattern router/service/repository/schemas |
| 4 | `models/models.py` (class `StudentClass`, `User`) | column spec đã định nghĩa sẵn, composite PK |
| 5 | `app/modules/auth/dependencies.py` | tái dùng `require_perm`, `get_current_user` |
| 6 | `app/scripts/seed.py` | pattern seed permission idempotent |

## D.4 Output Files (Union)

| File | Action | Slice | Note |
|---|---|---|---|
| `app/modules/academic/models.py` | modify | S01 | thêm re-export `StudentClass` |
| `app/modules/academic/schemas.py` | modify | S01 | thêm `EnrollmentCreate`, `EnrollmentOut` |
| `app/modules/academic/repository.py` | modify | S02 | thêm `EnrollmentRepository` |
| `app/modules/academic/services/enrollment_service.py` | create | S03 | |
| `app/modules/academic/routers/enrollments.py` | create | S04 | nested route `/classes/{class_id}/students` |
| `app/main.py` | modify | S04 | `include_router` cho enrollments |
| `app/scripts/seed.py` | modify | S05 | thêm `ACAD_ENROLLMENT_MANAGE`/`ACAD_ENROLLMENT_VIEW` |
| `tests/conftest.py` | modify | S05 | seed permission mới cho Admin trong test fixture |
| `tests/academic/integration/test_enrollments.py` | create | S06 | |
| `tests/academic/unit/test_enrollment_service.py` | create | S06 | |

## D.5 Forbidden Files

| Path | Lý do |
|---|---|
| `app/modules/auth/**` | cross-module ban — chỉ được SELECT `User` qua model import |
| `alembic/versions/d00f10e379e6_init_sprint_0_tables.py` | baseline immutable |
| `docs/base_sql_erd.sql` | freeze sau G4, không sửa schema |

## D.6 Constraints (Cross-cutting)

1. Mọi endpoint ghi (`POST`/`DELETE`) MUST bọc `Depends(require_perm("ACAD_ENROLLMENT_MANAGE"))`; endpoint đọc dùng `ACAD_ENROLLMENT_VIEW`.
2. Validate thứ tự: `class_id` tồn tại → `student_id` hợp lệ (role+status) → check trùng ghi danh → check `student_code` trùng.
3. Mọi ERR raise dùng ID đúng danh mục §E.1.
4. Pydantic schema cho request/response, không expose SQLAlchemy model trực tiếp.
5. File header theo `.claude/rules/coding_rules.md`.

## D.7 Test Commands (feature-level)

```bash
pytest tests/academic -k enrollment
pytest tests -q   # đảm bảo không phá Sprint 0, F-ACAD-01, F-ACAD-02
```

## D.8 Stop Conditions (AI ask-back triggers — cấp feature)

| # | Trigger | Hành động |
|---|---|---|
| F1 | Cần touch bảng ngoài `student_class`/`classes`/`users` (read-only) | STOP, escalate Architect |
| F2 | Cần catalog ID mới ngoài danh sách §E.1 | STOP, bổ sung §E.1 cùng PR |
| F3 | Phát hiện BR/EC mới chưa có ở §C.7/§C.8 | STOP, update spec cùng PR |

---

# PART E — Tracking & Sign-off

> **Owner:** PM

## E.1 Catalog Dependencies

| Catalog | IDs used |
|---|---|
| Error codes | `ERR-ACAD-STUDENT_NOT_FOUND`, `ERR-ACAD-INVALID_STUDENT_ROLE`, `ERR-ACAD-ALREADY_ENROLLED`, `ERR-ACAD-DUPLICATE_STUDENT_CODE`, `ERR-ACAD-ENROLLMENT_NOT_FOUND` |
| Permissions | `ACAD_ENROLLMENT_MANAGE`, `ACAD_ENROLLMENT_VIEW` |
| Events | `EVT-ACAD-STUDENT_ENROLLED`, `EVT-ACAD-STUDENT_UNENROLLED` |

## E.2 Task Breakdown

| Slice | Task ID | Type | Size | SP | Depends on | Owner | PR | Status |
|---|---|---|---|---|---|---|---|---|
| S01 | `F-ACAD-03-TASK-001` | SCHEMA | S | 1 | `F-ACAD-02` approved | BE | — | draft |
| S02 | `F-ACAD-03-TASK-002` | REPO | S | 1 | S01 | BE | — | draft |
| S03 | `F-ACAD-03-TASK-003` | SERVICE | M | 2 | S02 | BE | — | draft |
| S04 | `F-ACAD-03-TASK-004` | API | S | 1 | S03 | BE | — | draft |
| S05 | `F-ACAD-03-TASK-005` | SEED | S | 1 | S04 | BE | — | draft |
| S06 | `F-ACAD-03-TASK-006` | TEST | S | 2 | S05 | BE | — | draft |

## E.3 AI Session Plan Overview

| Slice | AI tier | Task file | AI session # |
|---|---|---|---|
| S01–S06 | T1 | (gộp 1 PR do scope nhỏ) | 3 |

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
