# Feature Spec — `F-AUTH-01` Authentication & RBAC

> Path: `docs/v_1/specs/f_auth_01_spec.md` ·

---

## Document Header

| Field | Giá trị |
|---|---|
| Feature ID | `F-AUTH-01` |
| Feature name | Authentication & RBAC |
| Module(s) | `auth` + `foundation` (consumer) |
| Sprint(s) allocated | `SPRINT-00` |
| Lane | `standard` |
| Spec version | `v1.0` |
| Last updated | `2026-06-26` |
| Source binding | SOP §12 · `docs/base_sql_erd.sql` v1.0 · `f_fnd_01_spec.md` · `.claude/rules/v2-coding-standard.md` |

### Gate status

| Gate | Bao trùm | Owner | Approver | Status | Date |
|---|---|---|---|---|---|
| G3 Business | PART A | BA/PM | Lead | `draft` | |
| G4 Architecture | PART B | Architect | CTO | `draft` | |
| G6 Design | PART C | Lead | Lead | `draft` | |
| G6.5 Coding | PART D | BE Lead | BE Lead | `draft` | |
| G7+ Tracking | PART E | PM | PM | `draft` | |

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

Cho phép người dùng (Admin / GiaoVien / HocSinh) **đăng nhập bằng email hoặc phone + password** để nhận **JWT access token**, dùng token gọi các API được bảo vệ. Cung cấp cơ chế **RBAC mịn theo permission (usecase)**: mỗi endpoint khai báo `require_perm("CODE")`; role là một *gói* permission (`role_permissions`); Admin gán/sửa quyền theo role lúc runtime và **override allow/deny theo từng user** (`user_permissions`). Đây là nền bảo mật cho toàn hệ thống — đáp ứng NFR §3 SRS: "phân quyền nghiêm ngặt, HS không xem dữ liệu HS khác, GV chỉ quản lý lớp mình". Phụ thuộc `F-FND-01` (model `users`/`roles`, JWT util, error envelope). **Sprint 0 không có self-registration** — tài khoản do Admin/seed tạo (AS-01); endpoint quản trị mapping quyền tách sang `F-AUTH-02` (AS-05).

## A.2 User Stories

| Story ID | As (role) | I want (capability) | So that (value) |
|---|---|---|---|
| US-01 | Người dùng | đăng nhập bằng email/phone + password | nhận token để truy cập hệ thống |
| US-02 | Người dùng đã đăng nhập | xem thông tin tài khoản của mình (`/me`) | xác nhận danh tính & vai trò |
| US-03 | Người dùng | đổi mật khẩu | bảo mật tài khoản |
| US-04 | Developer | dependency RBAC theo permission usecase (`require_perm`) | bảo vệ từng endpoint ở mức quyền chi tiết, nhất quán |
| US-05 | Người dùng | đăng xuất | kết thúc phiên (client xóa token) |
| US-06 | Admin | gán/sửa quyền cho role và override theo user (qua seed/DB ở Sprint 0, UI ở `F-AUTH-02`) | điều chỉnh phân quyền linh hoạt không cần sửa code |

## A.3 REQ Registry

| REQ ID | Mô tả ngắn | Priority | Status | Linked Story |
|---|---|---|---|---|
| REQ-AUTH-001 | Login: email/phone + password → access token | P0 | `draft` | US-01 |
| REQ-AUTH-002 | Phát hành & xác thực JWT (claims: sub, role, exp) | P0 | `draft` | US-01 |
| REQ-AUTH-003 | `GET /me`: lấy profile user hiện tại từ token | P0 | `draft` | US-02 |
| REQ-AUTH-004 | RBAC dependency `require_perm("CODE")` theo permission usecase | P0 | `draft` | US-04 |
| REQ-AUTH-005 | Đổi mật khẩu (verify mật khẩu cũ) | P1 | `draft` | US-03 |
| REQ-AUTH-006 | Logout stateless (client discard; server không lưu state) | P2 | `draft` | US-05 |
| REQ-AUTH-007 | Khóa đăng nhập tạm thời sau N lần sai (chống brute-force) | P1 | `draft` | US-01 |
| REQ-AUTH-008 | Tính tập quyền hiệu lực: `role_permissions ∪ user(allow) − user(deny)` (deny thắng), có cache theo role | P0 | `draft` | US-04 |
| REQ-AUTH-009 | Seed danh mục `permissions` + mapping role→permission mặc định (idempotent) | P0 | `draft` | US-04 |

