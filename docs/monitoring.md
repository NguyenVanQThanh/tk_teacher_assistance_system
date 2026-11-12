# Realtime API Monitoring — SmartLMS

Module giám sát request API theo thời gian thực, dành cho Admin. Thiết kế ưu tiên
**nhẹ, bounded RAM, không làm chậm request**; phù hợp mục tiêu 30 user đồng thời
trên stack 5 GB.

---

## 1. Kiến trúc

```text
HTTP request
   │
   ├─ MonitoringMiddleware (app/modules/monitoring/middleware.py)
   │    - X-Request-ID (nhận hoặc sinh mới, trả lại response header)
   │    - method, route template, path, status, latency, request/response bytes
   │    - user_ref = sha256(JWT sub)[:12], ip_ref = sha256(client host)[:12]
   │    - bỏ qua static/docs/OPTIONS/SSE stream
   │
   ├─ MetricsCollector (collector.py, threading.Lock)
   │    - ring buffer 5.000 request gần nhất
   │    - pending queue 1.000 request chờ ghi DB
   │    - snapshot: totals, error rate, p50/p95/p99, status counts,
   │      top routes, slowest, series 10s/1m, alerts, active users
   │
   ├─ Flush loop (main.py lifespan, mỗi 5s)
   │    - bulk INSERT vào api_request_metrics
   │    - purge retention 7 ngày mỗi giờ
   │
   └─ Admin router (/api/v1/admin/monitoring/*)
        - summary / requests / health / reset
        - SSE stream (fetch + Bearer header, không query token)
```

Lý do dùng custom module thay vì Prometheus/OpenTelemetry: quy mô 30 user không
cần thêm container/metrics backend; ring buffer + Postgres đủ, ít RAM, triển khai
đơn giản. Nếu sau này cần Prometheus, có thể thêm endpoint `/metrics` từ chính
collector này.

---

## 2. API

Tất cả endpoint yêu cầu role **Admin** (Bearer JWT).

| Method | Path | Mô tả |
|---|---|---|
| GET | `/api/v1/admin/monitoring/summary?window_seconds=300` | Snapshot tổng hợp |
| GET | `/api/v1/admin/monitoring/requests?limit=100&route=&status=` | Request gần nhất |
| GET | `/api/v1/admin/monitoring/stream?window_seconds=300` | SSE, mỗi 2s một event |
| GET | `/api/v1/admin/monitoring/health` | Buffer/pending/persist status |
| POST | `/api/v1/admin/monitoring/reset` | Xóa buffer in-memory (dev/test) |

### Summary shape

```json
{
  "window_seconds": 300,
  "generated_at": "2026-11-13T04:21:00+00:00",
  "totals": {
    "requests": 2121,
    "errors": 0,
    "error_rate": 0.0,
    "requests_per_sec": 7.07,
    "requests_per_minute": 424,
    "request_bytes": 0,
    "response_bytes": 0,
    "avg_latency_ms": 282
  },
  "error_rate": 0.0,
  "rps": 7.07,
  "req_per_minute": 424,
  "active_users": 3,
  "throughput": {"requests_per_sec": 7.07, "requests_per_minute": 424, "bytes_per_sec": 0},
  "latency_ms": {"p50": 282, "p95": 417, "p99": 454, "avg": 282, "min": 3, "max": 509},
  "status_counts": {"1xx": 0, "2xx": 2121, "3xx": 0, "4xx": 0, "5xx": 0, "other": 0},
  "top_routes": [
    {"route": "/api/v1/assignments", "count": 1052, "errors": 0, "error_rate": 0, "avg_ms": 251, "p95_ms": 366}
  ],
  "slowest": [
    {"request_id": "...", "method": "GET", "route": "/api/v1/exercises", "status_code": 200, "duration_ms": 509, "started_at": "...", "finished_at": "..."}
  ],
  "series": [
    {"timestamp": "2026-11-13T04:20:00+00:00", "bucket_seconds": 10, "requests": 120, "errors": 0, "p95_ms": 420, "avg_ms": 250}
  ],
  "alerts": [],
  "buffer_size": 2121,
  "pending": 0,
  "persist_enabled": true
}
```

