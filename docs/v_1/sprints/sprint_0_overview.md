# Sprint 0 — Foundation & Auth ✅ DONE

> Path: `docs/v_1/sprints/sprint_0_overview.md` · Module(s): `foundation` + `auth`
> Created At: `2026-07-17`
> Created By: `Tam Khang`
> Updated At: `2026-10-27`
> Updated By: `Tam Khang`

## Mục tiêu Sprint

Dựng **nền tảng kỹ thuật** và **xác thực/phân quyền** để mọi sprint nghiệp vụ sau (S1→S6) có thể bắt đầu. Kết thúc Sprint 0, hệ thống phải: chạy được FastAPI app, kết nối PostgreSQL qua Alembic, có bảng `roles` + `users` + seed, và cho phép người dùng **đăng nhập bằng credential → nhận JWT**, gọi API có bảo vệ theo vai trò (RBAC).

| Field | Giá trị |
|---|---|
| Sprint | `SPRINT-00` |
| Status | `done` |
| Stack | Python · FastAPI · SQLAlchemy 2.0 · Alembic · PostgreSQL · `python-jose` (JWT) · `passlib[bcrypt]` |
| SRS coverage | NFR Bảo mật / RBAC (§3) — tiền đề cho 4 module nghiệp vụ |
| DB tables | `roles`, `users` (v1.0) · `permissions`, `role_permissions`, `user_permissions` (v1.2 — RBAC) |

## Quyết định scope (assumptions)

| # | Quyết định | Lý do |
|---|---|---|
| AS-01 | **Không** có self-registration ở Sprint 0. Tài khoản do Admin tạo (hoặc seed). | SRS không mô tả luồng đăng ký; hệ thống trường học thường do quản trị cấp tài khoản. Self-register/OTP để dành module IAM sau. |
| AS-02 | Đăng nhập bằng **email hoặc phone + password** (1 trong 2 định danh). | `users` có cả `email` và `phone` UNIQUE. |
| AS-03 | JWT **stateless**, chỉ access token. Refresh token + blocklist để version sau. | Giữ Sprint 0 gọn; chưa cần bảng phụ. |
| AS-04 | RBAC **mịn theo permission (usecase)**: endpoint khai báo `require_perm("CODE")`; role là gói permission; Admin gán/sửa role↔permission lúc runtime + override allow/deny theo từng user. | Cần thêm bảng `permissions`, `role_permissions`, `user_permissions` (schema v1.2). Linh hoạt cho Admin, nâng mức bảo mật. |
| AS-05 | Endpoint quản trị quyền cho Admin (CRUD mapping) tách thành feature riêng `F-ADMIN-02` (Sprint 3); Sprint 0 chỉ làm **model + enforcement + seed mapping mặc định**. | Giữ F-AUTH-01 gọn; flexibility đã khả dụng qua DB/seed ngay. |

## Features trong Sprint

| Feature ID | Tên | Module | Spec | Phụ thuộc | Status |
|---|---|---|---|---|---|
| `F-FND-01` | Foundation & DB Baseline | `foundation` | [f_fnd_01_spec.md](../specs/f_fnd_01_spec.md) | — | `done` |
| `F-AUTH-01` | Authentication & RBAC | `auth` | [f_auth_01_spec.md](../specs/f_auth_01_spec.md) | `F-FND-01` | `done` |

## Thứ tự thực thi

```
F-FND-01 (scaffold + Alembic baseline roles/users + seed + error envelope + JWT util)
   └── F-AUTH-01 (login → JWT, current-user dependency, RBAC, change-password, /me)
```

F-AUTH-01 **không được start** trước khi F-FND-01 đạt gate G6.5 (Coding) `approved`, vì auth dùng lại: DB session, settings, error envelope, JWT util, model `users`/`roles` của foundation.

## Definition of Done — Sprint 0

| ✓ | Tiêu chí | Status |
|---|---|---|
| [x] | `alembic upgrade head` tạo `roles` + `users`, seed 3 role + 1 admin bootstrap | `done` |
| [x] | `GET /health` và `GET /health/ready` (DB ping) trả 200 | `done` |
| [x] | `POST /api/v1/auth/login` trả JWT hợp lệ; sai credential trả `ERR-AUTH-INVALID_CREDENTIALS` | `done` |
| [x] | `GET /api/v1/auth/me` yêu cầu Bearer token; thiếu/sai token trả 401 | `done` |
| [x] | Endpoint mẫu `require_perm("X")`: từ chối user thiếu quyền (403); user bị `deny` X → 403 dù role có; user được `allow` X → 200 | `done` |
| [x] | `alembic upgrade head` tạo `permissions`/`role_permissions`/`user_permissions`; seed mapping role mặc định idempotent | `done` |
| [x] | Mọi lỗi trả về theo **error envelope** chuẩn + `correlation_id` | `done` |
| [x] | `ruff check . && mypy app && pytest --cov=app` pass; coverage ≥ 80% unit | `done` |
| [x] | Cả 2 spec (F-FND-01, F-AUTH-01) sign-off PART A→D `approved` | `done` |

## Trạng thái Đồng bộ API Backend ↔ Frontend (`auth`)

| Method & Endpoint | Backend (`auth.py`) | Khai báo `api.js` | Màn hình Frontend sử dụng | Trạng thái Sync |
|---|---|---|---|---|
| `POST /api/v1/auth/login` | ✅ Đã có | `authApi.login` | `LoginPage.jsx`, `AuthContext.jsx` | ✅ Đã đồng bộ |
| `GET /api/v1/auth/me` | ✅ Đã có | `authApi.getMe` | `AuthContext.jsx`, `TeacherProfilePage.jsx` | ✅ Đã đồng bộ |
| `POST /api/v1/auth/logout` | ✅ Đã có | `authApi.logout` | `AuthContext.jsx`, `Header.jsx` | ✅ Đã đồng bộ |
| `POST /api/v1/auth/change-password` | ✅ Đã có | `authApi.changePassword` | `TeacherProfilePage.jsx` | ✅ Đã đồng bộ |
| `POST /api/v1/auth/register` | ✅ Đã có | ❌ Chưa khai báo | Chưa nối UI | ⚠️ Đã có BE, thiếu ở `api.js` |
| `PUT /api/v1/auth/me` *(Cập nhật hồ sơ cá nhân)* | ❌ Chưa có ở BE | ❌ Chưa khai báo | `TeacherProfilePage.jsx` (Tab Hồ sơ đang lưu state tạm) | ❌ Thiếu API ở BE |

## Catalogs khởi tạo trong Sprint này

- `docs/v_1/constraints/catalogs/error_codes.md` — seed `ERR-AUTH-*`, `ERR-CORE-*`
- `docs/v_1/constraints/catalogs/permissions.md` — danh mục `PERM-*` (permission code) + bảng map role→permission mặc định (seed)
- `docs/v_1/constraints/catalogs/events.md` — seed `EVT-AUTH-USER_LOGGED_IN`
