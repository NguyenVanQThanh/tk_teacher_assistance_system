# Feature Spec — `F-ACAD-01` Subjects (CRUD môn học)

> Path: `docs/v_1/specs/f_acad_01_subjects_spec.md` · Sprint: [sprint_1_overview.md](../sprints/sprint_1_overview.md)

---

## Document Header

| Field | Giá trị |
|---|---|
| Feature ID | `F-ACAD-01` |
| Feature name | Subjects — CRUD môn học |
| Module(s) | `academic` |
| Sprint(s) allocated | `SPRINT-01` |
| Lane | `standard` |
| Spec version | `v1.0` |
| Last updated | `2026-07-18` |
| Source binding | SOP §12 · `docs/base_sql_erd.sql` v1.0 (bảng `subjects`) · `f_auth_01_spec.md` (RBAC, current-user) · `.claude/rules/coding_rules.md` |

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

Cho phép **Admin** quản lý danh mục môn học (`subjects`) — nền tảng để gán lớp/giáo viên/bài tập theo môn ở các feature sau (`F-ACAD-02` Classes, `F-ACAD-04` Teacher Assignment, và S2 Bài tập lõi). Bảng `subjects` đã tồn tại từ baseline migration Sprint 0 (`F-FND-01`) — feature này chỉ xây tầng nghiệp vụ (repository/service/API), không migration mới.

## A.2 User Stories

| Story ID | As (role) | I want (capability) | So that (value) |
|---|---|---|---|
| US-01 | Admin | tạo môn học mới | có danh mục môn học cho hệ thống dùng |
| US-02 | Admin | xem danh sách/chi tiết môn học | biết môn nào đã tồn tại trước khi tạo lớp/phân công |
| US-03 | Admin | sửa tên/mô tả môn học | cập nhật khi thông tin thay đổi |
| US-04 | Admin | xóa môn học không còn dùng | dọn dẹp danh mục |

## A.3 REQ Registry

| REQ ID | Mô tả ngắn | Priority | Status | Linked Story |
|---|---|---|---|---|
| REQ-ACAD-001 | Tạo môn học (`subject_name` unique) | P0 | `approved` | US-01 |
| REQ-ACAD-002 | Liệt kê + xem chi tiết môn học | P0 | `approved` | US-02 |
| REQ-ACAD-003 | Sửa môn học | P1 | `approved` | US-03 |
| REQ-ACAD-004 | Xóa môn học | P1 | `approved` | US-04 |

## A.4 Acceptance Criteria (Feature-level)

| AC ID | REQ | Given | When | Then |
|---|---|---|---|---|
| AC-01 | REQ-ACAD-001 | Admin đã đăng nhập, tên môn chưa tồn tại | `POST /api/v1/subjects` | 201, trả về subject vừa tạo |
| AC-02 | REQ-ACAD-001 | tên môn đã tồn tại | `POST /api/v1/subjects` | 409 `ERR-ACAD-SUBJECT_DUPLICATE_NAME` |
| AC-03 | REQ-ACAD-002 | có N môn học trong DB | `GET /api/v1/subjects` | 200, danh sách N môn |
| AC-04 | REQ-ACAD-002 | `subject_id` không tồn tại | `GET /api/v1/subjects/{id}` | 404 `ERR-ACAD-SUBJECT_NOT_FOUND` |
| AC-05 | REQ-ACAD-003 | môn học tồn tại, đổi tên sang tên chưa dùng | `PUT /api/v1/subjects/{id}` | 200, thông tin cập nhật |
| AC-06 | REQ-ACAD-003 | đổi tên trùng với môn khác | `PUT /api/v1/subjects/{id}` | 409 `ERR-ACAD-SUBJECT_DUPLICATE_NAME` |
| AC-07 | REQ-ACAD-004 | môn học tồn tại | `DELETE /api/v1/subjects/{id}` | 200/204, môn bị xóa |
| AC-08 | REQ-ACAD-001..004 | user không có permission `ACAD_SUBJECT_MANAGE`/`ACAD_SUBJECT_VIEW` | gọi endpoint tương ứng | 403 `ERR-AUTH-FORBIDDEN` |

## A.5 In / Out of Scope

