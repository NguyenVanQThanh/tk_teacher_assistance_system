# Feature Spec — `{FEATURE_ID}` `{FEATURE_NAME}`

> Path: `docs/v_1/specs/f_{id}_spec.md` ·


---

## Document Header

| Field | Giá trị |
|---|---|
| Feature ID | `F-XXX-NN` |
| Feature name | |
| Module(s) | `{primary}` + `{liên quan}` |
| Sprint(s) allocated | `SPRINT-NN` …  |
| Lane | `standard` \| `fast-track` \| `hotfix` |
| Spec version | `v1.0` |
| Last updated | `YYYY-MM-DD` |
| Source binding | SOP §12 (Unified Feature Spec) · `.claude/rules/v2-coding-standard.md` |

### Gate status (cập nhật khi PART approved)

| Gate | Bao trùm | Owner | Approver | Status | Date |
|---|---|---|---|---|---|
| G3 Business | PART A | BA/PM | Lead | `draft` \| `review` \| `approved` | |
| G4 Architecture | PART B | Architect | CTO | `draft` \| `review` \| `approved` | |
| G6 Design | PART C | Lead | Lead | `draft` \| `review` \| `approved` | |
| G6.5 Coding | PART D | BE Lead | BE Lead | `draft` \| `review` \| `approved` | |
| G7+ Tracking | PART E | PM | PM | `draft` \| live | |

### Table of contents

