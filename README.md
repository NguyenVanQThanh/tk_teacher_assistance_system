# SmartLMS — Hệ thống Quản lý Bài tập & Phân tích Hành vi Học tập

> Nền tảng quản lý bài tập thông minh, tích hợp **phân tích hành vi học tập** (Learning Analytics) và **AI tạo sinh** (Generative AI), hỗ trợ toàn diện cho giáo viên và học sinh.

| | |
|---|---|
| **Trạng thái** | 🚧 Đang thiết kế (Sprint 0 — Foundation & Auth) |
| **Tài liệu nguồn** | SRS v1.0 — `docs/HỆ THỐNG QUẢN LÍ BÀI TẬP KẾT HỢP PHÂN TÍCH HÀNH VI.pdf` |
| **Stack** | Python · FastAPI · SQLAlchemy 2.0 · Alembic · PostgreSQL · JWT |

---

## 1. Bối cảnh & Mục tiêu

Mô hình giao/đánh giá bài tập hiện nay gặp 3 rào cản: giáo viên **không nắm được hành vi học thực tế** của học sinh ở nhà; **thiếu công cụ trực quan hóa năng lực**; và **áp lực biên soạn bài tập cá nhân hóa** tốn nhiều công sức.

SmartLMS giải quyết bằng cách:
- **Đo lường chi tiết hành vi học tập** (thời gian, tần suất, mức tập trung).
- **Trực quan hóa năng lực** lớp & cá nhân qua dashboard, biểu đồ.
- **Thúc đẩy tự học**: học sinh tự đánh giá, đặt mục tiêu, nhận gợi ý lộ trình.
- **Tối ưu biên soạn**: AI sinh bài tập từ tài liệu giáo viên cung cấp.

---

## 2. Phạm vi chức năng (4 module cốt lõi)

| # | Module | Tóm tắt | Vai trò chính |
|---|---|---|---|
| 1 | **Tracking — Theo dõi hành vi** | Ghi vết thời gian (bắt đầu/tạm dừng/nộp), đo mức tập trung, cảnh báo hạn nộp | Giáo viên |
| 2 | **AI Generation — Tạo sinh bài tập** | Upload tài liệu → AI sinh câu hỏi → GV duyệt/sửa → giao bài | Giáo viên |
| 3 | **Teacher Dashboard** | Phổ điểm lớp, phân tích hành vi, phát hiện HS sa sút / nộp sát giờ, khuyến nghị | Giáo viên |
| 4 | **Student Dashboard** | Số liệu theo môn, đặt mục tiêu điểm, gợi ý lộ trình, biểu đồ radar | Học sinh |

**Yêu cầu phi chức năng:** RBAC nghiêm ngặt · AI sinh đề ≤ 15–30s · dashboard tải < 3s (lớp ~50 HS) · responsive.

---

## 3. Công nghệ

| Lớp | Lựa chọn |
|---|---|
| Ngôn ngữ | Python 3.11+ |
| Web framework | FastAPI |
| ORM / Migration | SQLAlchemy 2.0 / Alembic |
| Database | PostgreSQL (UUID, JSONB, GIN index) |
| Auth | JWT (`python-jose`) + `passlib[bcrypt]` |
| Phân quyền | RBAC permission-based (usecase code) + override theo user |
| Test | `pytest` · `pytest-asyncio` · `httpx` · Testcontainers |
| Chất lượng | `ruff` · `mypy` · coverage ≥ 80% |

---

## 4. Kiến trúc & cấu trúc thư mục

Monolith modular: mỗi nghiệp vụ là 1 package dưới `app/modules/`; lớp dùng chung ở `app/core/`.

```
Client → FastAPI Router → Service → Repository → PostgreSQL (SQLAlchemy)
                              │
                              ▼
                     app/core (settings · session · errors · logging · security)
```