**In scope:**
- CRUD đầy đủ cho `subjects`: create, list, get by id, update, delete.
- Validate `subject_name` unique (case theo DB `UNIQUE` constraint có sẵn).

**Out of scope (defer):**
- Soft-delete / audit trail xóa môn học (dùng hard delete theo constraint DB hiện tại `ON DELETE CASCADE`/`SET NULL` đã định nghĩa ở bảng tham chiếu).
- Import hàng loạt (bulk import) môn học.
- Gán môn học cho khối lớp cụ thể (curriculum mapping) — không có trong SRS.

## A.6 REQ → Task Type Map

| REQ ID | Task type(s) cần | Note |
|---|---|---|
| REQ-ACAD-001/002/003/004 | SCHEMA → REPO → SERVICE → API → TEST | CRUD chuẩn, không cần MIG (bảng đã có) |

## A.7 Feature DoD

| ✓ | Tiêu chí Feature Done |
|---|---|
| ☐ | Tất cả AC §A.4 verified qua test |
| ☐ | `pytest tests/academic -k subject` pass |
| ☐ | Permission `ACAD_SUBJECT_MANAGE`, `ACAD_SUBJECT_VIEW` seed cho role Admin |
| ☐ | Sign-off §E.4 hoàn tất |

---

# PART B — Architecture

> **Owner:** Architect · **Approver:** CTO · **Gate:** G4

## B.1 Executive Summary (architectural)

Feature thuần CRUD trên bảng `subjects` đã tồn tại, tuân theo layering có sẵn của `auth` module (Router → Service → Repository → SQLAlchemy). Không migration mới, không thay đổi cấu trúc bảng. Rủi ro thấp nhất trong Sprint 1 vì không có FK phụ thuộc bảng khác.

## B.2 High-Level Architecture

### B.2.1 Layered diagram

```
Client → FastAPI Router (subjects.py) → SubjectService → SubjectRepository → PostgreSQL (subjects)
                                              │
                                              ▼
                                    require_perm("ACAD_SUBJECT_*") — tái dùng app/modules/auth/dependencies.py
```

### B.2.2 Critical data flow

1. Admin gọi `POST /api/v1/subjects` kèm Bearer token.
2. `require_perm("ACAD_SUBJECT_MANAGE")` xác thực quyền qua `PermissionService` (tái dùng từ `F-AUTH-01`).
3. `SubjectService.create_subject` kiểm tra trùng tên qua `SubjectRepository.get_by_name`.
4. Nếu hợp lệ, insert bản ghi `subjects`, trả về `SubjectOut`.

## B.3 Domain Ownership Matrix

| Table / Resource | Owner module | Readers | Writers (cross-module) |
|---|---|---|---|
| `subjects` | `academic` | `academic` (Classes, Teacher Assignment dùng làm FK reference) | (none) |

## B.4 Core Invariants (Feature-scope)

| ID | Invariant | Scope | Reference |
|---|---|---|---|
| `INV-ACAD-01-01` | `subject_name` luôn unique (enforce ở DB UNIQUE + check ở Service trước insert/update) | feature | `docs/base_sql_erd.sql` dòng `subjects.subject_name` |
| `INV-ACAD-01-02` | Không migration mới trong feature này — bảng `subjects` bất biến về cấu trúc | feature | baseline `d00f10e379e6_init_sprint_0_tables.py` |

## B.5 Architecture Decisions (ADR — Feature-scope)

| ADR ID | Title | Status | Approver | Date | Summary |
|---|---|---|---|---|---|
| `ADR-ACAD-01-001` | Không tạo migration mới, dùng lại bảng `subjects` từ baseline Sprint 0 | `approved` | CTO | 2026-07-18 | Bảng đã đủ cột cần thiết; tránh trùng lặp/migration rủi ro |
| `ADR-ACAD-01-002` | Hard delete (không soft-delete) cho `subjects` | `approved` | CTO | 2026-07-18 | SRS không yêu cầu audit trail; giữ đơn giản Sprint 1 |

## B.6 API Boundary

