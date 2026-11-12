# Deploy — hướng dẫn đưa hệ thống lên production

Thư mục này chứa toàn bộ cấu hình cần để deploy, tách biệt với môi trường dev ở repo root.

## Cấu trúc

```
deploy/
├── README.md                        # file này
├── PLAN-R2-STORAGE.md               # kế hoạch chuyển lưu file upload sang Cloudflare R2 (S3-compatible)
├── docker-compose.prod.yml          # compose cho production
├── .env.prod.example                # template biến môi trường prod -> copy thành .env.prod
├── nginx/
│   └── nginx.conf                   # reverse proxy (service nginx, chỉ chạy với --profile proxy)
├── docker/
│   └── Dockerfile.frontend.prod     # image prod cho frontend (build Vite + vite preview)
├── ci/
│   ├── ci.yml                       # CI đầy đủ -> copy vào .github/workflows/ci.yml
│   └── deploy.yml                   # CD tự động (GHCR + SSH) -> copy vào .github/workflows/deploy.yml
└── scripts/
    └── deploy.sh                    # script deploy thủ công trên server Linux
```

## khác biệt với bản dev (`docker-compose.yml` ở root)

| | Dev (root) | Prod (`deploy/`) |
|---|---|---|
| Source code | mount trực tiếp `./backend`, `./frontend` (sửa là thấy ngay, `--reload`) | baked sẵn trong image, không mount |
| Port công khai | 5432, 8000, 3000 đều mở | chỉ nginx mở 80 (khi bật `--profile proxy`), DB/API nội bộ |
| Secret | hardcode trong compose | đọc từ `deploy/.env.prod` (không commit) |
| Build time | chậm (trước đây còn torch qua marker-pdf) | nhanh — `marker-pdf`/torch đã bị loại khỏi `backend/requirements.txt` |

## Lưu trữ file upload — Cloudflare R2

Vì người dùng vừa upload vừa tải file về (egress), hệ thống sẽ lưu upload trên
**Cloudflare R2** (API tương thích S3, egress $0, 10GB free) thay vì đĩa EC2/AWS S3.
Xem kế hoạch + checklist implement ở [PLAN-R2-STORAGE.md](PLAN-R2-STORAGE.md);
các biến `R2_*` cần điền có sẵn trong [.env.prod.example](.env.prod.example).

## Các bước deploy lần đầu trên server

```bash
# 1. Clone repo lên server
 git clone <repo-url> /opt/smartlms && cd /opt/smartlms

# 2. Tạo file env production (KHÔNG commit file này)
cp deploy/.env.prod.example deploy/.env.prod
nano deploy/.env.prod        # điền mật khẩu DB, SECRET_KEY, MISTRAL_API_KEY, GEMINI_API_KEY...

# 3. Build & chạy (từ repo root)
bash deploy/scripts/deploy.sh                 # không có proxy, mở thẳng các port nội bộ
# hoặc bật reverse proxy qua nginx (khuyến nghị):
bash deploy/scripts/deploy.sh --proxy         # chỉ cần mở port 80 trên firewall
```

Lúc đó:
- Frontend: `http://<server-ip>/` (qua nginx) hoặc `http://<server-ip>:3000`
- API: `http://<server-ip>/api/...` (qua nginx, đã strip prefix) — frontend được build với `VITE_API_BASE_URL=/api`
- Health check: `curl http://<server-ip>/health`

Nếu **không** dùng nginx proxy thì đổi `VITE_API_BASE_URL=http://<server-ip>:8000` trong `.env.prod` và publish port 8000/3000 trong compose.

## Cập nhật khi có code mới

```bash
cd /opt/smartlms
git pull
bash deploy/scripts/deploy.sh --proxy        # build lại image rồi up -d
# xem log: docker logs -f smartlms_backend
```

## Thiết lập CI/CD tự động (GitHub Actions)

1. Copy 2 file CI vào đúng chỗ:
   ```bash
   cp deploy/ci/ci.yml     .github/workflows/ci.yml      # (đè bản CI cũ, thêm docker build smoke test)
   cp deploy/ci/deploy.yml .github/workflows/deploy.yml
   ```
2. Vào **Settings > Secrets and variables > Actions** của repo, tạo các secret cho `deploy.yml`:
   - `DEPLOY_HOST` — IP/hostname server
   - `DEPLOY_USER` — user SSH (vd: `ubuntu`)
   - `DEPLOY_SSH_KEY` — private key (public key đã thêm vào `~/.ssh/authorized_keys` của server)
   - `DEPLOY_PATH` — đường dẫn project trên server (vd: `/opt/smartlms`)
3. Mỗi lần push lên `main`: CI chạy test/build → CD build & push image lên GHCR → SSH sang server `docker compose pull && up -d`.

## Lưu ý bảo mật

- `deploy/.env.prod` **không được commit** (đã thêm vào `.gitignore`).
- Đổi `SECRET_KEY` và mật khẩu DB mặc định (`123456` ở bản dev) trước khi lên production.
- Prod compose không publish port 5432 ra ngoài; chỉ backend mới kết nối được với Postgres qua network nội bộ của compose.
- Ảnh upload lưu ở named volume `backend_uploads` — nhớ backup volume này cùng với `postgres_data`.
