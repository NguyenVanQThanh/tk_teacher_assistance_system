# Feature Spec — `F-FND-01` Foundation & DB Baseline

> Path: `docs/v_1/specs/f_fnd_01_spec.md` ·

---

## Document Header

| Field | Giá trị |
|---|---|
| Feature ID | `F-FND-01` |
| Feature name | Foundation & DB Baseline |
| Module(s) | `foundation` + `auth` (consumer) |
| Sprint(s) allocated | `SPRINT-00` |
| Lane | `standard` |
| Spec version | `v1.0` |
| Last updated | `2026-06-26` |
| Source binding | SOP §12 (Unified Feature Spec) · `docs/base_sql_erd.sql` v1.0 · `.claude/rules/v2-coding-standard.md` |

### Gate status (cập nhật khi PART approved)

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

> **Owner:** BA/PM · **Gate:** G3 · **Audience:** PM, Lead, stakeholder

## A.1 Feature Summary

Feature **enabler**: dựng khung dự án FastAPI và cơ sở dữ liệu nền để mọi feature nghiệp vụ chạy được. Bao gồm: cấu hình app + settings, kết nối PostgreSQL qua SQLAlchemy + Alembic, **migration baseline** tạo `roles` và `users`, **seed** 3 vai trò + 1 tài khoản admin bootstrap, error envelope chuẩn + correlation id, structured logging, health/readiness endpoint, và JWT util dùng chung cho module `auth`. Người dùng trực tiếp: đội phát triển & vận hành.

## A.2 User Stories

| Story ID | As (role) | I want (capability) | So that (value) |
|---|---|---|---|
| US-01 | Developer | một khung dự án + DB session + Alembic chạy được | tôi build feature mới không phải dựng lại hạ tầng |
| US-02 | DevOps | endpoint health/readiness | tôi cấu hình được liveness/readiness probe khi deploy |
| US-03 | System Admin | migration tạo `roles`/`users` + seed admin bootstrap | có tài khoản đầu tiên để đăng nhập và quản trị |
| US-04 | API consumer | mọi lỗi trả về theo một cấu trúc thống nhất kèm `correlation_id` | client xử lý lỗi nhất quán và trace được sự cố |

## A.3 REQ Registry

| REQ ID | Mô tả ngắn | Priority | Status | Linked Story |
|---|---|---|---|---|
| REQ-FND-001 | App skeleton + settings (.env) + DB session (SQLAlchemy) | P0 | `draft` | US-01 |
| REQ-FND-002 | Alembic baseline migration: tạo `roles` + `users` | P0 | `draft` | US-03 |
| REQ-FND-003 | Seed 3 role + 1 admin bootstrap (idempotent) | P0 | `draft` | US-03 |
| REQ-FND-004 | Error envelope chuẩn + global exception handler + `correlation_id` | P0 | `draft` | US-04 |
| REQ-FND-005 | Health `/health` + readiness `/health/ready` (DB ping) | P1 | `draft` | US-02 |
| REQ-FND-006 | JWT util + password hashing util (dùng chung cho `auth`) | P0 | `draft` | US-01 |
| REQ-FND-007 | Structured logging (structlog JSON) + request middleware | P1 | `draft` | US-04 |

## A.4 Acceptance Criteria (Feature-level)

| AC ID | REQ | Given | When | Then |
|---|---|---|---|---|
| AC-01 | REQ-FND-002 | DB rỗng | chạy `alembic upgrade head` | có bảng `roles`, `users` đúng cột theo ERD v1.0 |
| AC-02 | REQ-FND-003 | migration đã chạy | chạy seed | có role_id 1/2/3 (Admin/HocSinh/GiaoVien) + 1 user role Admin; chạy lại không tạo trùng |
| AC-03 | REQ-FND-005 | app đang chạy, DB up | `GET /health/ready` | 200 `{status:"ready"}` |
| AC-04 | REQ-FND-005 | app đang chạy, DB **down** | `GET /health/ready` | 503 `{status:"not_ready"}` |
| AC-05 | REQ-FND-004 | một endpoint raise domain error | client gọi | response theo envelope `{error:{code,message,correlation_id}}`, HTTP status đúng |
| AC-06 | REQ-FND-006 | password plaintext | hash rồi verify | `verify_password` trả True; hash dùng bcrypt, không lưu plaintext |

## A.5 In / Out of Scope

**In scope:**
- App skeleton, settings, DB session/engine, Alembic init + baseline migration (`roles`, `users`).
- Seed roles + admin bootstrap; error envelope; health/readiness; JWT & password util; structured logging.