| Method | Path | Auth | OpenAPI tag |
|---|---|---|---|
| POST | `/api/v1/subjects` | Bearer + `ACAD_SUBJECT_MANAGE` | `academic-subjects` |
| GET | `/api/v1/subjects` | Bearer + `ACAD_SUBJECT_VIEW` | `academic-subjects` |
| GET | `/api/v1/subjects/{subject_id}` | Bearer + `ACAD_SUBJECT_VIEW` | `academic-subjects` |
| PUT | `/api/v1/subjects/{subject_id}` | Bearer + `ACAD_SUBJECT_MANAGE` | `academic-subjects` |
| DELETE | `/api/v1/subjects/{subject_id}` | Bearer + `ACAD_SUBJECT_MANAGE` | `academic-subjects` |

## B.7 Database Boundary

| Table | Op | Table spec file | Migration |
|---|---|---|---|
| `subjects` | SELECT/INSERT/UPDATE/DELETE (không đổi schema) | `docs/base_sql_erd.sql` §2.1 | không có (dùng baseline có sẵn) |

## B.8 Security & Privacy

| Aspect | Decision |
|---|---|
| AuthN | JWT bearer, tái dùng `get_current_user` (`F-AUTH-01`) |
| AuthZ | `Depends(require_perm("ACAD_SUBJECT_MANAGE"))` / `require_perm("ACAD_SUBJECT_VIEW")` |
| PII handling | Không có PII trong `subjects` |
| Audit | Log `EVT-ACAD-SUBJECT_CREATED`/`UPDATED`/`DELETED` qua `logger.info`, theo pattern `auth_service.py` |
| Rate limit | Không cần (không phải endpoint public/brute-force target) |

## B.9 Observability & Operations

| Aspect | Plan |
|---|---|
| Structured log | `logger.info/warning` message dạng `"Domain Event: EVT-ACAD-..."`, theo pattern hiện có trong `auth_service.py` |
| Metrics | Chưa cần (Sprint 1 scope nhỏ) |
| Runbook | Không cần riêng, dùng chung vận hành FastAPI hiện tại |

## B.10 Risk Register

| Risk ID | Severity | Description | Mitigation | Owner |
|---|---|---|---|---|
| RISK-ACAD-01-01 | L | Xóa `subjects` đang được `documents`/`exercises` tham chiếu (`ON DELETE SET NULL`/`CASCADE`) gây mất liên kết dữ liệu ngoài ý muốn | Cảnh báo trong response khi xóa; xem xét chặn xóa nếu còn tham chiếu ở feature sau (không bắt buộc Sprint 1) | BE Lead |

---

# PART C — Design

> **Owner:** Lead · **Gate:** G6

## C.1 User Roles & Permissions

| Role | Permission ID (catalog) | Scope |
|---|---|---|
| `Admin` | `ACAD_SUBJECT_MANAGE` | create/update/delete |
| `Admin` | `ACAD_SUBJECT_VIEW` | list/get |

## C.2 Input Specification

| Input | Required? | Validation | Source |
|---|---|---|---|
| `subject_name` | ✓ | string, max 100, unique | Request body |
| `description` | ✗ | string, free text | Request body |

## C.3 Output Specification

| Success | Error |
|---|---|
| 201 `SubjectOut {subject_id, subject_name, description, created_at, updated_at}` | `ERR-ACAD-SUBJECT_NOT_FOUND` (404), `ERR-ACAD-SUBJECT_DUPLICATE_NAME` (409), `ERR-AUTH-FORBIDDEN` (403) |

## C.4 Main Flow (End-to-End)

```
Step 1: Admin gửi POST /api/v1/subjects {subject_name, description}
Step 2: require_perm("ACAD_SUBJECT_MANAGE") xác thực quyền
Step 3: SubjectService kiểm tra subject_name chưa tồn tại (SubjectRepository.get_by_name)
Step 4: Insert bản ghi mới, log EVT-ACAD-SUBJECT_CREATED
Step 5: Trả về 201 SubjectOut
```

## C.5 API Contract

| Method | Path | Request shape | Response shape | OpenAPI ref |
|---|---|---|---|---|
| POST | `/api/v1/subjects` | `{subject_name, description?}` | 201 `SubjectOut` | tag `academic-subjects` |
| GET | `/api/v1/subjects` | — | 200 `SubjectOut[]` | tag `academic-subjects` |
| GET | `/api/v1/subjects/{subject_id}` | — | 200 `SubjectOut` | tag `academic-subjects` |
| PUT | `/api/v1/subjects/{subject_id}` | `{subject_name?, description?}` | 200 `SubjectOut` | tag `academic-subjects` |
| DELETE | `/api/v1/subjects/{subject_id}` | — | 204 | tag `academic-subjects` |