## A.4 Acceptance Criteria (Feature-level)

| AC ID | REQ | Given | When | Then |
|---|---|---|---|---|
| AC-01 | REQ-AUTH-001 | user active đúng credential | `POST /auth/login` | 200 `{access_token, token_type, user}` |
| AC-02 | REQ-AUTH-001 | sai password | `POST /auth/login` | 401 `ERR-AUTH-INVALID_CREDENTIALS` (không tiết lộ user tồn tại hay không) |
| AC-03 | REQ-AUTH-001 | user `status='Blocked'` | login đúng password | 403 `ERR-AUTH-ACCOUNT_BLOCKED` |
| AC-04 | REQ-AUTH-003 | token hợp lệ | `GET /auth/me` | 200 profile (không có `password_hash`) |
| AC-05 | REQ-AUTH-002 | token hết hạn/sai chữ ký | gọi endpoint bảo vệ | 401 `ERR-AUTH-INVALID_TOKEN` |
| AC-06 | REQ-AUTH-004 | user không có quyền `X` | gọi endpoint yêu cầu `require_perm("X")` | 403 `ERR-AUTH-FORBIDDEN` |
| AC-07 | REQ-AUTH-005 | mật khẩu cũ đúng | `POST /auth/change-password` | 200, hash mới lưu DB, mật khẩu cũ hết hiệu lực |
| AC-08 | REQ-AUTH-007 | sai password 5 lần liên tiếp | login lần 6 | 429 `ERR-AUTH-TOO_MANY_ATTEMPTS` + `Retry-After` |
| AC-09 | REQ-AUTH-008 | role có quyền `X` nhưng user bị `deny X` | gọi endpoint cần `X` | 403 (deny thắng role) |
| AC-10 | REQ-AUTH-008 | role không có `Y` nhưng user được `allow Y` | gọi endpoint cần `Y` | 200 (override allow) |
| AC-11 | REQ-AUTH-009 | DB mới seed | kiểm tra mapping | 3 role có tập permission mặc định đúng; chạy seed lại không nhân đôi |

## A.5 In / Out of Scope

**In scope:**
- Login (email/phone + password), JWT access token, `/me`, change-password, logout stateless, rate-limit login.
- **RBAC permission-based**: dependency `require_perm`, tính tập quyền hiệu lực (role ∪ user-allow − user-deny), cache theo role.
- Seed danh mục `permissions` + mapping role→permission mặc định.

**Out of scope (defer):**
- Self-registration / OTP / email verification → module IAM sau (AS-01).
- Refresh token, token blocklist/revocation server-side → version sau (AS-03).
- Quản lý user (CRUD, gán vai trò, import) → module IAM.
- **Endpoint Admin CRUD quyền** (tạo permission, sửa mapping role/user qua API/UI) → `F-AUTH-02` (AS-05). Sprint 0 chỉnh qua seed/DB.
- Quên mật khẩu / reset qua email → sau.

## A.6 REQ → Task Type Map

| REQ ID | Task type(s) cần | Note |
|---|---|---|
| REQ-AUTH-001/002 | SCHEMA → REPO → SERVICE → API → TEST | login flow |
| REQ-AUTH-003 | API → TEST | dùng current-user dependency |
| REQ-AUTH-004 | DEPENDENCY → TEST | RBAC |
| REQ-AUTH-005 | SERVICE → API → TEST | change password |
| REQ-AUTH-007 | MIDDLEWARE/SERVICE → TEST | rate limit |

## A.7 Feature DoD

| ✓ | Tiêu chí Feature Done |
|---|---|
| ☐ | Tất cả AC §A.4 verified qua test |
| ☐ | Tất cả task con merged (PART E.2) |
| ☐ | Smoke test login→/me→endpoint bảo vệ pass trên staging |
| ☐ | Catalog ERR/EVT/PERM updated |
| ☐ | `ruff check . && mypy app && pytest --cov=app` pass |
| ☐ | Sign-off §E.4 hoàn tất |

---

# PART B — Architecture

> **Owner:** Architect · **Approver:** CTO · **Gate:** G4

## B.1 Executive Summary (architectural)