**Out of scope (defer/feature khác):**
- Login/RBAC endpoint thực tế → `F-AUTH-01`.
- Các bảng nghiệp vụ khác (`subjects`, `classes`, `exercises`, …) → sprint sau.
- Cột `users.last_login_at`, trigger `updated_at`, sync `total_questions` → schema v1.2 (làm khi vào module cần).
- CI/CD pipeline cloud, container orchestration.

## A.6 REQ → Task Type Map

| REQ ID | Task type(s) cần | Note |
|---|---|---|
| REQ-FND-001 | SETUP → CONFIG | scaffold + settings + DB session |
| REQ-FND-002 | MIG | Alembic baseline |
| REQ-FND-003 | MIG (data) / SCRIPT | seed idempotent |
| REQ-FND-004 | MIDDLEWARE → TEST | exception handler |
| REQ-FND-005 | API → TEST | health router |
| REQ-FND-006 | UTIL → TEST | jwt + hashing |
| REQ-FND-007 | MIDDLEWARE | logging |

## A.7 Feature DoD

| ✓ | Tiêu chí Feature Done |
|---|---|
| ☐ | Tất cả AC §A.4 verified qua test |
| ☐ | `alembic upgrade head` + seed chạy sạch trên DB mới |
| ☐ | `ruff check . && mypy app && pytest --cov=app` pass |
| ☐ | Health/readiness verify trên staging |
| ☐ | Catalog ERR/EVT khởi tạo (`ERR-CORE-*`) |
| ☐ | Sign-off §E.4 hoàn tất |

---

# PART B — Architecture

> **Owner:** Architect · **Approver:** CTO · **Gate:** G4

## B.1 Executive Summary (architectural)

Dựng monolith modular bằng FastAPI: mỗi nghiệp vụ là một package dưới `app/modules/`. Foundation cung cấp lớp dùng chung (`app/core/`): settings, DB session, error envelope, logging, security util. Persistence dùng SQLAlchemy 2.0 + Alembic; PostgreSQL là store duy nhất. Quyết định chính: **chuẩn hóa error envelope + correlation id ngay từ đầu** để mọi feature kế thừa. Rủi ro lớn nhất: baseline migration sai khiến mọi sprint sau lệch — phải khớp 100% với `base_sql_erd.sql` v1.0.

## B.2 High-Level Architecture

### B.2.1 Layered diagram

```
Client → FastAPI Router → Service → Repository → PostgreSQL (SQLAlchemy)
                             │
                             ▼
                     app/core (settings · session · errors · logging · security)
```

### B.2.2 Critical data flow

1. App startup → đọc `Settings` (.env) → tạo SQLAlchemy engine + sessionmaker.
2. `alembic upgrade head` (deploy step) → tạo `roles`, `users`.
3. Seed script → INSERT 3 role + admin bootstrap (ON CONFLICT DO NOTHING).
4. Request đến → middleware gắn `correlation_id` → router → service → repo (DB session per-request).
5. Exception → global handler → map sang error envelope + HTTP status.

## B.3 Domain Ownership Matrix

| Table / Resource | Owner module | Readers | Writers (cross-module) |
|---|---|---|---|
| `roles` | `foundation` | `auth`, mọi module | (none — seed only) |
| `users` | `foundation` | `auth`, `iam` | `auth` (qua service, không sửa schema) |

## B.4 Core Invariants (Feature-scope)

| ID | Invariant | Scope | Reference |
|---|---|---|---|
| `INV-FND-01` | Baseline migration phải khớp tuyệt đối với `base_sql_erd.sql` v1.0 (bảng `roles`, `users`) | feature | `docs/base_sql_erd.sql` |
| `INV-FND-02` | Password chỉ lưu dạng hash (bcrypt); cấm lưu/log plaintext | global | V2 §13.4 |
| `INV-FND-03` | Một DB session per-request, đóng sau response | global | SQLAlchemy session scope |
| `INV-FND-04` | Mọi response lỗi tuân theo error envelope chuẩn | global | §C.3 |

## B.5 Architecture Decisions (ADR — Feature-scope)

| ADR ID | Title | Status | Approver | Date | Summary |
|---|---|---|---|---|---|
| `ADR-FND-001` | Monolith modular theo `app/modules/{module}` | `approved` | CTO | 2026-06-26 | Đơn giản hóa Sprint sớm; tách microservice sau nếu cần |
| `ADR-FND-002` | Alembic làm công cụ migration (thay vì chạy raw SQL) | `approved` | CTO | 2026-06-26 | Versioning + rollback; `base_sql_erd.sql` là ERD tham chiếu |
| `ADR-FND-003` | JWT stateless, access-only ở Sprint 0 | `proposed` | CTO | 2026-06-26 | Refresh token + blocklist defer |