## C.6 State Machine

Không áp dụng (resource CRUD đơn giản, không có state machine).

## C.7 Business Rules

| BR ID | Rule | Source |
|---|---|---|
| BR-ACAD-01-01 | `subject_name` phải unique trong toàn hệ thống | `docs/base_sql_erd.sql` `subjects.subject_name UNIQUE` |
| BR-ACAD-01-02 | Update `subject_name` cũng phải kiểm tra trùng với môn khác (loại trừ chính nó) | nghiệp vụ |

## C.8 Edge Cases

| EC ID | Scenario | Expected | Test ref |
|---|---|---|---|
| EC-01 | Tạo môn học với tên đã tồn tại | 409 `ERR-ACAD-SUBJECT_DUPLICATE_NAME` | `SubjectIntegrationTest.test_EC01` |
| EC-02 | Xem/sửa/xóa `subject_id` không tồn tại | 404 `ERR-ACAD-SUBJECT_NOT_FOUND` | `SubjectIntegrationTest.test_EC02` |
| EC-03 | User role Student gọi `POST /api/v1/subjects` | 403 `ERR-AUTH-FORBIDDEN` | `SubjectIntegrationTest.test_EC03` |
| EC-04 | Update chỉ đổi `description`, giữ nguyên `subject_name` | 200, không bị false-positive trùng tên với chính nó | `SubjectIntegrationTest.test_EC04` |

## C.9 UI States

Không áp dụng ở Sprint 1 (chưa có frontend trong scope repo hiện tại).

## C.10 Test Strategy

| Layer | Approach | Framework |
|---|---|---|
| Unit | Mock `SubjectRepository`, test `SubjectService` (duplicate check) | `pytest` + `pytest-mock` |
| Integration | `TestClient` + SQLite in-memory (`tests/conftest.py`) | `pytest` |

Coverage target: ≥ 80% unit cho `subject_service.py`.

---

# PART D — Coding context

> **Owner:** BE Lead · **Gate:** G6.5

## D.1 Task Types Inventory

| Slice ID | Task type | Size | SP | Task file | Status |
|---|---|---|---|---|---|
| S01 | SCHEMA | S | 1 | (inline trong PR, không tách task file riêng — Sprint 1 nhỏ gọn) | draft |
| S02 | REPO | S | 1 | ” | draft |
| S03 | SERVICE | S | 1 | ” | draft |
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
| 1 | `docs/v_1/specs/f_acad_01_subjects_spec.md` (file này) | spec full |
| 2 | `app/modules/auth/` | golden pattern (router/service/repository/schemas) |
| 3 | `models/models.py` (class `Subject`) | column spec đã định nghĩa sẵn |
| 4 | `app/modules/auth/dependencies.py` | tái dùng `require_perm`, `get_current_user` |
| 5 | `app/scripts/seed.py` | pattern seed permission idempotent |

## D.4 Output Files (Union)

| File | Action | Slice | Note |
|---|---|---|---|
| `app/modules/academic/models.py` | create | S01 | re-export `Subject` từ `models.models` |
| `app/modules/academic/schemas.py` | create | S01 | `SubjectCreate`, `SubjectUpdate`, `SubjectOut` |
| `app/modules/academic/repository.py` | create | S02 | `SubjectRepository` |
| `app/modules/academic/services/subject_service.py` | create | S03 | |
| `app/modules/academic/routers/subjects.py` | create | S04 | |
| `app/main.py` | modify | S04 | `include_router` cho subjects |
| `app/scripts/seed.py` | modify | S05 | thêm `ACAD_SUBJECT_MANAGE`/`ACAD_SUBJECT_VIEW` |
| `tests/conftest.py` | modify | S05 | seed permission mới cho Admin trong test fixture |
| `tests/academic/integration/test_subjects.py` | create | S06 | |
| `tests/academic/unit/test_subject_service.py` | create | S06 | |

## D.5 Forbidden Files