Module `auth` xây trên hạ tầng `F-FND-01`: dùng model `User`/`Role`, JWT util, password util, error envelope. Login xác thực credential → phát JWT stateless (HS256, claims `sub`=user_id, `role`, `exp`). Bảo vệ endpoint qua FastAPI dependency `get_current_user` + `require_perm("CODE")`, với tập quyền hiệu lực resolve từ DB (role ∪ user-allow − user-deny) và cache theo role. Quyết định chính: **stateless access-only** (không lưu session) + **permission-based RBAC** (quyền không nhúng token) để vừa scale ngang dễ vừa đổi quyền có hiệu lực ngay. Rủi ro lớn nhất: lộ token / brute-force — giảm thiểu bằng exp ngắn + rate-limit login + thông báo lỗi không tiết lộ.

## B.2 High-Level Architecture

### B.2.1 Layered diagram

```
Client → /auth/* Router → AuthService → UserRepository → PostgreSQL (users, roles)
   ▲                          │
   │ Bearer JWT               ▼
get_current_user ← security.decode_token (app/core/security)
```

### B.2.2 Critical data flow (login)

1. Client `POST /auth/login {identifier, password}`.
2. `AuthService` check rate-limit (BR-05) → load user theo email **hoặc** phone (BR-01).
3. `verify_password(plain, user.password_hash)`; sai → tăng đếm fail, raise `INVALID_CREDENTIALS`.
4. Check `status` (Active/Blocked).
5. Phát JWT (`create_access_token`), emit `EVT-AUTH-USER_LOGGED_IN`, cập nhật đếm fail = 0.
6. Trả `{access_token, token_type:"bearer", expires_in, user}`.

## B.3 Domain Ownership Matrix

| Table / Resource | Owner module | Readers | Writers (cross-module) |
|---|---|---|---|
| `users` | `foundation` | `auth` | `auth` (update `password_hash` qua service — không sửa schema) |
| `roles` | `foundation` | `auth` | (none) |
| `permissions` | `auth` | mọi module (kiểm tra quyền) | `auth` (seed); `F-AUTH-02` (Admin CRUD) |
| `role_permissions` | `auth` | `auth` | `auth` (seed); `F-AUTH-02` |
| `user_permissions` | `auth` | `auth` | `auth`; `F-AUTH-02` |

## B.4 Core Invariants (Feature-scope)

| ID | Invariant | Scope | Reference |
|---|---|---|---|
| `INV-AUTH-01` | Response login không tiết lộ user có tồn tại hay không (cùng lỗi `INVALID_CREDENTIALS`) | feature | OWASP |
| `INV-AUTH-02` | Token claim `role` phải khớp `users.role_id` tại thời điểm phát; không tin role/permission do client gửi | feature | RBAC |
| `INV-AUTH-03` | `password_hash` không bao giờ xuất hiện trong response/log | global | INV-FND-02 |
| `INV-AUTH-04` | Endpoint bảo vệ bắt buộc qua `Depends(get_current_user)` / `require_perm`; không tự parse header | feature | V2 §11.3 |
| `INV-AUTH-05` | Quyền hiệu lực luôn tính tại server từ DB; **deny (user) thắng** mọi allow; mặc định **fail-closed** (không có quyền = 403) | feature | RBAC |
| `INV-AUTH-06` | Tập quyền **không** nhúng vào JWT (tránh stale khi Admin đổi quyền); resolve qua DB + cache theo role, invalidate khi mapping đổi | feature | ADR-AUTH-004 |

## B.5 Architecture Decisions (ADR — Feature-scope)

| ADR ID | Title | Status | Approver | Date | Summary |
|---|---|---|---|---|---|
| `ADR-AUTH-001` | JWT HS256 stateless, access-only (Sprint 0) | `approved` | CTO | 2026-06-26 | Refresh/blocklist defer (kế thừa ADR-FND-003) |
| `ADR-AUTH-002` | RBAC permission-based (usecase code) ngay từ Sprint 0; role là gói permission + override theo user | `approved` | CTO | 2026-06-26 | Khớp AS-04; nâng mức bảo mật, linh hoạt cho Admin |
| `ADR-AUTH-003` | Rate-limit login theo identifier + IP (`slowapi`) | `proposed` | CTO | 2026-06-26 | Chống brute-force, REQ-AUTH-007 |
| `ADR-AUTH-004` | Permission **không** nhúng trong JWT; resolve từ DB + cache theo role (invalidate khi đổi mapping) | `approved` | CTO | 2026-06-26 | Đổi quyền có hiệu lực ngay, không chờ token hết hạn |

## B.6 API Boundary