## B.6 API Boundary

| Method | Path | Auth | OpenAPI tag |
|---|---|---|---|
| GET | `/health` | none | `health` |
| GET | `/health/ready` | none | `health` |

## B.7 Database Boundary

| Table | Op | Table spec file | Migration |
|---|---|---|---|
| `roles` | CREATE | `database/tables/roles.md` | `alembic/versions/{baseline}_create_roles_users.py` (risk low) |
| `users` | CREATE | `database/tables/users.md` | `alembic/versions/{baseline}_create_roles_users.py` (risk low) |

## B.8 Security & Privacy

| Aspect | Decision |
|---|---|
| AuthN | JWT bearer (`python-jose`), password hash `bcrypt`/`passlib` (V2 §12.1) |
| AuthZ | (định nghĩa dependency ở `F-AUTH-01`) |
| PII handling | Email/phone masked trong log (V2 §13.4) |
| Audit | Event prefix `CORE_*` / `AUTH_*` (xem `catalogs/events.md`) |
| Secrets | `SECRET_KEY`, `DATABASE_URL`, admin bootstrap creds từ `.env` — không hardcode |
| Threat model | STRIDE — risk §B.10 |

## B.9 Observability & Operations

| Aspect | Plan |
|---|---|
| Structured log | JSON via `structlog`, contextvar `correlation_id` (V2 §13.1) |
| Metrics | `prometheus-fastapi-instrumentator` (V2 §13.6) |
| Health | `/health` (liveness), `/health/ready` (DB ping) |
| Runbook | `docs/v_1/runbooks/f_fnd_01.md` (TBD) |

## B.10 Risk Register

| Risk ID | Severity | Description | Mitigation | Owner |
|---|---|---|---|---|
| RISK-01 | H | Baseline migration lệch ERD → mọi sprint sau sai | Test so khớp schema với `base_sql_erd.sql`; review G4 | Architect |
| RISK-02 | M | Admin bootstrap dùng mật khẩu mặc định yếu | Bắt buộc đặt qua `.env`; cảnh báo nếu thiếu | BE Lead |
| RISK-03 | L | Session leak không đóng | Dependency `get_db` dùng `yield` + finally close | BE |

---

# PART C — Design

> **Owner:** Lead · **Gate:** G6

## C.1 User Roles & Permissions

| Role | Permission ID (catalog) | Scope |
|---|---|---|
| (n/a) | — | Foundation không expose endpoint nghiệp vụ; health là public |

## C.2 Input Specification

| Input | Required? | Validation | Source |
|---|---|---|---|
| `DATABASE_URL` | ✓ | DSN PostgreSQL hợp lệ | `.env` |
| `SECRET_KEY` | ✓ | chuỗi ≥ 32 ký tự | `.env` |
| `ADMIN_BOOTSTRAP_EMAIL` / `ADMIN_BOOTSTRAP_PASSWORD` | ✓ | email hợp lệ / password ≥ 8 | `.env` (seed) |

## C.3 Output Specification

**Error envelope chuẩn** (mọi feature dùng chung):

```json
{
  "error": {
    "code": "ERR-CORE-INTERNAL",
    "message": "Human-readable message",
    "correlation_id": "uuid",
    "details": []
  }
}
```

| Success | Error |
|---|---|
| Health: 200 `{status, version}` | Envelope trên + HTTP status map theo ERR catalog |

## C.4 Main Flow (End-to-End) — bootstrap

```
Step 1: Ops set .env (DATABASE_URL, SECRET_KEY, ADMIN_BOOTSTRAP_*)
Step 2: alembic upgrade head  → tạo roles, users
Step 3: python -m app.scripts.seed  → INSERT roles (1,2,3) + admin (ON CONFLICT DO NOTHING)
Step 4: uvicorn app.main:app  → app up
Step 5: GET /health/ready → 200 ready
```

## C.5 API Contract

| Method | Path | Request shape | Response shape | OpenAPI ref |
|---|---|---|---|---|
| GET | `/health` | — | 200 `{status:"ok", version}` | FastAPI auto `/openapi.json` tag `health` |
| GET | `/health/ready` | — | 200 `{status:"ready"}` / 503 `{status:"not_ready"}` | tag `health` |

## C.6 State Machine