- [PART A — Business](#part-a--business) (8 mục)
- [PART B — Architecture](#part-b--architecture) (10 mục)
- [PART C — Design](#part-c--design) (10 mục)
- [PART D — Coding context](#part-d--coding-context) (8 mục)
- [PART E — Tracking & Sign-off](#part-e--tracking--sign-off) (5 mục)

---

# PART A — Business

> **Owner:** BA/PM · **Gate:** G3 · **Audience:** PM, Lead, stakeholder

## A.1 Feature Summary

2–3 câu mô tả: feature làm gì, ai dùng, giá trị mang lại. Link `functional_overview.md` Feature Registry row nếu có.

## A.2 User Stories

| Story ID | As (role) | I want (capability) | So that (value) |
|---|---|---|---|
| US-01 | | | |
| US-02 | | | |

## A.3 REQ Registry

| REQ ID | Mô tả ngắn | Priority | Status | Linked Story |
|---|---|---|---|---|
| REQ-001 | | P0/P1/P2 | `draft`/`approved` | US-01 |

## A.4 Acceptance Criteria (Feature-level)

> Given/When/Then đầy đủ per REQ. Union AC này = AC của tất cả task con (CODD-style coverage).

| AC ID | REQ | Given | When | Then |
|---|---|---|---|---|
| AC-01 | REQ-001 | | | |

## A.5 In / Out of Scope

**In scope:**
-

**Out of scope (defer hoặc feature khác):**
-

## A.6 REQ → Task Type Map

| REQ ID | Task type(s) cần | Note |
|---|---|---|
| REQ-001 | MIG → MODEL → REPO → SERVICE → API → TEST | full stack |

## A.7 Feature DoD

| ✓ | Tiêu chí Feature Done |
|---|---|
| ☐ | Tất cả AC §A.4 verified qua test |
| ☐ | Tất cả task con merged (PART E.1) |
| ☐ | Smoke test pass trên staging |
| ☐ | OpenAPI updated nếu API change |
| ☐ | Catalog ERR/PERM/EVT updated nếu cần |
| ☐ | Feature complete review file sinh (`feature_complete_review_prompt.md`) |
| ☐ | Sign-off §E.4 hoàn tất |

---

# PART B — Architecture

> **Owner:** Architect · **Approver:** CTO · **Gate:** G4 · **Audience:** Architect, BE Lead, CTO

## B.1 Executive Summary (architectural)

3–5 câu: outcome architecture · scope · key decision · biggest risk.

## B.2 High-Level Architecture

### B.2.1 Layered diagram (ASCII / mermaid)

```
Client → FastAPI Router → Service → Repository → PostgreSQL (SQLAlchemy)
                             │
                             ▼
                         Outbox → Event Relay → Consumers
```

### B.2.2 Critical data flow

Mô tả luồng data quan trọng nhất của feature (≤ 5 step, có actor + module + table).

## B.3 Domain Ownership Matrix

| Table / Resource | Owner module | Readers | Writers (cross-module) |
|---|---|---|---|
| `users` | `auth` | `iam`, `crm` | (none — INV-5) |
| `phone_otps` | `auth` | — | — |

## B.4 Core Invariants (Feature-scope)

| ID | Invariant | Scope | Reference |
|---|---|---|---|
| `INV-{MODULE}-{FF}-01` | | feature | `constraints/invariants_global.md` (nếu link) |

## B.5 Architecture Decisions (ADR — Feature-scope)

| ADR ID | Title | Status | Approver | Date | Summary |
|---|---|---|---|---|---|
| `ADR-{MODULE}-{FF}-001` | | `proposed`/`approved`/`superseded` | CTO | | |

## B.6 API Boundary

Liệt kê endpoint feature expose (path · method · auth · OpenAPI tag). Chi tiết contract ở §C.5.

| Method | Path | Auth | OpenAPI tag |
|---|---|---|---|
| POST | `/api/v1/...` | Bearer | `auth` |

## B.7 Database Boundary

Tables/columns feature touch (link table spec). Migration count + risk.

| Table | Op | Table spec file | Migration |
|---|---|---|---|
| `phone_otps` | CREATE | `database/tables/phone_otps.md` | `alembic/versions/{rev}_create_phone_otps.py` (risk low) |
| `users` | ALTER (add column) | `database/tables/users.md` | `alembic/versions/{rev}_add_last_login_at.py` (risk low) |

## B.8 Security & Privacy

| Aspect | Decision |
|---|---|
| AuthN | JWT bearer (`python-jose`), password hash `bcrypt`/`passlib` (V2 §12.1) |
| AuthZ | FastAPI `Depends(require_perm(...))` PERM IDs (xem §C.1) |
| PII handling | Phone masked log/response (V2 §13.4) |
| Audit | Event prefix `AUTH_*` (xem `catalogs/events.md`) |
| Rate limit | 3 OTP / 15min / phone — config `app/core/settings.py` (`slowapi`) |
| Threat model | STRIDE applied — risk register §B.10 |

## B.9 Observability & Operations

| Aspect | Plan |
|---|---|
| Structured log | JSON via `structlog`, contextvar `correlation_id` (V2 §13.1) |
| Metrics | `auth_signup_requested_total`, `otp_verify_failed_total` — `prometheus-fastapi-instrumentator` (V2 §13.6) |
| Alert | Slack `#auth-ops` khi error rate > 5% / 5min |
| Runbook | `docs/v_2/runbooks/f_{id}.md` (TBD) |

## B.10 Risk Register

| Risk ID | Severity | Description | Mitigation | Owner |
|---|---|---|---|---|
| RISK-01 | H/M/L | | | |

---

# PART C — Design

> **Owner:** Lead · **Gate:** G6 · **Audience:** Lead, Dev

## C.1 User Roles & Permissions

| Role | Permission ID (catalog) | Scope |
|---|---|---|
| `USER` | `PERM-USER-VIEW_OWN` | own profile |
| `ADMIN` | `PERM-IAM-USER_ROLE_ASSIGN` | all |

## C.2 Input Specification

Per-endpoint hoặc per-action input shape (cấp feature, chi tiết per-task ở task §7).

| Input | Required? | Validation | Source |
|---|---|---|---|
| `phone` | ✓ | E.164, max 16 | Request body |

## C.3 Output Specification

| Success | Error |
|---|---|
| 200/201 với shape `{...}` | ERR catalog (xem §E.1) |

## C.4 Main Flow (End-to-End)

```
Step 1: User submit POST /auth/signup/request-otp
Step 2: Service normalize phone (BR-01) + check blocklist
Step 3: Generate OTP + persist hash + send SMS
Step 4: Return requestId + expiresInSeconds
...
```

## C.5 API Contract

| Method | Path | Request shape | Response shape | OpenAPI ref |
|---|---|---|---|---|
| POST | `/auth/signup/request-otp` | `{phone}` | 200 `{requestId, expiresInSeconds}` | FastAPI auto `/openapi.json` tag `auth` |

(Detailed schema → task §7.A khi implement)

## C.6 State Machine

| Current state | Action | Next state | Error |
|---|---|---|---|
| `PHONE_NEW` | request OTP | `OTP_PENDING` | rate limit → stay |
| `OTP_PENDING` | verify OTP success | `OTP_VERIFIED` | wrong OTP → stay (attempts++) |
| `OTP_VERIFIED` | create password | `USER_ACTIVE` | weak password → stay |

## C.7 Business Rules

| BR ID | Rule | Source |
|---|---|---|
| BR-01 | Phone normalize E.164 trước store | Vietnam format `+84xxx` |
| BR-07 | Invalidate OTP cũ khi request mới | session safety |

## C.8 Edge Cases

| EC ID | Scenario | Expected | Test ref |
|---|---|---|---|
| EC-01 | Phone format sai | 400 `ERR-AUTH-INVALID_PHONE_FORMAT` | `SignupEdgeCasesTest.test_EC01` |
| EC-05 | OTP expired | 400 `ERR-AUTH-OTP_EXPIRED` | `SignupEdgeCasesTest.test_EC05` |
| EC-07 | 5 sai liên tiếp | 429 `ERR-AUTH-OTP_MAX_ATTEMPTS` + `Retry-After` | `SignupSecurityTest.test_EC07` |

(Tối thiểu 3 EC. Liệt kê đủ — VSDD §11 cũ.)

## C.9 UI States

| State | Trigger | UI behavior |
|---|---|---|
| `loading` | submit OTP request | spinner + disable button |
| `error_rate_limit` | 429 response | toast "Vui lòng thử lại sau {n}s" |
| `success` | 200 response | next step (verify OTP screen) |

## C.10 Test Strategy

| Layer | Approach | Framework |
|---|---|---|
| Unit | Mock repo, OTP service, clock | `pytest` + `pytest-mock` |
| Integration | Testcontainers PostgreSQL + DB thật | `pytest` + `pytest-asyncio` |
| E2E | full flow request→verify→create password | `httpx.AsyncClient` + Testcontainers |
| Security | brute-force, timing, JSON escape | `pytest` (auth/permission cases) |

Coverage target: ≥ 80% unit, ≥ 70% integration (V2 §15.3).

---

# PART D — Coding context

> **Owner:** BE Lead · **Gate:** G6.5 · **Audience:** Dev, AI agent

## D.1 Task Types Inventory

> Bảng tất cả task (slice) thuộc feature. Synced với §E.2 Task Breakdown — đây là view AI-binding.

| Slice ID | Task type | Size | SP | Task file | Status |
|---|---|---|---|---|---|
| S01 | MIG | S | 1 | `tasks/f_{id}/f_{id}-task_001.md` | done/in-progress/draft |
| S02 | MODEL | S | 1 | `tasks/f_{id}/f_{id}-task_002.md` | |

## D.2 Source of Truth (anchor map)

Bảng anchor giúp task §6 VSDD/SDD/CODD Pointers trỏ chính xác section của spec này.

| Concept | Section anchor |
|---|---|
| API contract | `#c5-api-contract` |
| BR rules | `#c7-business-rules` |
| EC list | `#c8-edge-cases` |
| ADR | `#b5-architecture-decisions-adr--feature-scope` |
| INV | `#b4-core-invariants-feature-scope` |
| Table spec | `database/tables/{table}.md` |
| ERR catalog | `constraints/catalogs/error_codes.md` |

## D.3 Input Context Pack

Golden references cấp feature — AI đọc TRƯỚC khi mở task đầu.

| Order | Path | Lý do đọc |
|---|---|---|
| 1 | `docs/v_2/specs/f_{id}_spec.md` (file này) | spec full |
| 2 | `app/modules/{module}/` | golden pattern |
| 3 | `database/tables/{table}.md` | column spec |
| 4 | `.claude/rules/v2-coding-standard.md` | coding standard |
| 5 | `constraints/catalogs/error_codes.md` | ERR ID |

## D.4 Output Files (Union)

Toàn bộ file mà N slice sẽ tạo/sửa (dedup, kèm chú thích slice). Verify khớp khi tổng hợp PR.

| File | Action | Slice | Note |
|---|---|---|---|
| `alembic/versions/{rev}_create_phone_otps.py` | create | S01 | |
| `app/modules/auth/models/phone_otp.py` | create | S02 | |
| `app/modules/auth/services/signup_service.py` | create | S05 | |
| `app/modules/auth/routers/signup.py` | modify | S06 | API contract (OpenAPI auto-gen) |

## D.5 Forbidden Files

Cấm chung cho mọi slice của feature.

| Path | Lý do |
|---|---|
| `app/modules/{other-module}/**` | cross-module ban (INV-5) |
| `alembic/versions/{baseline}_*.py` | foundation baseline immutable |
| `database/tables/{table}.md` | freeze sau G4 |

## D.6 Constraints (Cross-cutting)

5–10 invariant cấp feature mọi slice phải giữ.

1. INV-3 outbox: mọi domain write phát sinh event MUST INSERT outbox same TX (session/commit).
2. V2 §11.3: current-user dependency (`Depends(get_current_user)`) bắt buộc cho mọi router endpoint cần auth.
3. Không log raw phone/OTP/password/token (V2 §13.4 + BR-14).
4. Mọi ERR raise phải dùng ID từ `constraints/catalogs/error_codes.md`.
5. Pydantic schema cho mọi request/response; ORM model (SQLAlchemy) không lộ trực tiếp ra API (V2 §7).

## D.7 Test Commands (feature-level)

```bash
# Run all tests cho feature
pytest tests/auth -k signup

# Run integration (Testcontainers PostgreSQL)
pytest tests/auth/integration

# Lint + type-check + full test gate (V2 standard gate)
ruff check . && mypy app && pytest --cov=app
```

## D.8 Stop Conditions (AI ask-back triggers — cấp feature)

> Mọi task con kế thừa trigger này + 17 trigger task-level (template task §13.B).

| # | Trigger | Hành động |
|---|---|---|
| F1 | Slice cần touch table thuộc module khác (INV-5 violation candidate) | STOP, escalate Architect |
| F2 | Slice cần catalog ID mới (ERR/PERM/EVT) | STOP, add catalog cùng PR |
| F3 | Slice phát hiện BR/EC mới chưa có ở §C.7/§C.8 | STOP, update spec PART C cùng PR |
| F4 | Slice phát hiện migration risk thực tế cao hơn dự kiến §B.7 | STOP, escalate CTO |
| F5 | Slice cần ADR mới (architectural decision) | STOP, add §B.5 cùng PR |

---

# PART E — Tracking & Sign-off

> **Owner:** PM · **Audience:** PM, all roles

## E.1 Catalog Dependencies

ERR / PERM / EVT IDs mà feature reference (link `constraints/catalogs/*.md`).

| Catalog | IDs used |
|---|---|
| `error_codes.md` | `ERR-AUTH-INVALID_PHONE_FORMAT`, `ERR-AUTH-OTP_EXPIRED`, ... |
| `permissions.md` | (nếu có) |
| `events.md` | `EVT-AUTH-USER_SIGNED_UP` |

## E.2 Task Breakdown

| Slice | Task ID | Type | Size | SP | Depends on | Owner | PR | Status |
|---|---|---|---|---|---|---|---|---|
| S01 | `F-XXX-NN-TASK-001` | MIG | S | 1 | — | BE | #123 | done |
| S02 | `F-XXX-NN-TASK-002` | MODEL | S | 1 | S01 | BE | #124 | in-progress |
| ... | | | | | | | | |

## E.3 AI Session Plan Overview

Mapping slice ↔ AI session ↔ task file. Mỗi slice = 1 Claude Code conversation = 1 PR (V2 §16 T2 default).

| Slice | AI tier | Task file | AI session # |
|---|---|---|---|
| S01 | T1 | `tasks/f_{id}/f_{id}-task_001.md` | 1 |

## E.4 Sign-off Matrix (gate per PART)

| PART | Gate | Owner | Approver | Status | Người ACK | Ngày |
|---|---|---|---|---|---|---|
| A Business | G3 | BA/PM | Lead | `draft` | | |
| B Architecture | G4 | Architect | CTO | `draft` | | |
| C Design | G6 | Lead | Lead | `draft` | | |
| D Coding | G6.5 | BE Lead | BE Lead | `draft` | | |
| E Tracking | G7+ | PM | PM | live | | |
| Feature Done | G8 | PM | PM + Tech Lead | — | | |

**Update rule:** mỗi khi PART đạt `approved`, ghi tên + ngày. Block-task rule: task chỉ được start khi PART A+B+C+D đều `approved` (verify ở task §4.A.2..§4.A.5).

## E.5 PR Evidence Index

| PR # | Slice | Task ID | Merged date | Notes |
|---|---|---|---|---|
| | | | | |

---

## Changelog

| Date | Version | Change | Author |
|---|---|---|---|
| YYYY-MM-DD | v1.0 | Initial spec (migrated from REQ + SDD + VSDD + CODD) | |