| Method | Path | Auth | OpenAPI tag |
|---|---|---|---|
| POST | `/api/v1/auth/login` | none | `auth` |
| GET | `/api/v1/auth/me` | Bearer | `auth` |
| POST | `/api/v1/auth/change-password` | Bearer | `auth` |
| POST | `/api/v1/auth/logout` | Bearer | `auth` |

## B.7 Database Boundary

| Table | Op | Table spec file | Migration |
|---|---|---|---|
| `users` | READ + UPDATE (`password_hash`) | `database/tables/users.md` | (không migration mới — dùng baseline `F-FND-01`) |
| `roles` | READ | `database/tables/roles.md` | — |
| `permissions` | CREATE + READ | `database/tables/permissions.md` | `alembic/versions/{rev}_create_rbac_tables.py` (risk low) |
| `role_permissions` | CREATE + READ | `database/tables/role_permissions.md` | (cùng migration trên) |
| `user_permissions` | CREATE + READ | `database/tables/user_permissions.md` | (cùng migration trên) |

> Lưu ý: 3 bảng RBAC theo `base_sql_erd.sql` **v1.2** (mục 16–18). Cột `users.last_login_at` vẫn **defer** (chỉ emit event ở Sprint 0).

## B.8 Security & Privacy

| Aspect | Decision |
|---|---|
| AuthN | JWT bearer (`python-jose`), password verify `bcrypt`/`passlib` (V2 §12.1) |
| AuthZ | FastAPI `Depends(require_perm("EXERCISE_CREATE"))` — quyền hiệu lực resolve từ DB (role ∪ user-allow − user-deny), cache theo role (xem §C.1, INV-AUTH-05/06) |
| PII handling | Email/phone masked trong log; không log password/token (V2 §13.4) |
| Audit | `EVT-AUTH-USER_LOGGED_IN`, `EVT-AUTH-LOGIN_FAILED`, `EVT-AUTH-PASSWORD_CHANGED` |
| Rate limit | 5 lần sai / 15 phút / identifier — config `app/core/settings.py` (`slowapi`) |
| Token | HS256, `exp` mặc định 60 phút (config); secret từ `SECRET_KEY` |
| Threat model | STRIDE — risk §B.10 |

## B.9 Observability & Operations

| Aspect | Plan |
|---|---|
| Structured log | JSON via `structlog`, contextvar `correlation_id` (V2 §13.1) |
| Metrics | `auth_login_success_total`, `auth_login_failed_total`, `auth_token_invalid_total` — `prometheus-fastapi-instrumentator` |
| Alert | error rate login_failed > 30% / 5min → cảnh báo brute-force |
| Runbook | `docs/v_1/runbooks/f_auth_01.md` (TBD) |

## B.10 Risk Register

| Risk ID | Severity | Description | Mitigation | Owner |
|---|---|---|---|---|
| RISK-01 | H | Brute-force password | Rate-limit (REQ-AUTH-007) + exp ngắn + log/alert | BE Lead |
| RISK-02 | H | Lộ `SECRET_KEY` → giả mạo token | Secret từ `.env`/secret manager, rotate được | Architect |
| RISK-03 | M | Token không revoke được khi đổi mật khẩu (stateless) | exp ngắn; revocation/blocklist version sau | CTO |
| RISK-04 | M | User enumeration qua message lỗi | INV-AUTH-01 (lỗi đồng nhất) | BE |

---

# PART C — Design

> **Owner:** Lead · **Gate:** G6

## C.1 User Roles & Permissions

**Permission code (module `auth`) seed ở Sprint 0:**

| Permission code | Mô tả | Endpoint |
|---|---|---|
| `AUTH_ME_VIEW` | Xem profile của chính mình | `GET /auth/me` |
| `AUTH_PASSWORD_CHANGE` | Đổi mật khẩu của chính mình | `POST /auth/change-password` |
| `AUTH_PERM_MANAGE` | Quản trị danh mục quyền & mapping (dùng ở `F-AUTH-02`) | (F-AUTH-02) |

> `POST /auth/login` và `POST /auth/logout` là **public/authenticated cơ bản**, không gắn permission.

**Mapping role → permission mặc định (seed, `role_permissions`):**

| Role | Permission mặc định |
|---|---|
| `Admin` | `AUTH_ME_VIEW`, `AUTH_PASSWORD_CHANGE`, `AUTH_PERM_MANAGE` (+ mọi quyền module khác khi thêm) |
| `GiaoVien` | `AUTH_ME_VIEW`, `AUTH_PASSWORD_CHANGE` |
| `HocSinh` | `AUTH_ME_VIEW`, `AUTH_PASSWORD_CHANGE` |