**Error rate chỉ tính 5xx** (server errors). 4xx vẫn nằm trong `status_counts` và
`top_routes[].count` để phân biệt lỗi client (401/404/422) với lỗi hệ thống.

### SSE

- `Content-Type: text/event-stream`
- Mỗi event: `data: <summary json>\n\n`
- Header: `Cache-Control: no-cache, no-store`, `X-Accel-Buffering: no`
- Dashboard dùng `fetch()` + `ReadableStream` vì `EventSource` không gắn được
  `Authorization` header; không truyền token qua query string.
- Reconnect backoff phía FE: 1s → 2s → 5s → 10s; fallback polling 5s sau 3 lỗi.

---

## 3. Lưu trữ & retention

Bảng `api_request_metrics` (migration `e7a9c1d3f5b2`):

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `metric_id` | UUID | PK |
| `request_id` | varchar(64) | correlation ID |
| `method`, `route`, `path` | varchar | route template, không chứa UUID thật |
| `status_code` | int | |
| `duration_ms` | float | |
| `request_bytes`, `response_bytes` | int | từ Content-Length, không đọc body |
| `user_ref`, `ip_ref` | varchar(64) | hash 12 ký tự, không lưu PII thô |
| `is_error` | bool | `status_code >= 500` |
| `created_at` | timestamptz | index |

Retention mặc định **7 ngày** (`MONITORING_RETENTION_DAYS`), purge mỗi giờ.
Buffer in-memory 5.000 request; pending 1.000 request. Mọi cấu trúc đều bounded,
không tăng RAM vô hạn.

---

## 4. Cấu hình

| Env | Default | Ý nghĩa |
|---|---:|---|
| `MONITORING_PERSIST_ENABLED` | `1` | `0` để tắt ghi DB (test/dev) |
| `MONITORING_BUFFER_SIZE` | `5000` | ring buffer |
| `MONITORING_PENDING_LIMIT` | `1000` | queue chờ flush |
| `MONITORING_FLUSH_INTERVAL_SECONDS` | `5` | chu kỳ flush |
| `MONITORING_RETENTION_DAYS` | `7` | retention DB |
| `MONITORING_PURGE_INTERVAL_SECONDS` | `3600` | chu kỳ purge |
| `MONITORING_SERIES_BUCKET_SECONDS` | `10` | bucket chart (window > 600s dùng 60s) |
| `MONITOR_ALERT_P95_MS` | `1000` | ngưỡng alert p95 |
| `MONITOR_ALERT_ERROR_RATE` | `0.05` | ngưỡng alert error rate (5xx) |

---

## 5. Dashboard

Route: **`/admin/monitoring`** (menu “Giám sát hệ thống”).

- 6 KPI: tổng request, request/phút, error rate, active users, p95, p99.
- Alert banner warning/critical.
- Chart SVG thuần: requests, errors, p95 (không thêm chart dependency).
- Phân bố status 2xx/3xx/4xx/5xx.
- Top routes, slowest requests, recent requests có filter route/status.
- Nút Refresh + chọn cửa sổ 1/5/15/60 phút.
- Trạng thái Live/Reconnecting/Offline.

---

## 6. Vận hành & giới hạn

- **1 worker**: metrics in-memory đầy đủ. Nếu chạy nhiều worker/replica, mỗi
  process có collector riêng; dashboard chỉ thấy metrics của worker đang phục vụ
  request SSE. Với 30 user, khuyến nghị 1 worker.
- **Không log body**: chỉ đo Content-Length; không đọc nội dung bài làm/đáp án.
- **Không lưu token**: chỉ hash `sub`; IP hash; route template thay vì UUID.
- **SSE qua Nginx**: đã cấu hình `proxy_buffering off`, timeout 3600s; Cloudflare
  phải bypass cache/buffering cho `/api/*`.
- **Alert threshold**: đọc env mỗi lần snapshot, có thể đổi không cần restart.
- **Reset**: chỉ admin; dùng cho dev/test, không cần trong production.

---

## 7. Kiểm thử

```bash
cd backend
..\.venv\Scripts\python.exe -m pytest tests/test_monitoring.py -q
```

Coverage: X-Request-ID, admin-only, filter, percentile/alert, SSE first event,
bảng SQLite, flush/requeue, normalize path, error rate chỉ 5xx.