| Path | Lý do |
|---|---|
| `app/modules/auth/**` | cross-module ban (INV-5 kiểu Sprint 0) |
| `alembic/versions/d00f10e379e6_init_sprint_0_tables.py` | baseline immutable |
| `docs/base_sql_erd.sql` | freeze sau G4, không sửa schema |

## D.6 Constraints (Cross-cutting)

1. Mọi endpoint ghi (`POST`/`PUT`/`DELETE`) MUST bọc `Depends(require_perm("ACAD_SUBJECT_MANAGE"))`; endpoint đọc dùng `ACAD_SUBJECT_VIEW`.
2. Không log/lộ thông tin nhạy cảm (không áp dụng ở `subjects` vì không có PII, nhưng giữ pattern chung).
3. Mọi ERR raise dùng ID đúng danh mục §E.1.
4. Pydantic schema cho request/response, không expose SQLAlchemy model trực tiếp.
5. File header theo `.claude/rules/coding_rules.md`.

## D.7 Test Commands (feature-level)

```bash
pytest tests/academic -k subject
pytest tests -q   # đảm bảo không phá Sprint 0
```

## D.8 Stop Conditions (AI ask-back triggers — cấp feature)

| # | Trigger | Hành động |
|---|---|---|
| F1 | Cần touch bảng ngoài `subjects` | STOP, escalate Architect |
| F2 | Cần catalog ID mới ngoài danh sách §E.1 | STOP, bổ sung §E.1 cùng PR |
| F3 | Phát hiện BR/EC mới chưa có ở §C.7/§C.8 | STOP, update spec cùng PR |

---

# PART E — Tracking & Sign-off

> **Owner:** PM

## E.1 Catalog Dependencies

| Catalog | IDs used |
|---|---|
| Error codes | `ERR-ACAD-SUBJECT_NOT_FOUND`, `ERR-ACAD-SUBJECT_DUPLICATE_NAME` |
| Permissions | `ACAD_SUBJECT_MANAGE`, `ACAD_SUBJECT_VIEW` |
| Events | `EVT-ACAD-SUBJECT_CREATED`, `EVT-ACAD-SUBJECT_UPDATED`, `EVT-ACAD-SUBJECT_DELETED` |

## E.2 Task Breakdown

| Slice | Task ID | Type | Size | SP | Depends on | Owner | PR | Status |
|---|---|---|---|---|---|---|---|---|
| S01 | `F-ACAD-01-TASK-001` | SCHEMA | S | 1 | — | BE | — | draft |
| S02 | `F-ACAD-01-TASK-002` | REPO | S | 1 | S01 | BE | — | draft |
| S03 | `F-ACAD-01-TASK-003` | SERVICE | S | 1 | S02 | BE | — | draft |
| S04 | `F-ACAD-01-TASK-004` | API | S | 1 | S03 | BE | — | draft |
| S05 | `F-ACAD-01-TASK-005` | SEED | S | 1 | S04 | BE | — | draft |
| S06 | `F-ACAD-01-TASK-006` | TEST | S | 2 | S05 | BE | — | draft |

## E.3 AI Session Plan Overview

| Slice | AI tier | Task file | AI session # |
|---|---|---|---|
| S01–S06 | T1 | (gộp 1 PR do scope nhỏ) | 1 |

## E.4 Sign-off Matrix

| PART | Gate | Owner | Approver | Status | Người ACK | Ngày |
|---|---|---|---|---|---|---|
| A Business | G3 | BA/PM | Lead | `approved` | | 2026-07-18 |
| B Architecture | G4 | Architect | CTO | `approved` | | 2026-07-18 |
| C Design | G6 | Lead | Lead | `approved` | | 2026-07-18 |
| D Coding | G6.5 | BE Lead | BE Lead | `approved` | | 2026-07-18 |
| E Tracking | G7+ | PM | PM | `approved` | | 2026-07-18 |

**Update rule:** task chỉ start khi PART A→D đều `approved`.

## E.5 PR Evidence Index

| PR # | Slice | Task ID | Merged date | Notes |
|---|---|---|---|---|
| | | | | (chưa code — spec-only tại thời điểm này) |

---

## Changelog

| Date | Version | Change | Author |
|---|---|---|---|
| 2026-07-18 | v1.0 | Initial spec — breakdown từ `sprint_1_overview.md` | AI Agent |