> Quyền của các module nghiệp vụ (vd `EXERCISE_CREATE`, `DASHBOARD_CLASS_VIEW`) được seed dần khi vào sprint tương ứng; Admin chỉnh mapping runtime (qua `F-AUTH-02`). Override cá nhân lưu ở `user_permissions` (allow/deny).

## C.2 Input Specification

| Input | Required? | Validation | Source |
|---|---|---|---|
| `identifier` | ✓ | email hợp lệ **hoặc** phone (E.164/local) | login body |
| `password` | ✓ | 1..128 ký tự, không trim giữa | login body |
| `old_password` / `new_password` | ✓ | new ≥ 8 ký tự, khác old | change-password body |
| `Authorization` | ✓ (endpoint bảo vệ) | `Bearer <jwt>` | header |

## C.3 Output Specification

| Success | Error |
|---|---|
| Login 200 `{access_token, token_type:"bearer", expires_in, user:{user_id, full_name, role, email_masked}}` | Error envelope (`F-FND-01` §C.3) + ERR catalog §E.1 |
| `/me` 200 `{user_id, full_name, role, email, phone, status}` (no `password_hash`) | 401 / 403 |

## C.4 Main Flow (End-to-End)

```
Step 1: POST /api/v1/auth/login {identifier, password}
Step 2: Rate-limit check (BR-05) → nếu vượt → 429
Step 3: Load user by email OR phone (BR-01); không thấy → INVALID_CREDENTIALS (INV-AUTH-01)
Step 4: verify_password; sai → fail_count++ + LOGIN_FAILED + INVALID_CREDENTIALS
Step 5: status != Active → ACCOUNT_BLOCKED / ACCOUNT_INACTIVE
Step 6: create_access_token(sub=user_id, role=role_name) → reset fail_count
Step 7: emit EVT-AUTH-USER_LOGGED_IN → trả token + user
```

## C.5 API Contract

| Method | Path | Request shape | Response shape | OpenAPI ref |
|---|---|---|---|---|
| POST | `/api/v1/auth/login` | `{identifier, password}` | 200 `{access_token, token_type, expires_in, user}` | FastAPI auto `/openapi.json` tag `auth` |
| GET | `/api/v1/auth/me` | — (Bearer) | 200 `{user_id, full_name, role, ...}` | tag `auth` |
| POST | `/api/v1/auth/change-password` | `{old_password, new_password}` | 200 `{status:"ok"}` | tag `auth` |
| POST | `/api/v1/auth/logout` | — (Bearer) | 200 `{status:"ok"}` | tag `auth` |

## C.6 State Machine

| Current state | Action | Next state | Error |
|---|---|---|---|
| `ANON` | login success | `AUTHENTICATED` (token cấp) | wrong cred → stay (fail_count++) |
| `AUTHENTICATED` | gọi endpoint bảo vệ | stay | token expired → `ANON` (401) |
| `AUTHENTICATED` | change-password | stay (token cũ vẫn valid tới exp) | old sai → stay |
| `AUTHENTICATED` | logout | `ANON` (client xóa token) | — |

## C.7 Business Rules

| BR ID | Rule | Source |
|---|---|---|
| BR-01 | Định danh login: thử match `email` trước, không có thì `phone` | AS-02 |
| BR-02 | Role trong token lấy từ DB (`roles.role_name`), không tin client | INV-AUTH-02 |
| BR-03 | Đổi mật khẩu phải verify `old_password` đúng và `new != old` | REQ-AUTH-005 |
| BR-04 | Token exp mặc định 60 phút (config `ACCESS_TOKEN_EXPIRE_MINUTES`) | ADR-AUTH-001 |
| BR-05 | Rate-limit: 5 lần sai / 15 phút / identifier → khóa tạm 15 phút | REQ-AUTH-007 |
| BR-06 | Logout stateless: server không lưu, client chịu trách nhiệm xóa token | AS-03 |
| BR-07 | Tập quyền hiệu lực = `role_permissions(role)` ∪ `user_permissions(allow)` − `user_permissions(deny)`; **deny thắng** | INV-AUTH-05 |
| BR-08 | Không có quyền yêu cầu = **fail-closed** → 403 `ERR-AUTH-FORBIDDEN` | INV-AUTH-05 |
| BR-09 | Permission resolve từ DB + cache theo `role_id`; cache invalidate khi `role_permissions` đổi; override user không cache (luôn đọc tươi) | ADR-AUTH-004 |
| BR-10 | Permission **không** nhúng trong JWT; token chỉ mang `sub`, `role`, `exp` | INV-AUTH-06 |

