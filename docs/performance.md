# Hiệu năng & khả năng chịu tải (30 user đồng thời, 5 GB RAM)

Tài liệu này ghi lại các thay đổi hạ tầng/concurrency/ETL cho mục tiêu **30 user
đồng thời** trên một máy chủ **tối đa 5 GB RAM**, cách đo bằng load test, và các
khuyến nghị Nginx/CDN/gateway.

> Trạng thái số đo: **baseline trước thay đổi chưa đo** (không có môi trường đo
> ổn định trước khi sửa). Số "sau" bên dưới là đo trên môi trường dev hiện tại;
> xem phần [Kết quả đo](#kết-quả-đo) để biết điều kiện và caveat.

---

## 1. Vấn đề gốc: vì sao 1 user chặn user khác?

Có hai nguyên nhân chính:

1. **Endpoint `async def` nhưng gọi code đồng bộ nặng trên event loop.**
   `POST /api/v1/exercises/{id}/questions/import` và
   `POST /api/v1/admin/users/import-excel` từng là `async def`, nhưng bên trong
   gọi `ImportParserService.parse_document`, `AnswerSolverService.solve_questions`
   và nhiều `db.commit()` đồng bộ. Trong lúc parse PDF/DOCX + gọi AI + ghi DB,
   event loop bị block, nên mọi request khác (kể cả health check/SSE) phải chờ.
   Đã đổi hai endpoint sang `def` để FastAPI chạy trong threadpool, và bọc phần
   nặng bằng `IMPORT_SEMAPHORE` (mặc định 2 slot/process).

2. **Truy vấn/ghi DB không có giới hạn và thiếu index.**
   Mỗi request mở một session; khi 30 request cùng vào, pool mặc định không đủ
   connection, hoặc query filter/join phải sequential scan. Đã thêm connection
   pool có timeout, `statement_timeout`, và migration index cho các bảng nóng.

Ngoài ra, PDF export và ETL ingest là hai tác vụ ngốn RAM/CPU; nếu không giới hạn
thì 30 user export/upload cùng lúc sẽ OOM container 2.5 GB. Đã thêm semaphore
riêng cho từng loại.

---

## 2. Thay đổi đã thực hiện

| Khu vực | File | Thay đổi |
|---|---|---|
| DB pool | `backend/app/core/database.py` | `pool_size=20`, `max_overflow=30`, `pool_timeout=10`, `pool_recycle=1800`, `pool_pre_ping=True`; PostgreSQL thêm `options=-c statement_timeout=30000`; guard SQLite |
| Resource limits | `backend/app/core/config.py`, `backend/app/core/resource_limits.py` | `PDF_EXPORT_CONCURRENCY=2`, `IMPORT_CONCURRENCY=2`, `ETL_CONCURRENCY=1`, `MAX_INGEST_BYTES=50MB`; các `BoundedSemaphore` process-local |
| PDF export | `backend/app/modules/exercise/routers/exercises.py` | Acquire semaphore tối đa 30s; quá hạn trả `503` với `ERR-EXE-PDF_BUSY`; không đổi response thành công |
| Import | `exercises.py`, `admin/routers/users.py` | Chuyển `async def` → `def` (threadpool), bọc `IMPORT_SEMAPHORE`; đọc file bằng `file.file.read()` |
| ETL | `backend/app/modules/document/services/document_ingest_service.py` | `ETL_SEMAPHORE`; check `MAX_INGEST_BYTES` trước `read_bytes()`; generator `iter_pages_from_pdf` render từng trang; bulk insert chunks theo batch 100 |
| Index | `backend/alembic/versions/f4b8c2d6e9a1_add_concurrency_indexes.py` | Index cho questions/answer_options/attempts/class_assignments/student_class/users/exercises |
| Docker | `docker-compose.yml`, `deploy/docker-compose.prod.yml`, `backend/Dockerfile` | `mem_limit` tổng 5 GB; healthcheck; `--limit-concurrency 128`; env pool/semaphore; `MALLOC_ARENA_MAX=2` |
| Nginx | `deploy/nginx/nginx.conf` | gzip JSON/JS/CSS; SSE tắt buffering + timeout 3600s; cache ảnh `/uploads/`, `/sgk-images/`; `client_max_body_size 50m` |
| Load test | `backend/scripts/load_test.py` | 30 worker httpx async, đo p50/p95/p99/RPS/error rate, in text + JSON |
| Docs | `docs/performance.md` | File này |

---

## 3. Connection pool & timeout

### 3.1 Công thức

```
max physical connections / process = DB_POOL_SIZE + DB_MAX_OVERFLOW
code default                       = 20 + 30 = 50
compose cho 30 user                = 20 + 30 = 50
```

- Code default và compose dev/prod đều đặt 20 + 30 = 50 để có headroom cho
  session ngắn hạn của middleware `X-Data-Version` trong lúc 30 request đang giữ
  session riêng.
- `pool_timeout=10s`: request chờ connection quá 10s sẽ fail fast thay vì treo.
- `pool_recycle=1800s`: tái tạo connection trước khi firewall/Postgres đóng idle.
- `pool_pre_ping=True`: kiểm tra connection còn sống trước khi dùng, tránh lỗi
  `server closed the connection unexpectedly` sau khi DB restart.
- PostgreSQL: `statement_timeout=30000ms` (env `DB_STATEMENT_TIMEOUT_MS`) để một
  query chậm không giữ connection vô hạn.

### 3.2 Với 1 worker

50 connection là đủ cho 30 user + middleware. Nếu vẫn thấy p99 tăng, kiểm tra
`pg_stat_activity` xem có session `idle in transaction` hoặc pool bị cạn không.
Với Postgres mặc định `max_connections=100`, 1 worker dùng tối đa 50 là an toàn;
2 worker sẽ là 100 — lúc đó phải tăng `max_connections` hoặc giảm pool.

---

## 4. Threadpool, semaphore và worker model

### 4.1 Threadpool

FastAPI chạy endpoint `def` (sync) trong AnyIO threadpool (mặc định 40 thread).
Vì vậy:

- DB query đồng bộ, reportlab, pypdfium2, `db.commit()` **không** block event loop.
- SSE và các endpoint `async def` khác vẫn được phục vụ trong lúc import/PDF chạy.
- Nhưng threadpool có giới hạn: nếu 30 import cùng chờ semaphore, 30 thread bị
  giữ. Đó là lý do `IMPORT_CONCURRENCY=2` và semaphore chỉ cho 2 import chạy;
  28 request còn lại chờ trong threadpool. Với 30 user, 40 thread là đủ; nếu
  tăng user, cần tăng `--limit-concurrency`/threadpool hoặc dùng queue.

### 4.2 Semaphore (process-local)

| Semaphore | Mặc định | Bảo vệ |
|---|---:|---|
| `PDF_EXPORT_SEMAPHORE` | 2 | reportlab + ảnh nhúng; quá 30s → 503 `ERR-EXE-PDF_BUSY` |
| `IMPORT_SEMAPHORE` | 2 | parse DOCX/PDF + AI answer solver + commit từng câu |
| `ETL_SEMAPHORE` | 1 | render PDF + VLM + embedding + bulk insert |

**Quan trọng:** đây là giới hạn **theo process**. Với N uvicorn worker, tổng
concurrency = N × giá trị cấu hình. Nếu scale lên 2 worker, PDF có thể chạy 4
cùng lúc và ETL 2 cùng lúc — cần kiểm tra lại RAM. Nếu cần giới hạn toàn cụm
(xuyên process), phải dùng Postgres advisory lock/Redis semaphore (chưa làm).

### 4.3 Worker model

- Dev: `uvicorn --reload` = 1 worker (reloader + server process).
- Prod 30 user: **1 worker** là đủ vì phần lớn thời gian là I/O (DB, VLM, AI API)
  và các tác vụ nặng đã được đẩy vào threadpool + semaphore.
- `--limit-concurrency 128`: chặn runaway connection; 30 SSE + 30 API vẫn còn
  headroom. Nếu mở nhiều tab/user, tăng lên 256.
- Scale lên 100+ user: tăng worker (2–4) hoặc chạy thêm backend replica sau
  Nginx; nhớ nhân pool/semaphore và kiểm tra `max_connections`.

---

## 5. RAM budget 5 GB

| Service | `mem_limit` | Ghi chú |
|---|---:|---|
| postgres | 1536 MB | shared_buffers + 30–60 connection + pgvector |
| backend | 2560 MB | Python + uvicorn + reportlab + pypdfium2 + ETL |
| frontend | 896 MB (prod) / 1024 MB (dev) | Node/Vite preview; thực tế thấp hơn |
| nginx | 128 MB (prod) | reverse proxy; cache static nằm trên disk |
| **Tổng** | **5120 MB** | chừa ~1 GB cho host OS/Docker |

- Docker OOM-kill container vượt `mem_limit`; backend bị kill sẽ làm rơi SSE
  stream và job ingest đang chạy.
- `MALLOC_ARENA_MAX=2` trong Dockerfile giảm phân mảnh RSS khi threadpool chạy
  nhiều tác vụ blocking.
- Nếu tăng backend lên 3 GB, phải giảm postgres/frontend tương ứng để tổng ≤ 5 GB.

---

## 6. Nginx / CDN / API gateway

### 6.1 Nginx

Với 30 user, chỉ cần **1 Nginx reverse proxy + 1 backend worker**. Không cần API
gateway (Kong/APISIX/Envoy) — thêm một tầng nữa chỉ làm tăng latency và RAM.

Cấu hình hiện tại (`deploy/nginx/nginx.conf`):

- `gzip on` cho JSON/JS/CSS; **không** gzip `text/event-stream`.
- SSE `/api/v1/sync/stream` và `/api/v1/admin/monitoring/stream`:
  `proxy_buffering off`, `proxy_read_timeout 3600s`, `proxy_http_version 1.1`.
- `client_max_body_size 50m` khớp `MAX_INGEST_BYTES`.
- `/uploads/` và `/sgk-images/`: `Cache-Control: public, max-age=604800, immutable`
  để browser cache 7 ngày.
- Frontend prod dùng `VITE_API_BASE_URL=/api` nên ảnh có thể có URL
  `/api/uploads/...` hoặc `/api/sgk-images/...`; Nginx rewrite các prefix này về
  `/uploads/...` / `/sgk-images/...` trước khi proxy/cache.
- `proxy_request_buffering off` cho API upload lớn (stream thay vì buffer).
- Rate limit: `limit_req_zone` phải khai báo ở http context (file này là server
  block trong `conf.d`). App đã rate-limit login trong `app/core/rate_limit.py`.
  Nếu cần edge rate limit, thêm zone vào `/etc/nginx/nginx.conf` rồi bật
  `limit_req` trong `/api/`.

### 6.2 CDN

- **Nên** dùng CDN cho static assets: JS/CSS build, `/uploads/`, `/sgk-images/`.
  Các file này gần như bất biến theo tên, cache dài ngày.
- **Không** cache API cá nhân (`Authorization`, cookie, `/api/v1/...`), đặc biệt
  các endpoint trả đề thi/đáp án. Nếu dùng CDN, chỉ cache theo path static và
  bypass mọi request có `Authorization`.
- SSE không đi qua CDN cache; cần CDN/proxy hỗ trợ streaming hoặc bypass.

### 6.3 Gateway

Không cần cho 30 user. Khi lên multi-tenant/1000+ user mới cân nhắc API gateway
để authn/authz tập trung, rate limit, observability. Ở quy mô này Nginx + app
middleware là đủ.

---

## 7. Kết quả đo

### 7.1 Cách chạy

```bash
cd backend
..\.venv\Scripts\python.exe scripts\load_test.py \
  --base-url http://localhost:8000 \
  --users 30 --requests-per-user 20 \
  --phone 0999000002 --password 'Teacher@1234'
```

Script login một lần, chạy 30 worker đồng thời, mỗi worker luân phiên:

- `GET /api/v1/exercises?page_size=6`
- `GET /api/v1/assignments`

Kết quả gồm p50/p95/p99, RPS, tổng request, error rate, status count, per-endpoint
và JSON report (`--json-out` để ghi file).

### 7.2 Trước khi nâng pool (tái hiện lỗi)

Đo trên máy dev, backend container **1 GB**, 1 uvicorn worker, pool **10 + 20 = 30**,
30 request đồng thời:

| Workload | RPS | p50 | p95 | p99 | Error |
|---|---:|---:|---:|---:|---:|
| 30 × 10 = 300 | 12.91 | 384 ms | **10 218 ms** | **10 266 ms** | 0% |

Nguyên nhân: mỗi request giữ 1 session, middleware `X-Data-Version` cần thêm 1
session; 30 request làm cạn pool 30, tất cả chờ `pool_timeout=10s`. Đây chính là
hiện tượng "một user giữ BE làm user khác bị chặn" ở tầng connection pool.

### 7.3 Sau khi nâng pool + serialize cache version (dev)

Cùng máy dev, backend container **1 GB**, 1 worker, pool **20 + 30 = 50**,
`get_cached_version_snapshot` chỉ cho 1 thread tính khi cache miss:

| Workload | Wall | RPS | p50 | p95 | p99 | Error |
|---|---:|---:|---:|---:|---:|---:|
| 30 × 20 = 600 | 7.335 s | **81.80** | 349 ms | 509 ms | **552 ms** | **0%** |
| 30 × 50 = 1 500 | 18.371 s | **81.65** | 369 ms | 476 ms | **520 ms** | **0%** |

- 600 request: 600×200, 0 exception.
- 1 500 request: 1 500×200, 0 exception.
- Per-endpoint 1 500 request: `/exercises` p95 478 ms / p99 520 ms;
  `/assignments` p95 466 ms / p99 513 ms.
- RAM lúc chạy 1 500 request (docker stats): backend **273.5 MB**, postgres
  **252.4 MB**, frontend **106.2 MB**; tổng stack SmartLMS ~**632 MB**, rất xa
  ngưỡng 5 GB. CPU backend ~122% (đa nhân), Postgres ~24%.

**Caveat:** load test dùng cùng một tài khoản teacher (30 HTTP worker đồng thời,
không phải 30 user session riêng), chạy trên dev container 1 GB và Postgres dev
dùng chung. Đây là bằng chứng concurrency của app, không phải benchmark production
tuyệt đối. Cần đo lại trên prod compose (backend 2.5 GB, Postgres riêng) để có số
chính thức; kỳ vọng tương đương hoặc tốt hơn.

### 7.4 Nếu vẫn thấy p99 cao

- `pg_stat_activity` có nhiều session `idle in transaction` không.
- Pool có bị cạn không (`DB_POOL_SIZE`/`DB_MAX_OVERFLOW`); xem lại công thức 20 + 30.
- Query chậm trong log Postgres (`log_min_duration_statement`).
- SSE có chiếm connection không (SSE dùng session ngắn hạn, không giữ pool).
- `X-Data-Version` cache có bị miss liên tục không (TTL 2s, có `_compute_lock`).

---

## 8. Database indexes

Migration: `backend/alembic/versions/f4b8c2d6e9a1_add_concurrency_indexes.py`
(down_revision = `e7a9c1d3f5b2`, head monitoring hiện tại).

Chạy:

```bash
cd backend
..\.venv\Scripts\python.exe -m alembic upgrade head
```

Index thêm:

- `questions(exercise_id, status)`
- `answer_options(question_id)`
- `student_exercise_attempts(student_id, assignment_id, is_finished)`
- `class_assignments(class_id, status)`
- `class_assignments(exercise_id, status)`
- `student_class(student_id, class_id, status)`
- `users(phone)` (đã có unique constraint; index này giữ tên ổn định nếu constraint bị bỏ)
- `exercises(subject_id, created_by, status)`

Migration dùng `if_not_exists=True` nên an toàn nếu index đã tồn tại. Không chạy
trên SQLite test (test dùng `Base.metadata.create_all`), nên không ảnh hưởng test.

---

## 9. Frontend đã tối ưu trong task này

1. **Request dedupe/cancel:** `studentTakingApi.getAssignmentTaking` nhận
   `signal` + `force`; trang làm bài dùng `AbortController` và hủy request khi
   unmount/StrictMode. Refetch sau khi start attempt dùng `force: true` để không
   nhận cache preview.
2. **Lazy route/code-split:** `App.jsx` dùng `React.lazy` + `Suspense` cho toàn bộ
   trang teacher/student/admin. Bundle chính giảm từ ~2.5 MB (700 KB gzip) xuống
   **330.91 KB (101.91 KB gzip)**; trang nặng như editor công thức/PDF chỉ tải khi
   mở. `AdminMonitoringPage` là chunk riêng 27.9 KB (8.6 KB gzip).
3. **SSE:** dashboard monitoring dùng `fetch` + `ReadableStream` (Bearer header,
   không query token), parser chịu được chunk cắt giữa event, reconnect backoff
   1s→2s→5s→10s, fallback polling 5s sau 3 lần lỗi, cleanup khi unmount.
4. **Debounce:** filter route của bảng request debounce 400ms; filter status gọi
   lại ngay khi đổi.
5. **SEO:** `index.html` có title/description/robots/OG/Twitter/JSON-LD;
   `robots.txt` + `sitemap.xml`; hook `usePageMeta` set canonical/title/robots
   theo route; trang làm bài và khu vực private set `noindex,nofollow`.
6. **Không cache API cá nhân:** Nginx chỉ cache `/uploads/`, `/sgk-images/`,
   JS/CSS build; mọi `/api/v1/*` có `Authorization` đi thẳng backend.

**Còn khuyến nghị (chưa làm):**
- React Query/SWR cache cho danh sách exercises/assignments (hiện vẫn gọi lại khi
  filter/route thay đổi).
- `loading="lazy"` cho ảnh câu hỏi/SGK nếu một đề có nhiều ảnh.
- Đóng SSE khi tab ẩn (`visibilitychange`) nếu không cần realtime.

---

## 10. Việc cần làm tiếp

- [x] Apply migration index trên dev (`alembic upgrade head` → `f4b8c2d6e9a1`).
- [x] Đo load test 30 user trên dev; ghi số vào mục 7.3.
- [ ] Đo lại trên prod compose (backend 2.5 GB, Postgres riêng) để có số chính thức.
- [ ] Theo dõi `pg_stat_activity`, slow query log, RAM từng container.
- [ ] Nếu scale > 30 user: tăng worker/replica, nhân pool/semaphore, kiểm tra
      `max_connections`; cân nhắc Redis/Postgres advisory lock cho semaphore
      toàn cụm.
- [ ] Nếu p99 vẫn cao: điều tra N+1 ở assignment feed và query list exercises.