| Current state | Action | Next state | Error |
|---|---|---|---|
| `DB_EMPTY` | `alembic upgrade head` | `SCHEMA_READY` | migration fail → stay |
| `SCHEMA_READY` | seed | `SEEDED` | conflict → no-op (idempotent) |

## C.7 Business Rules

| BR ID | Rule | Source |
|---|---|---|
| BR-01 | Seed roles cố định: 1=Admin, 2=HocSinh, 3=GiaoVien | ERD v1.0 |
| BR-02 | Admin bootstrap chỉ tạo nếu chưa tồn tại email đó | idempotent |
| BR-03 | Password admin bootstrap hash bcrypt trước khi INSERT | INV-FND-02 |

## C.8 Edge Cases

| EC ID | Scenario | Expected | Test ref |
|---|---|---|---|
| EC-01 | `.env` thiếu `DATABASE_URL` | app fail-fast khi startup với message rõ ràng | `test_settings.py::test_EC01` |
| EC-02 | DB down lúc `/health/ready` | 503 `not_ready` | `test_health.py::test_EC02` |
| EC-03 | Chạy seed 2 lần | lần 2 không tạo trùng, exit 0 | `test_seed.py::test_EC03` |
| EC-04 | Unhandled exception trong handler | trả `ERR-CORE-INTERNAL` 500 + correlation_id, không lộ stacktrace | `test_errors.py::test_EC04` |

## C.9 UI States

(n/a — feature backend/infrastructure, không có UI.)

## C.10 Test Strategy

| Layer | Approach | Framework |
|---|---|---|
| Unit | settings parsing, hashing, jwt util, error mapping | `pytest` + `pytest-mock` |
| Integration | migration + seed trên DB thật | `pytest` + Testcontainers PostgreSQL |
| E2E | health/readiness qua HTTP | `httpx.AsyncClient` |

Coverage target: ≥ 80% unit (V2 §15.3).

---

# PART D — Coding context

> **Owner:** BE Lead · **Gate:** G6.5 · **Audience:** Dev, AI agent

## D.1 Task Types Inventory

| Slice ID | Task type | Size | SP | Task file | Status |
|---|---|---|---|---|---|
| S01 | SETUP | M | 2 | `tasks/f_fnd_01/f_fnd_01-task_001.md` | done |
| S02 | CONFIG | S | 1 | `tasks/f_fnd_01/f_fnd_01-task_002.md` | done |
| S03 | MIG | S | 1 | `tasks/f_fnd_01/f_fnd_01-task_003.md` | done |
| S04 | MIG (seed) | S | 1 | `tasks/f_fnd_01/f_fnd_01-task_004.md` | done |
| S05 | MIDDLEWARE (errors+logging) | M | 2 | `tasks/f_fnd_01/f_fnd_01-task_005.md` | done |
| S06 | UTIL (jwt+hashing) | S | 1 | `tasks/f_fnd_01/f_fnd_01-task_006.md` | done |
| S07 | API (health) | S | 1 | `tasks/f_fnd_01/f_fnd_01-task_007.md` | done |

## D.2 Source of Truth (anchor map)

| Concept | Section anchor |
|---|---|
| Error envelope | `#c3-output-specification` |
| BR rules | `#c7-business-rules` |
| EC list | `#c8-edge-cases` |
| ADR | `#b5-architecture-decisions-adr--feature-scope` |
| INV | `#b4-core-invariants-feature-scope` |
| ERD reference | `docs/base_sql_erd.sql` |

## D.3 Input Context Pack

| Order | Path | Lý do đọc |
|---|---|---|
| 1 | `docs/v_1/specs/f_fnd_01_spec.md` (file này) | spec full |
| 2 | `docs/base_sql_erd.sql` | cột chuẩn `roles`/`users` |
| 3 | `.claude/rules/v2-coding-standard.md` | coding standard |
| 4 | `docs/v_1/constraints/catalogs/error_codes.md` | ERR ID |

## D.4 Output Files (Union)

| File | Action | Slice | Note |
|---|---|---|---|
| `app/main.py` | create | S01 | app factory + router include |
| `app/core/settings.py` | create | S02 | Pydantic Settings |
| `app/core/db.py` | create | S02 | engine + `get_db` dependency |
| `alembic.ini`, `alembic/env.py` | create | S03 | Alembic init |
| `alembic/versions/{baseline}_create_roles_users.py` | create | S03 | baseline migration |
| `app/scripts/seed.py` | create | S04 | seed roles + admin |
| `app/core/errors.py` | create | S05 | error envelope + handlers |
| `app/core/logging.py`, `app/core/middleware.py` | create | S05 | structlog + correlation id |
| `app/core/security.py` | create | S06 | jwt + passlib util |
| `app/modules/foundation/routers/health.py` | create | S07 | health endpoints |
| `app/modules/foundation/models.py` | create | S03 | SQLAlchemy `Role`, `User` |