## C.8 Edge Cases

| EC ID | Scenario | Expected | Test ref |
|---|---|---|---|
| EC-01 | identifier không tồn tại | 401 `ERR-AUTH-INVALID_CREDENTIALS` (giống sai password) | `test_login.py::test_EC01` |
| EC-02 | password đúng, `status='Blocked'` | 403 `ERR-AUTH-ACCOUNT_BLOCKED` | `test_login.py::test_EC02` |
| EC-03 | token hết hạn | 401 `ERR-AUTH-INVALID_TOKEN` | `test_token.py::test_EC03` |
| EC-04 | token chữ ký sai / bị sửa | 401 `ERR-AUTH-INVALID_TOKEN` | `test_token.py::test_EC04` |
| EC-05 | user thiếu permission yêu cầu gọi endpoint `require_perm` | 403 `ERR-AUTH-FORBIDDEN` | `test_rbac.py::test_EC05` |
| EC-05b | role có quyền nhưng user bị `deny` quyền đó | 403 (deny thắng, BR-07) | `test_rbac.py::test_EC05b` |
| EC-05c | role thiếu quyền nhưng user được `allow` quyền đó | 200 (override allow) | `test_rbac.py::test_EC05c` |
| EC-06 | 5 lần sai liên tiếp | 429 `ERR-AUTH-TOO_MANY_ATTEMPTS` + `Retry-After` | `test_login.py::test_EC06` |
| EC-07 | change-password với `new == old` | 400 `ERR-AUTH-PASSWORD_REUSE` | `test_password.py::test_EC07` |
| EC-08 | thiếu header Authorization ở endpoint bảo vệ | 401 `ERR-AUTH-MISSING_TOKEN` | `test_rbac.py::test_EC08` |

## C.9 UI States

| State | Trigger | UI behavior |
|---|---|---|
| `loading` | submit login | spinner + disable nút |
| `error_invalid` | 401 | toast "Sai tài khoản hoặc mật khẩu" (không nói rõ trường nào) |
| `error_rate_limit` | 429 | toast "Thử lại sau {n}s", disable form |
| `success` | 200 | lưu token, điều hướng theo role (Admin/GV/HS) |

## C.10 Test Strategy

| Layer | Approach | Framework |
|---|---|---|
| Unit | service login, verify_password, token decode, rbac dependency | `pytest` + `pytest-mock` |
| Integration | login→DB thật→token, change-password | `pytest` + Testcontainers PostgreSQL |
| E2E | login → /me → endpoint bảo vệ | `httpx.AsyncClient` + Testcontainers |
| Security | brute-force, user enumeration, token tampering | `pytest` (auth/permission cases) |

Coverage target: ≥ 80% unit, ≥ 70% integration (V2 §15.3).

---

# PART D — Coding context

> **Owner:** BE Lead · **Gate:** G6.5 · **Audience:** Dev, AI agent

## D.1 Task Types Inventory

| Slice ID | Task type | Size | SP | Task file | Status |
|---|---|---|---|---|---|
| S01 | SCHEMA (Pydantic) | S | 1 | `tasks/f_auth_01/f_auth_01-task_001.md` | draft |
| S02 | REPO | S | 1 | `tasks/f_auth_01/f_auth_01-task_002.md` | draft |
| S03 | SERVICE (login + token) | M | 3 | `tasks/f_auth_01/f_auth_01-task_003.md` | draft |
| S04 | DEPENDENCY (get_current_user + require_perm + permission resolver/cache) | M | 3 | `tasks/f_auth_01/f_auth_01-task_004.md` | draft |
| S05 | API (login, me, logout) | M | 2 | `tasks/f_auth_01/f_auth_01-task_005.md` | draft |
| S06 | SERVICE+API (change-password) | S | 1 | `tasks/f_auth_01/f_auth_01-task_006.md` | draft |
| S07 | MIDDLEWARE (rate-limit login) | S | 1 | `tasks/f_auth_01/f_auth_01-task_007.md` | draft |
| S08 | TEST (e2e + security + rbac override) | M | 2 | `tasks/f_auth_01/f_auth_01-task_008.md` | draft |
| S09 | MIG+SEED (3 bảng RBAC + permissions/role_permissions mặc định) | M | 2 | `tasks/f_auth_01/f_auth_01-task_009.md` | draft |
| S10 | REPO (permission_repository: load role perms + user overrides) | S | 1 | `tasks/f_auth_01/f_auth_01-task_010.md` | draft |