```
.
├── README.md                     ← (file này) tổng quan dự án
├── docs/
│   ├── HỆ THỐNG ... .pdf          ← SRS gốc (BA)
│   ├── base_sql_erd.sql          ← schema PostgreSQL (ERD tham chiếu, v1.0→v1.2)
│   ├── _template_feature_spec.md ← template spec chuẩn (PART A–E)
│   └── v_1/
│       ├── sprints/              ← kế hoạch theo sprint
│       │   └── sprint_0_overview.md
│       ├── specs/                ← feature spec
│       │   ├── f_fnd_01_spec.md  ← Foundation & DB Baseline
│       │   └── f_auth_01_spec.md ← Authentication & RBAC
│       └── constraints/catalogs/ ← (TBD) error_codes / permissions / events
└── app/                          ← (TBD) mã nguồn FastAPI
```

---

## 5. Cơ sở dữ liệu

ERD đầy đủ ở [docs/base_sql_erd.sql](docs/base_sql_erd.sql), tổ chức theo version (thêm field/bảng mới ở version sau):

| Version | Nội dung | Bảng |
|---|---|---|
| **v1.0** | Lõi nghiệp vụ | `roles`, `users`, `subjects`, `classes`, `student_class`, `teacher_subjects`, `exercises`, `class_assignments`, `student_exercise_attempts` |
| **v1.1** | Phủ kín module S2–S6 | `documents`, `questions`, `answer_options`, `notifications`, `student_goals`, `learning_recommendations` |
| **v1.2** | RBAC mịn theo permission | `permissions`, `role_permissions`, `user_permissions` |
| *(hoãn)* | Cột + trigger | `users.last_login_at`, auto-sync `total_questions`, trigger `updated_at` — làm khi vào module cần |

**Phân tích hành vi** lưu ở `student_exercise_attempts` (`behavior_logs`, `detailed_results` dạng JSONB + GIN index) — trọng tâm dữ liệu của hệ thống.

---

## 6. Mô hình phân quyền (RBAC)

Phân quyền **mịn theo permission (usecase)**, không chỉ theo role:

- Mỗi endpoint khai báo `require_perm("CODE")` (vd `EXERCISE_CREATE`).
- **Role là gói permission** (`role_permissions`) — Admin chỉnh runtime.
- **Override theo user** (`user_permissions`, `allow`/`deny`).
- Tập quyền hiệu lực: `role ∪ user(allow) − user(deny)` — **deny thắng**, mặc định **fail-closed**.
- Quyền **không nhúng vào JWT** (resolve từ DB + cache theo role) → đổi quyền có hiệu lực ngay.

---

## 7. Lộ trình Sprint

| Sprint | Module | Mục tiêu |
|---|---|---|
| **S0** | Foundation & Auth | Scaffold, baseline migration, login JWT, RBAC permission-based ← *đang làm* |
| S1 | Academic Org | Môn học, lớp, ghi danh HS, phân công GV |
| S2 | Bài tập lõi | Câu hỏi, giao bài, làm & chấm điểm |
| S3 | Tracking | Ghi vết hành vi, cảnh báo hạn nộp |
| S4 | AI Generation | Upload tài liệu, AI sinh đề, GV duyệt |
| S5 | Teacher Dashboard | Phổ điểm, phân tích hành vi, khuyến nghị |
| S6 | Student Dashboard | Mục tiêu, gợi ý lộ trình, radar |

Chi tiết Sprint 0: [docs/v_1/sprints/sprint_0_overview.md](docs/v_1/sprints/sprint_0_overview.md).

---

## 8. Quy trình tài liệu

Mỗi feature có 1 spec theo template thống nhất ([_template_feature_spec.md](docs/_template_feature_spec.md)) gồm 5 phần & gate phê duyệt:

| PART | Nội dung | Gate |
|---|---|---|
| A | Business (user story, REQ, AC) | G3 |
| B | Architecture (ADR, invariant, DB boundary) | G4 |
| C | Design (API contract, BR, edge case) | G6 |
| D | Coding context (task, file, constraint) | G6.5 |
| E | Tracking & Sign-off | G7+ |

Task chỉ bắt đầu khi PART A→D đều `approved`.

---

## 9. Bước tiếp theo

- [ ] Tạo 3 catalog: `error_codes.md`, `permissions.md`, `events.md`
- [ ] Bung task files cho `F-FND-01`, `F-AUTH-01`
- [ ] Spec `F-AUTH-02` — Admin quản trị quyền (CRUD permission, mapping)
- [ ] Scaffold mã nguồn `app/` + Alembic + CI
