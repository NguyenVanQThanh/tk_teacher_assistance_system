# SmartLMS — Hệ thống Quản lý Bài tập & Phân tích Hành vi Học tập

> Nền tảng quản lý bài tập thông minh, tích hợp **phân tích hành vi học tập** (Learning Analytics) và **AI tạo sinh** (Generative AI), hỗ trợ toàn diện cho giáo viên và học sinh.

| | |
|---|---|
| **Trạng thái** | ✅ Sprint 0, Sprint 1, Sprint 2 |
| **Kiến trúc** | Monorepo (`backend/` & `frontend/`) |
| **Backend Stack** | Python 3.11+ · FastAPI · SQLAlchemy 2.0 · Alembic · PostgreSQL · JWT |
| **Frontend Stack** | React 18 · Vite · JavaScript/CSS |

---

## 1. Cấu trúc Thư mục Monorepo

```text
tk_teacher_assistance_system/
├── backend/                      # Dịch vụ Backend (FastAPI, Alembic, SQLAlchemy)
│   ├── alembic/                  # Database migration scripts
│   ├── alembic.ini               # Cấu hình Alembic
│   ├── app/                      # Mã nguồn ứng dụng FastAPI
│   │   ├── core/                 # Cấu hình, database, bảo mật, xử lý lỗi
│   │   ├── modules/              # Các module nghiệp vụ (auth, academic, exercise,...)
│   │   ├── scripts/              # Script khởi tạo seed data và tiện ích
│   │   └── main.py               # Điểm khởi chạy FastAPI
│   ├── models/                   # SQLAlchemy ORM Models
│   ├── tests/                    # Unit, Integration & E2E tests
│   ├── requirements.txt          # Python dependencies
│   ├── pytest.ini                # Cấu hình pytest
│   ├── Dockerfile                # Docker build cho Backend
│   └── README.md                 # Hướng dẫn chi tiết cho Backend
│
├── frontend/                     # Ứng dụng Frontend (React + Vite)
│   ├── public/                   # Static assets
│   ├── src/                      # Source code giao diện (Components, Pages, Services)
│   ├── index.html                # Entrypoint HTML
│   ├── package.json              # Quản lý dependencies Frontend
│   ├── vite.config.js            # Cấu hình Vite & API Proxy
│   ├── Dockerfile                # Docker build cho Frontend
│   └── README.md                 # Hướng dẫn chi tiết cho Frontend
│
├── docs/                         # Tài liệu hệ thống, SRS, Specs & Tasks
├── docker-compose.yml            # Docker Compose chạy toàn bộ hệ thống (DB, BE, FE)
└── README.md                     # Tài liệu tổng quan dự án
```

---

## 2. Hướng dẫn Khởi chạy Dự án

### Cách 1: Sử dụng Docker Compose (Toàn bộ hệ thống)

Khởi chạy cả Database (PostgreSQL), Backend (FastAPI) và Frontend (React/Vite) chỉ với một lệnh:

```bash
docker-compose up -d --build
```

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **PostgreSQL**: `localhost:5432`

---

### Cách 2: Chạy độc lập từng phần (Local Development)

#### 1. Khởi chạy Database (PostgreSQL)
```bash
docker-compose up -d postgres
```

#### 2. Khởi chạy Backend (`backend/`)
```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env

# Chạy migrations & khởi động server
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

#### 3. Khởi chạy Frontend (`frontend/`)
```bash
cd frontend
npm install
npm run dev
```

---

## 3. Kiểm thử (Testing)

Chạy test suite cho Backend:
```bash
cd backend
pytest
```