## D.2 Source of Truth (anchor map)

| Concept | Section anchor |
|---|---|
| API contract | `#c5-api-contract` |
| BR rules | `#c7-business-rules` |
| EC list | `#c8-edge-cases` |
| ADR | `#b5-architecture-decisions-adr--feature-scope` |
| INV | `#b4-core-invariants-feature-scope` |
| ERR catalog | `docs/v_1/constraints/catalogs/error_codes.md` |
| Foundation util | `f_fnd_01_spec.md` §D.4 (`app/core/security.py`) |

## D.3 Input Context Pack

| Order | Path | Lý do đọc |
|---|---|---|
| 1 | `docs/v_1/specs/f_auth_01_spec.md` (file này) | spec full |
| 2 | `docs/v_1/specs/f_fnd_01_spec.md` | util/model/error dùng lại |
| 3 | `app/core/security.py`, `app/modules/foundation/models.py` | golden pattern |
| 4 | `docs/v_1/constraints/catalogs/error_codes.md` | ERR ID |
| 5 | `.claude/rules/v2-coding-standard.md` | coding standard |

## D.4 Output Files (Union)

| File | Action | Slice | Note |
|---|---|---|---|
| `app/modules/auth/schemas.py` | create | S01 | LoginRequest/Response, ChangePassword, UserOut |
| `app/modules/auth/repository.py` | create | S02 | get_by_email / get_by_phone |
| `app/modules/auth/services/auth_service.py` | create | S03 | login, issue token, fail-count |
| `app/modules/auth/dependencies.py` | create | S04 | `get_current_user`, `require_perm` |
| `app/modules/auth/services/permission_service.py` | create | S04 | resolve tập quyền hiệu lực + cache theo role |
| `app/modules/auth/routers/auth.py` | create | S05 | login, me, logout |
| `app/modules/auth/services/password_service.py` | create | S06 | change-password |
| `app/core/rate_limit.py` | create/modify | S07 | slowapi limiter cho login |
| `tests/auth/**` | create | S08 | unit/integration/e2e/rbac |
| `alembic/versions/{rev}_create_rbac_tables.py` | create | S09 | permissions, role_permissions, user_permissions |
| `app/modules/auth/models.py` | create | S09 | SQLAlchemy `Permission`, `RolePermission`, `UserPermission` |
| `app/scripts/seed.py` | modify | S09 | seed permission code + mapping mặc định (idempotent) |
| `app/modules/auth/permission_repository.py` | create | S10 | query role perms + user overrides |

## D.5 Forbidden Files

| Path | Lý do |
|---|---|
| `app/modules/foundation/**` (sửa schema/model) | foundation immutable sau G4 (chỉ đọc/dùng) |
| `alembic/versions/{baseline}_*.py` | baseline immutable |
| `app/modules/{other}/**` | cross-module ban (INV-5) |

## D.6 Constraints (Cross-cutting)

1. Endpoint bảo vệ bắt buộc qua `Depends(get_current_user)` / `require_perm("CODE")` — không tự parse header (INV-AUTH-04, V2 §11.3).
2. Không log raw password/token; email/phone masked (INV-AUTH-03, V2 §13.4).
3. Lỗi credential đồng nhất, không tiết lộ user tồn tại (INV-AUTH-01).
4. Mọi ERR raise dùng ID từ `error_codes.md`; mọi domain event ghi qua outbox cùng transaction (INV-3).
5. Pydantic schema cho request/response; `password_hash` không bao giờ vào response model.
6. Role/permission lấy & kiểm tra ở server từ DB, không tin client (INV-AUTH-02).
7. Quyền hiệu lực fail-closed; **deny (user) thắng** allow; permission không nhúng JWT (INV-AUTH-05/06, BR-07..10).

## D.7 Test Commands (feature-level)

```bash
# Unit + service
pytest tests/auth -k "unit or service"

# Integration + e2e (Testcontainers PostgreSQL)
pytest tests/auth/integration tests/auth/e2e

# Lint + type-check + full gate
ruff check . && mypy app && pytest --cov=app
```

## D.8 Stop Conditions (AI ask-back triggers)