## D.5 Forbidden Files

| Path | Lý do |
|---|---|
| `alembic/versions/{baseline}_*.py` (sau khi merged) | foundation baseline immutable |
| `docs/base_sql_erd.sql` | ERD reference, sửa schema phải qua version mới |
| `app/modules/{other}/**` | foundation không chứa logic nghiệp vụ |

## D.6 Constraints (Cross-cutting)

1. Password chỉ lưu hash bcrypt; cấm log raw password/token (INV-FND-02, V2 §13.4).
2. Mọi ERR raise dùng ID từ `constraints/catalogs/error_codes.md`.
3. Pydantic schema cho mọi request/response; SQLAlchemy model không lộ trực tiếp ra API (V2 §7).
4. DB session per-request qua `Depends(get_db)`, đóng ở `finally` (INV-FND-03).
5. Baseline migration khớp tuyệt đối ERD v1.0 (INV-FND-01).
6. Settings đọc từ `.env`, fail-fast nếu thiếu biến bắt buộc.

## D.7 Test Commands (feature-level)

```bash
# Unit
pytest tests/foundation -k "unit"

# Integration (Testcontainers PostgreSQL)
pytest tests/foundation/integration

# Lint + type-check + full gate
ruff check . && mypy app && pytest --cov=app
```

## D.8 Stop Conditions (AI ask-back triggers)

| # | Trigger | Hành động |
|---|---|---|
| F1 | Cần sửa cột `roles`/`users` khác ERD v1.0 | STOP, escalate Architect (đổi schema = version mới) |
| F2 | Cần ERR/EVT ID mới | STOP, add catalog cùng PR |
| F3 | Phát hiện BR/EC mới chưa có ở §C.7/§C.8 | STOP, update PART C cùng PR |

---

# PART E — Tracking & Sign-off

> **Owner:** PM

## E.1 Catalog Dependencies

| Catalog | IDs used |
|---|---|
| `error_codes.md` | `ERR-CORE-INTERNAL`, `ERR-CORE-DB_UNAVAILABLE`, `ERR-CORE-CONFIG_MISSING` |
| `events.md` | `EVT-CORE-APP_STARTED` |

## E.2 Task Breakdown

| Slice | Task ID | Type | Size | SP | Depends on | Owner | PR | Status |
|---|---|---|---|---|---|---|---|---|
| S01 | `F-FND-01-TASK-001` | SETUP | M | 2 | — | BE | | done |
| S02 | `F-FND-01-TASK-002` | CONFIG | S | 1 | S01 | BE | | done |
| S03 | `F-FND-01-TASK-003` | MIG | S | 1 | S02 | BE | | done |
| S04 | `F-FND-01-TASK-004` | MIG(seed) | S | 1 | S03 | BE | | done |
| S05 | `F-FND-01-TASK-005` | MIDDLEWARE | M | 2 | S01 | BE | | done |
| S06 | `F-FND-01-TASK-006` | UTIL | S | 1 | S02 | BE | | done |
| S07 | `F-FND-01-TASK-007` | API | S | 1 | S02,S05 | BE | | done |

## E.3 AI Session Plan Overview

| Slice | AI tier | Task file | AI session # |
|---|---|---|---|
| S01–S07 | T2 | `tasks/f_fnd_01/f_fnd_01-task_00N.md` | 1 mỗi slice |

## E.4 Sign-off Matrix

| PART | Gate | Owner | Approver | Status | Người ACK | Ngày |
|---|---|---|---|---|---|---|
| A Business | G3 | BA/PM | Lead | `draft` | | |
| B Architecture | G4 | Architect | CTO | `draft` | | |
| C Design | G6 | Lead | Lead | `draft` | | |
| D Coding | G6.5 | BE Lead | BE Lead | `draft` | | |
| E Tracking | G7+ | PM | PM | `live` | | |
| Feature Done | G8 | PM | PM + Tech Lead | — | | |

**Update rule:** task chỉ start khi PART A+B+C+D đều `approved`.

## E.5 PR Evidence Index

| PR # | Slice | Task ID | Merged date | Notes |
|---|---|---|---|---|
| | | | | |

---

## Changelog

| Date | Version | Change | Author |
|---|---|---|---|
| 2026-06-26 | v1.0 | Initial spec — Sprint 0 foundation | BA |