| # | Trigger | Hành động |
|---|---|---|
| F1 | Cần touch bảng/cột ngoài `users`/`roles` (vd thêm `last_login_at`) | STOP, escalate — đó là schema v1.2 |
| F2 | Cần ERR/PERM/EVT ID mới | STOP, add catalog cùng PR |
| F3 | Phát hiện BR/EC mới chưa có ở §C.7/§C.8 | STOP, update PART C cùng PR |
| F4 | Yêu cầu refresh token / revocation phát sinh | STOP, escalate — ngoài scope Sprint 0 (AS-03) |

---

# PART E — Tracking & Sign-off

> **Owner:** PM

## E.1 Catalog Dependencies

| Catalog | IDs used |
|---|---|
| `error_codes.md` | `ERR-AUTH-INVALID_CREDENTIALS`, `ERR-AUTH-ACCOUNT_BLOCKED`, `ERR-AUTH-ACCOUNT_INACTIVE`, `ERR-AUTH-INVALID_TOKEN`, `ERR-AUTH-MISSING_TOKEN`, `ERR-AUTH-FORBIDDEN`, `ERR-AUTH-TOO_MANY_ATTEMPTS`, `ERR-AUTH-PASSWORD_REUSE` |
| `permissions.md` | `AUTH_ME_VIEW`, `AUTH_PASSWORD_CHANGE`, `AUTH_PERM_MANAGE` + mapping role mặc định |
| `events.md` | `EVT-AUTH-USER_LOGGED_IN`, `EVT-AUTH-LOGIN_FAILED`, `EVT-AUTH-PASSWORD_CHANGED` |

## E.2 Task Breakdown

| Slice | Task ID | Type | Size | SP | Depends on | Owner | PR | Status |
|---|---|---|---|---|---|---|---|---|
| S01 | `F-AUTH-01-TASK-001` | SCHEMA | S | 1 | F-FND-01 | BE | | draft |
| S02 | `F-AUTH-01-TASK-002` | REPO | S | 1 | S01 | BE | | draft |
| S03 | `F-AUTH-01-TASK-003` | SERVICE | M | 3 | S02 | BE | | draft |
| S09 | `F-AUTH-01-TASK-009` | MIG+SEED | M | 2 | F-FND-01 | BE | | draft |
| S10 | `F-AUTH-01-TASK-010` | REPO (perm) | S | 1 | S09 | BE | | draft |
| S04 | `F-AUTH-01-TASK-004` | DEPENDENCY | M | 3 | S03,S10 | BE | | draft |
| S05 | `F-AUTH-01-TASK-005` | API | M | 2 | S03,S04 | BE | | draft |
| S06 | `F-AUTH-01-TASK-006` | SERVICE+API | S | 1 | S04 | BE | | draft |
| S07 | `F-AUTH-01-TASK-007` | MIDDLEWARE | S | 1 | S05 | BE | | draft |
| S08 | `F-AUTH-01-TASK-008` | TEST | M | 2 | S05,S06,S07 | BE | | draft |

## E.3 AI Session Plan Overview

| Slice | AI tier | Task file | AI session # |
|---|---|---|---|
| S01–S08 | T2 | `tasks/f_auth_01/f_auth_01-task_00N.md` | 1 mỗi slice |

## E.4 Sign-off Matrix

| PART | Gate | Owner | Approver | Status | Người ACK | Ngày |
|---|---|---|---|---|---|---|
| A Business | G3 | BA/PM | Lead | `draft` | | |
| B Architecture | G4 | Architect | CTO | `draft` | | |
| C Design | G6 | Lead | Lead | `draft` | | |
| D Coding | G6.5 | BE Lead | BE Lead | `draft` | | |
| E Tracking | G7+ | PM | PM | `live` | | |
| Feature Done | G8 | PM | PM + Tech Lead | — | | |

**Update rule:** task chỉ start khi PART A+B+C+D đều `approved` **và** `F-FND-01` đã đạt G6.5.

## E.5 PR Evidence Index

| PR # | Slice | Task ID | Merged date | Notes |
|---|---|---|---|---|
| | | | | |

---

## Changelog

| Date | Version | Change | Author |
|---|---|---|---|
| 2026-06-26 | v1.0 | Initial spec — Sprint 0 authentication & RBAC | BA |
| 2026-06-26 | v1.1 | Nâng RBAC role-only → permission-based (usecase code) + override theo user (deny-wins); thêm bảng `permissions`/`role_permissions`/`user_permissions`; tách admin-management sang F-AUTH-02 | BA |
