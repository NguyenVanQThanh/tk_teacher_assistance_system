# Deploy — hướng dẫn đưa hệ thống lên production

Thư mục này chứa toàn bộ cấu hình cần để deploy, tách biệt với môi trường dev ở repo root.

## Cấu trúc

```
deploy/
├── README.md                        # file này
├── PLAN-R2-STORAGE.md               # kế hoạch chuyển lưu file upload sang Cloudflare R2 (S3-compatible)
├── docker-compose.prod.yml          # compose cho production — build từ source (cần repo trên server)
├── docker-compose.images.yml        # compose image-only — pull từ GHCR, KHÔNG cần source trên server
├── .env.prod.example                # template biến môi trường prod -> copy thành .env.prod
├── nginx/
│   └── nginx.conf                   # reverse proxy (service nginx, chỉ chạy với --profile proxy)
├── docker/
│   └── Dockerfile.frontend.prod     # image prod cho frontend (build Vite + vite preview)
├── ci/
│   └── ci.yml                       # CI đầy đủ -> copy vào .github/workflows/ci.yml
│                                    # (CD deploy đã nằm sẵn ở .github/workflows/deploy.yml)
└── scripts/
    ├── deploy.sh                    # script deploy thủ công trên server Linux (build từ source)
    ├── build-push.ps1               # build + push 2 image lên GHCR từ máy Windows
    └── deploy-remote.ps1            # deploy từ máy Windows: scp config + sgk_data rồi pull/up
```

## khác biệt với bản dev (`docker-compose.yml` ở root)

| | Dev (root) | Prod (`deploy/`) |
|---|---|---|
| Source code | mount trực tiếp `./backend`, `./frontend` (sửa là thấy ngay, `--reload`) | baked sẵn trong image, không mount |
| Port công khai | 5432, 8000, 3000 đều mở | chỉ nginx mở 80 (khi bật `--profile proxy`), DB/API nội bộ |
| Secret | hardcode trong compose | đọc từ `deploy/.env.prod` (không commit) |
| Build time | chậm (trước đây còn torch qua marker-pdf) | nhanh — `marker-pdf`/torch đã bị loại khỏi `backend/requirements.txt` |

## Kiểm tra server trước khi deploy (IP / port / registry)

Chạy trên **server** (Linux):

```bash
# 1) IP public vs IP của interface -> phát hiện NAT/CGNAT
curl -4 -s https://ifconfig.me; echo
ip -4 -o addr show scope global | awk '{print $2, $4}'

# 2) Có gì đang listen 80/443 + firewall
sudo ss -tlnp | grep -E ':(80|443)\b' || echo "chưa có gì listen 80/443"
sudo ufw status verbose 2>/dev/null || sudo nft list ruleset 2>/dev/null | head -40

# 3) Server pull được image từ đâu?
curl -sS -o /dev/null -w 'ghcr: %{http_code}\n'      https://ghcr.io/v2/
curl -sS -o /dev/null -w 'dockerhub: %{http_code}\n' https://registry-1.docker.io/v2/

# 4) DNS (nếu đã có domain)
dig +short A example.com
```

Chạy từ **máy khác** (kiểm tra port có thật sự mở từ Internet, không chỉ local):

```powershell
Test-NetConnection <IP> -Port 80
Test-NetConnection <IP> -Port 443
curl.exe -sS -m 5 -o NUL -w "%{http_code}`n" http://<IP>/
```

Cách đọc kết quả:

| Kết quả | Nghĩa | Bước tiếp |
|---|---|---|
| IP public **=** IP interface | Server có public IP trực tiếp | Mở 80/443 (ufw + security group) → nginx + domain + TLS |
| IP public **≠** IP interface, hoặc IP dạng `100.64.x.x` | Đang sau NAT/CGNAT | Bắt buộc **tunnel** (Cloudflare Tunnel) — không mở port được |
| `ss` thấy listen nhưng `Test-NetConnection` fail | Firewall/security group chặn | Mở inbound 80/443 ở cloud provider, rồi `sudo ufw allow 80,443/tcp` |
| `ghcr: 200` | Pull được image | OK |
| `ghcr: 401` | Bình thường (cần auth) | `docker login ghcr.io` nếu package private |

### Nhánh A — server có public IP

```bash
sudo ufw allow 80,443/tcp          # + mở inbound 80/443 ở security group của cloud
# DNS: A record  app.example.com -> <IP>
```

TLS: hoặc bật proxy Cloudflare (bản ghi cam) và để Cloudflare terminate TLS, hoặc thêm
`listen 443 ssl` + certbot vào `deploy/nginx/nginx.conf`. Hiện file này chỉ `listen 80`.

### Nhánh B — Cloudflare Tunnel (không mở port, không cần IP tĩnh)

Điều kiện duy nhất: domain đã trỏ nameserver về Cloudflare. Không cần mở port, không cần
port-forward router, không cần certbot — Cloudflare lo TLS ở edge, `cloudflared` chỉ mở
kết nối **outbound** từ server ra ngoài.

**1. Tạo tunnel** — Zero Trust dashboard → **Networks → Tunnels → Create a tunnel** →
chọn **Cloudflared** → đặt tên `smartlms` → copy **token**.

**2. Thêm Public Hostname** trong tunnel vừa tạo:

| Trường | Giá trị |
|---|---|
| Subdomain | `app` |
| Domain | domain của bạn |
| Service · Type | `HTTP` |
| Service · URL | `nginx:80` |

`nginx` là tên service trong compose — cloudflared resolve qua DNS nội bộ của Docker,
không đi vòng qua host, nên không phụ thuộc port nào trên máy.

**3. Điền `deploy/.env.prod` trên server:**

```
CLOUDFLARE_TUNNEL_TOKEN=eyJhIjoi...
NGINX_BIND=127.0.0.1
NGINX_PORT=8080
```

**4. Deploy:**

```powershell
pwsh deploy/scripts/deploy-remote.ps1 -Server <ip> -User thanhnvq -Tag <tag> -Tunnel
```

`-Tunnel` bật profile `tunnel`, và nginx tự bật theo (nginx nằm trong cả profile
`proxy` lẫn `tunnel`).

**5. Kiểm tra:**

```bash
curl -I https://app.example.com/health          # 200 + server: cloudflare
docker logs -f smartlms_cloudflared             # "Registered tunnel connection"
```

Luồng: browser → Cloudflare edge (HTTPS) → tunnel (outbound) → `nginx:80` → frontend/backend.

Lưu ý khi chạy qua Cloudflare:

- `NGINX_BIND=127.0.0.1` chỉ để port 8080 nghe trên loopback (debug `curl localhost:8080/health`);
  tunnel vẫn vào được qua network nội bộ compose.
- **SSE**: Cloudflare cắt kết nối rảnh sau ~100s. Backend đã gửi comment `: keep-alive`
  mỗi 15s ([sync.py](../backend/app/modules/exercise/routers/sync.py)) nên stream không đứt.
- Upload: Cloudflare Free giới hạn 100 MB/request, app giới hạn 50 MB (`MAX_INGEST_BYTES`) — an toàn.
- Token là secret, chỉ nằm trong `.env.prod` (gitignored). Ai vào được Docker trên server
  đều đọc được, nhưng người đó đã là root rồi.
- Muốn chạy `cloudflared` trên host thay vì container: `cloudflared service install <token>`
  và trỏ hostname về `http://127.0.0.1:8080`.

### Nhánh C — Quick tunnel: 0đ, không cần domain (chỉ để demo)

Cloudflare cấp một URL ngẫu nhiên `https://<random>.trycloudflare.com`, không cần domain,
không cần token, không cần tài khoản:

```powershell
pwsh deploy/scripts/deploy-remote.ps1 -Server <ip> -User thanhnvq -Tag <tag> -Quick
```

Script tự bật nginx + `cloudflared-quick` và in ra URL. Hoặc làm tay trên server:

```bash
docker compose --project-directory . --env-file deploy/.env.prod \
  -f deploy/docker-compose.images.yml --profile quick up -d
docker logs smartlms_cloudflared_quick 2>&1 | grep -o 'https://[a-z0-9-]*\.trycloudflare\.com'
```

| Ưu | Nhược |
|---|---|
| 0đ, chạy trong 2 phút | URL **đổi mỗi lần restart** container |
| HTTPS sẵn, không cần DNS | Cloudflare rate-limit, không đảm bảo uptime |
| Test được SSE/upload qua Internet thật | Không đưa cho giáo viên dùng thật được |

Dùng đúng mục đích: demo, kiểm tra tunnel + SSE trước khi bỏ tiền mua domain.

### Trường hợp port 80 đã bị chiếm (đã có nginx trên host)

Kiểm tra trước khi deploy:

```bash
sudo ss -tlnp | grep -E ':(80|443)\b'          # ai đang giữ port 80?
sudo systemctl status nginx --no-pager -l | head -20
sudo nginx -T 2>/dev/null | grep -nE '^\s*(server_name|listen|root|proxy_pass)' | head -40
sudo docker ps --format '{{.Names}}\t{{.Ports}}'   # hay là container?
```

Nếu port 80 đã có chủ, **đừng** publish `80:80` (container sẽ không start được:
`bind: address already in use`). Chọn một trong hai:

| Cách | Làm gì |
|---|---|
| Giữ nginx host | Đặt `NGINX_BIND=127.0.0.1`, `NGINX_PORT=8080`; thêm `location / { proxy_pass http://127.0.0.1:8080; }` vào server block của domain trong nginx host |
| Bỏ nginx host | `sudo systemctl disable --now nginx`, rồi để `NGINX_BIND=0.0.0.0`, `NGINX_PORT=80` |

Lưu ý: Docker publish port sẽ **bỏ qua ufw** (Docker chèn rule vào chain `DOCKER`).
Nên `ufw deny 80` không có nghĩa là port 80 kín — muốn chắc thì bind `127.0.0.1`.

## Deploy image-only — server KHÔNG cần clone repo

`docker-compose.prod.yml` vẫn `build:` từ source, nên nó bắt buộc có repo trên server.
Muốn deploy container đã build sẵn, dùng **`docker-compose.images.yml`**: mọi service
dùng `image:` (pull từ GHCR) thay vì `build:`. Server chỉ nhận **file config + data**,
không nhận source code.

### Trên server cần đúng 5 thứ

```
/opt/smartlms/
├── deploy/docker-compose.images.yml   # ~7 KB
├── deploy/.env.prod                   # secrets — tự tạo trên server, KHÔNG commit
├── deploy/nginx/nginx.conf            # ~8 KB (chỉ khi dùng --profile proxy)
├── postgres-init/01_extensions.sql    # tạo extension unaccent + vector cho volume mới
└── sgk_data/                          # 2.1 GB — gitignored, phải upload riêng
    ├── vectors.dump   (72 MB)
    └── images.tar     (2.0 GB)
```

Backend tự chạy `alembic upgrade head` + load SGK trong `backend/docker/entrypoint.sh`,
nên **không cần chạy migration tay** trên server.

### Bước 1 — build & push image (máy dev hoặc CI)

Trên Windows dùng script (tự lowercase owner, tự lấy tag từ `git rev-parse`):

```powershell
pwsh deploy/scripts/build-push.ps1                              # build + push cả 2 image
pwsh deploy/scripts/build-push.ps1 -Tag v1.2.0 -Platform linux/amd64
pwsh deploy/scripts/build-push.ps1 -NoPush                      # chỉ build để test
```

Hoặc làm tay:

```bash
# Tên image GHCR phải VIẾT THƯỜNG, nếu không docker báo
# "invalid reference format: repository name must be lowercase"
IMAGE_OWNER=nguyenvanqthanh        # = owner GitHub, lowercase
TAG=$(git rev-parse --short HEAD)

docker build -t ghcr.io/$IMAGE_OWNER/smartlms-backend:$TAG ./backend
docker build -f deploy/docker/Dockerfile.frontend.prod \
  --build-arg VITE_API_BASE_URL=/api \
  -t ghcr.io/$IMAGE_OWNER/smartlms-frontend:$TAG ./frontend

docker push ghcr.io/$IMAGE_OWNER/smartlms-backend:$TAG
docker push ghcr.io/$IMAGE_OWNER/smartlms-frontend:$TAG
```

Điền `BACKEND_IMAGE` / `FRONTEND_IMAGE` (không kèm tag) vào `deploy/.env.prod`;
`IMAGE_TAG` do script/CI truyền vào.

### Bước 2 — deploy từ máy dev (Windows)

```powershell
pwsh deploy/scripts/deploy-remote.ps1 -Server <ip> -User ubuntu -Tag <tag> -Proxy
# đang dùng Cloudflare Tunnel thì thay -Proxy bằng -Tunnel
```

Script làm: `mkdir` thư mục → `scp` compose + nginx.conf + 01_extensions.sql →
kiểm tra `.env.prod` trên server → `scp sgk_data` (bỏ qua nếu đã có) →
`docker compose pull && up -d` → chờ backend `healthy`.

Lần đầu, tạo `.env.prod` trên server trước:

```bash
scp deploy/.env.prod.example ubuntu@<ip>:/opt/smartlms/deploy/.env.prod
ssh ubuntu@<ip> "nano /opt/smartlms/deploy/.env.prod"   # DB password, SECRET_KEY, API key, R2_*
```

Hoặc đặt file thật vào `deploy/.env.prod` ở máy dev rồi chạy script (script tự copy).

Các cờ hữu ích: `-SkipData` (server đã có sgk_data), `-SkipUpload` (chỉ pull/up),
`-SkipNginx`, `-RegistryUser/-RegistryToken` (package private), `-Port`, `-SshKey`.

### Bước 3 — rollback

```powershell
pwsh deploy/scripts/deploy-remote.ps1 -Server <ip> -Tag <tag-cu> -SkipData -SkipUpload
```

Vì tag là bất biến (CI dùng full SHA), rollback chỉ là deploy lại tag cũ — không build lại.

## Lưu trữ file upload — local hay Cloudflare R2

Một biến môi trường quyết định nơi lưu file upload, **không cần sửa code, không đổi schema**:

```
STORAGE_BACKEND=local     # mặc định: đĩa container, volume backend_uploads
STORAGE_BACKEND=r2        # Cloudflare R2 (alias: cloud, s3)
```

| | `local` | `r2` |
|---|---|---|
| File nằm ở | volume `backend_uploads` | bucket R2 |
| URL trả về | `/uploads/questions/x.png` (nginx/StaticFiles phục vụ) | `https://files.<domain>/questions/x.png` |
| Cần credential | không | `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`, `R2_PUBLIC_BASE_URL` |
| Backup | volume `backend_uploads` | bucket R2 (bật versioning/lifecycle) |
| Egress | tốn băng thông server | $0 (Cloudflare) |

Đổi flag là đủ để rollback — dữ liệu cũ vẫn đọc được vì DB lưu URL, và mỗi backend
tự nhận URL của mình. Thiếu credential khi `STORAGE_BACKEND=r2` thì app báo lỗi rõ
ràng ngay lần dùng đầu tiên (không âm thầm ghi sai chỗ).

Lưu ý:

- Ảnh SGK (`/sgk-images/...`) **luôn** nằm trên đĩa (giải nén từ `sgk_data/images.tar`),
  không đi qua storage backend — chúng là nội dung tĩnh, không phải file người dùng upload.
- Migration dữ liệu cũ từ `local` sang `r2` **không tự động**: phải upload lại
  `uploads/` lên bucket rồi cập nhật URL trong DB (hoặc chấp nhận URL cũ chỉ đọc được
  khi còn chạy `local`).
- Kế hoạch gốc + checklist: [PLAN-R2-STORAGE.md](PLAN-R2-STORAGE.md).

## Các bước deploy lần đầu trên server (cách build từ source)

> Chỉ dùng khi bạn **muốn** có repo trên server. Nếu không, xem mục image-only ở trên.

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
- API: `http://<server-ip>/api/...` (qua nginx) — frontend được build với `VITE_API_BASE_URL=/api`; nginx chuẩn hoá `/api/api/v1/...` → `/api/v1/...` và chuyển nguyên path `/api/v1/...` cho FastAPI (các router đã có prefix `/api/v1`).
- Health check: `curl http://<server-ip>/health`

Nếu **không** dùng nginx proxy thì đổi `VITE_API_BASE_URL=http://<server-ip>:8000` trong `.env.prod` và publish port 8000/3000 trong compose.

## Cập nhật khi có code mới

Image-only (không cần repo trên server):

```powershell
# build + push tag mới ở máy dev, rồi:
pwsh deploy/scripts/deploy-remote.ps1 -Server <ip> -Tag <tag-moi> -SkipData -SkipUpload -Proxy
# đang dùng tunnel: thay -Proxy bằng -Tunnel
```

Hoặc để CD tự làm: **push lên branch `prod`** → GitHub build và deploy (xem mục CD bên dưới).

Cách build từ source trên server:

```bash
cd /opt/smartlms
git pull
bash deploy/scripts/deploy.sh --proxy        # build lại image rồi up -d
# xem log: docker logs -f smartlms_backend
```

## CD tự động (GitHub Actions) — push `prod` là lên server

Workflow đã có sẵn ở [`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml).
**Không cần copy gì**, chỉ cần tạo branch `prod` và điền secret.

### Luồng chạy

```
push lên branch prod
   ↓
GitHub build backend + frontend  (cache layer qua GHA, build lại chỉ phần thay đổi)
   ↓
push 2 image lên GHCR, tag = full commit SHA (+ latest)
   ↓
cài cloudflared trong runner  →  SSH qua Cloudflare Access (service token)
   ↓
scp compose + nginx.conf + 01_extensions.sql + remote-deploy.sh + .deploy.env
   ↓
bash deploy/scripts/remote-deploy.sh: merge env → pre-flight → pull → up -d → chờ healthy
```

Server **không** clone repo, **không** build gì. Image tag là SHA bất biến → rollback chỉ
là deploy lại tag cũ.

> **sshd không mở ra Internet.** Kết nối đi qua Cloudflare Access
> (`ssh-staging.vnexus.io.vn`), nên workflow cài `cloudflared` và dùng
> `ProxyCommand cloudflared access ssh --hostname %h`. Xác thực không tương tác bằng
> **service token**, không phải browser/SSO.

### Cài lần đầu

1. Tạo branch `prod` (workflow chỉ chạy khi push vào đúng branch này):

   ```bash
   git checkout -b prod
   git push -u origin prod
   ```

2. **Settings → Secrets and variables → Actions** → tạo:

   | Secret | Bắt buộc | Giá trị |
   |---|---|---|
   | `DEPLOY_HOST` | ✅ | **hostname** SSH qua Access — `ssh-staging.vnexus.io.vn`. **Không phải IP server** (IP vẫn bị tunnel che) |
   | `DEPLOY_USER` | ✅ | user SSH (vd `thanhnvq`) |
   | `DEPLOY_SSH_KEY` | ✅ | private key, public key đã nằm trong `~/.ssh/authorized_keys` của server |
   | `DEPLOY_PATH` | ✅ | thư mục project trên server (vd `/opt/smartlms`) |
   | `CF_ACCESS_CLIENT_ID` | ✅ | Client ID của Cloudflare Access **service token** |
   | `CF_ACCESS_CLIENT_SECRET` | ✅ | Client Secret của service token đó |
   | `ADMIN_PHONE` | ⭐ nên có | số điện thoại đăng nhập của admin chính (login bằng **phone**, không phải email) |
   | `ADMIN_PASSWORD` | ⭐ nên có | mật khẩu admin, **≥ 8 ký tự**, không được là placeholder |
   | `ADMIN_EMAIL` | tuỳ chọn | chỉ là metadata, không dùng để đăng nhập |
   | `ADMIN_FULL_NAME` | tuỳ chọn | mặc định `System Administrator` |
   | `STORAGE_BACKEND` | tuỳ chọn | `local` (mặc định) hoặc `r2` |
   | `R2_ACCOUNT_ID` | khi dùng R2 | Cloudflare account ID |
   | `R2_ACCESS_KEY_ID` | khi dùng R2 | access key của R2 API token |
   | `R2_SECRET_ACCESS_KEY` | khi dùng R2 | secret key của R2 API token |
   | `R2_BUCKET` | khi dùng R2 | tên bucket (vd `smartlms-tk`) |
   | `R2_PUBLIC_BASE_URL` | khi dùng R2 | domain public của bucket (custom domain hoặc `*.r2.dev`) |
   | `GHCR_PAT` | tuỳ chọn | PAT quyền `read:packages`, chỉ cần khi package để private |

   Có secret thì workflow ghi đè đúng key đó trong `deploy/.env.prod` trên server
   trước khi `up -d`. Secret để trống ⇒ giữ nguyên giá trị đang có trong file (không xoá).

   Nếu `STORAGE_BACKEND=r2` mà thiếu bất kỳ `R2_*` nào, workflow **dừng trước khi deploy**
   thay vì để backend trả 500 ở request upload đầu tiên.

3. Tạo **service token** cho Cloudflare Access (CI không đăng nhập browser/SSO được):

   a. Zero Trust → **Access** → **Service Auth** → **Create Service Token**
      - Name: `github-actions-smartlms`
      - Duration: `Non-expiring` (hoặc 1 năm — hết hạn thì deploy fail, nhớ gia hạn)
   b. Copy **Client ID** + **Client Secret** → 2 secret `CF_ACCESS_CLIENT_ID` / `CF_ACCESS_CLIENT_SECRET`
   c. Zero Trust → **Access** → **Applications** → application của `ssh-staging.vnexus.io.vn`
      → **Policies** → thêm policy:
      - Action: **Service Auth**
      - Include: **Service Token** → chọn `github-actions-smartlms`

   Thiếu bước c thì token đúng vẫn bị **403** — policy mặc định chỉ cho email/SSO.

   Kiểm tra nhanh từ máy dev (không cần đợi CI):

   ```powershell
   $env:TUNNEL_SERVICE_TOKEN_ID="<client-id>"
   $env:TUNNEL_SERVICE_TOKEN_SECRET="<client-secret>"
   ssh -o ProxyCommand="cloudflared access ssh --hostname %h" thanhnvq@ssh-staging.vnexus.io.vn "echo OK"
   ```

4. Tab **Variables** → thêm `DEPLOY_PROFILE` = `tunnel` (hoặc `proxy` / `quick`).
   Không đặt thì mặc định là `tunnel`. (Không cần cổng SSH — `cloudflared` lo phần đó.)

5. Chạy bootstrap một lần từ máy dev để tạo thư mục + `sgk_data` trên server:

   ```powershell
   $env:TUNNEL_SERVICE_TOKEN_ID="<client-id>"
   $env:TUNNEL_SERVICE_TOKEN_SECRET="<client-secret>"
   pwsh deploy/scripts/deploy-remote.ps1 -Server ssh-staging.vnexus.io.vn -User thanhnvq `
     -CloudflareAccess -SkipUpload -SkipData
   ```

   (cần `deploy/.env.prod` có sẵn trên server — xem mục trên)

6. Push lên `prod` → xem tab **Actions**.

### Account Admin chính trên production

`alembic upgrade head` chỉ tạo **bảng**, không seed role/permission/user. Bản dev chạy
`app/scripts/seed.py` bằng tay nên có sẵn `admin@school.com`; database production dựng
thuần từ migration thì **rỗng hoàn toàn** — mà login lại chỉ nhận **số điện thoại**, nên
không có account nào thì không ai vào được.

Vì vậy `backend/docker/entrypoint.sh` chạy thêm một bước sau migrate:

```
alembic upgrade head
  ↓
python app/scripts/bootstrap_admin.py     ← tạo role + permission + account Admin
  ↓
load_sgk.sh
  ↓
uvicorn
```

Cấu hình trong `deploy/.env.prod` (hoặc secret GitHub như bảng trên):

| Biến | Ý nghĩa |
|---|---|
| `ADMIN_PHONE` | số điện thoại đăng nhập — **bắt buộc để tạo account** |
| `ADMIN_PASSWORD` | mật khẩu thô, được bcrypt hash trước khi lưu |
| `ADMIN_EMAIL` | tuỳ chọn, chỉ để hiển thị |
| `ADMIN_FULL_NAME` | tuỳ chọn, mặc định `System Administrator` |
| `ADMIN_RESET_PASSWORD` | `1` = ép mật khẩu về `ADMIN_PASSWORD` (dùng khi quên mật khẩu) |

Đặc tính:

- **Idempotent** — chạy lại mỗi lần restart chỉ kiểm tra, không tạo trùng, **không đổi mật
  khẩu** (trừ khi `ADMIN_RESET_PASSWORD=1`).
- Bỏ trống cả `ADMIN_PHONE` và `ADMIN_PASSWORD` ⇒ bỏ qua bước này, container vẫn start
  (dev/CI không bị ảnh hưởng).
- Chỉ điền một trong hai ⇒ **fail**, vì gần như chắc chắn là secret điền thiếu.
- Mật khẩu còn là placeholder (`<doi-mat-khau...>`, `changeme`...) hoặc < 8 ký tự ⇒ **fail**
  thay vì tạo account có mật khẩu ai cũng biết.
- `ADMIN_PHONE` trùng với một user **không phải Admin** ⇒ **fail**, không âm thầm promote
  giáo viên/học sinh thành admin.
- Script cũng tạo luôn 3 role + 19 permission + mapping, nếu thiếu thì admin đăng nhập
  được nhưng **không có quyền nào**.

Kiểm tra sau khi deploy:

```bash
docker logs smartlms_backend 2>&1 | grep bootstrap_admin:
# bootstrap_admin: admin 099****001 -> created, role=Admin
# hoặc: -> unchanged   (lần restart sau)
```

Quên mật khẩu → đặt `ADMIN_RESET_PASSWORD=1`, deploy lại, đăng nhập, rồi **đưa về `0`**
(nếu không mỗi lần deploy lại reset tiếp).

### Rollback

```powershell
$env:TUNNEL_SERVICE_TOKEN_ID="<client-id>"
$env:TUNNEL_SERVICE_TOKEN_SECRET="<client-secret>"
pwsh deploy/scripts/deploy-remote.ps1 -Server ssh-staging.vnexus.io.vn -User thanhnvq `
  -CloudflareAccess -Tag <sha-cu> -SkipData -SkipUpload -Tunnel
```

Hoặc chạy lại workflow của commit cũ (Actions → chọn run → Re-run), rồi trên server
`IMAGE_TAG=<sha-cu> docker compose ... up -d`.

> Mọi lệnh `deploy-remote.ps1` trong tài liệu này đều phải thêm
> `-CloudflareAccess -Server ssh-staging.vnexus.io.vn` (thay `-Server <ip>`), vì sshd
> không mở ra Internet.

### Lưu ý

- Workflow **không** chạy `git pull` trên server và **không** gửi source code — chỉ gửi
  3 file config.
- `deploy/.env.prod` trên server **không bị ghi đè** bởi workflow, trừ các key `ADMIN_*`
  khi secret tương ứng được đặt (xem mục *Account Admin chính* ở trên).
- Nếu package GHCR để private mà không có `GHCR_PAT`, bước `docker login` trên server vẫn
  chạy bằng `GITHUB_TOKEN` của run đó — pull được ngay, nhưng `docker pull` thủ công sau
  này trên server sẽ cần login lại.

## Lưu ý bảo mật

- `deploy/.env.prod` **không được commit** (đã thêm vào `.gitignore`).
- Đổi `SECRET_KEY` và mật khẩu DB mặc định (`123456` ở bản dev) trước khi lên production.
- Prod compose không publish port 5432 ra ngoài; chỉ backend mới kết nối được với Postgres qua network nội bộ của compose.
- Ảnh upload lưu ở named volume `backend_uploads` (khi `STORAGE_BACKEND=local`) hoặc trên
  R2 (khi `STORAGE_BACKEND=r2`) — nhớ backup `postgres_data` và đúng nơi đang dùng.

## Sự cố thường gặp khi deploy image-only

| Triệu chứng | Nguyên nhân | Cách sửa |
|---|---|---|
| `invalid reference format: repository name must be lowercase` | `github.repository_owner` có chữ hoa | lowercase owner trước khi `docker build` (CD đã làm sẵn) |
| `pull access denied` / `403 Forbidden` | package GHCR để private | `docker login ghcr.io -u <user> --password-stdin` trên server, hoặc để package public |
| Tìm kiếm đề thi trả 500, log báo `function unaccent(...) does not exist` | volume Postgres được tạo **trước** khi mount `postgres-init/` | `docker exec -it smartlms_postgres psql -U postgres -d teacher_assistance -c "CREATE EXTENSION IF NOT EXISTS unaccent;"` |
| RAG không có dữ liệu, `/sgk-images/...` 404 | thiếu `sgk_data/` hoặc upload sai chỗ | `ls /opt/smartlms/sgk_data` phải thấy `vectors.dump` + `images.tar`; xem log `load_sgk:` |
| Backend restart liên tục sau khi đổi image | migration/entrypoint lỗi | `docker logs --tail 200 smartlms_backend` |
| Frontend gọi API sai host | image build với `VITE_API_BASE_URL` khác `/api` | build lại frontend với `--build-arg VITE_API_BASE_URL=/api` |
| `smartlms_cloudflared` restart liên tục | token sai/bị thu hồi, hoặc tunnel đã xoá trên dashboard | tạo token mới, cập nhật `CLOUDFLARE_TUNNEL_TOKEN`, `docker compose ... up -d` |
| Cloudflare trả **1033** (tunnel không có connector) | container cloudflared chết hoặc chưa start | `docker ps` phải thấy `smartlms_cloudflared`; `docker logs smartlms_cloudflared` |
| Cloudflare trả **502/521** | public hostname trỏ sai service | phải là `http://nginx:80` (không phải `localhost:80`) |
| SSE tự ngắt sau ~1-2 phút | thiếu keep-alive qua Cloudflare | backend đã gửi `: keep-alive` mỗi 15s; nếu đã sửa code, kiểm tra `SSE_HEARTBEAT_SECONDS` |
| Ảnh R2 trả `403 error code: 1010` | Cloudflare **Browser Integrity Check** chặn User-Agent lạ (vd `Python-urllib`, `python-httpx`) | Không phải lỗi bucket. Browser thật (`<img src>`) vẫn 200. Backend đọc file qua **S3 API** chứ không qua domain public, nên PDF export vẫn OK. Chỉ script tự viết gọi HTTP mới cần set User-Agent giống browser |
| Upload R2 trả 500, log `requires these environment variables: ...` | `STORAGE_BACKEND=r2` nhưng thiếu biến `R2_*` | điền đủ 5 biến; CD đã chặn sẵn ở bước pre-flight. Kiểm tra nhanh: `python scripts/r2_smoke_test.py` |
| CD dừng ở bước SSH, log `Permission denied (publickey)` | `DEPLOY_SSH_KEY` sai, hoặc public key chưa nằm trong `~/.ssh/authorized_keys` của server | test tay bằng đúng lệnh trong mục *Service token*; nhớ secret phải là file **private** (không có `.pub`) |
| CD dừng ở bước SSH, log `403` từ Cloudflare hoặc treo ~60s rồi timeout | service token chưa được **authorize trong Access policy** của application SSH | thêm policy `Service Auth` + `Include: Service Token` (bước 3c ở trên) |
| CD lỗi `cloudflared: command not found` | bước cài cloudflared bị bỏ qua / `$GITHUB_PATH` không áp dụng | xem log step *Install cloudflared*; `cloudflared --version` phải in ra |
| CD treo ở SSH, log nhắc `browser` / `login` | cloudflared bản 2026.6.0 bỏ qua service token và chuyển sang SSO | workflow đã pin `2026.5.1`; nếu tự nâng version thì kiểm tra lại service token |
| `DEPLOY_HOST` trỏ IP mà vẫn timeout | sshd không mở ra Internet, chỉ vào được qua Access | `DEPLOY_HOST` phải là `ssh-staging.vnexus.io.vn`, không phải `171.251.234.131` |

## Hiệu năng cho ~30 user đồng thời

### RAM budget 5 GB

Prod compose đặt `mem_limit` cho từng service (tổng 5.0 GB):

| Service | Limit | Vai trò |
|---|---:|---|
| postgres | 1536 MB | shared_buffers + connection pool + pgvector |
| backend | 2560 MB | Python/uvicorn + reportlab (PDF) + pypdfium2 (ETL) |
| frontend | 896 MB | Node/Vite preview (thực tế dùng ít hơn) |
| nginx | 128 MB | reverse proxy + buffer nhỏ |
| cloudflared | 128 MB | *chỉ khi `--profile tunnel`* |
| **Tổng** | **5120 MB** | **5248 MB** nếu bật tunnel; chừa thêm ~1 GB cho host OS/Docker |

Nếu tăng limit của một service, phải giảm service khác — Docker OOM-kill container
vượt limit, và backend bị kill sẽ làm rơi SSE stream + job ingest đang chạy.

### Nginx (`deploy/nginx/nginx.conf`)

- `gzip on` cho JSON/JS/CSS (không gzip `text/event-stream`).
- SSE `/api/v1/sync/stream` và `/api/v1/admin/monitoring/stream`:
  `proxy_buffering off`, `proxy_read_timeout 3600s`, `proxy_http_version 1.1`.
- `client_max_body_size 50m` khớp `MAX_INGEST_BYTES`.
- Ảnh `/uploads/` và `/sgk-images/` được trình duyệt cache 7 ngày
  (`Cache-Control: public, max-age=604800, immutable`).
- File này là server block (mount vào `conf.d`). `limit_req_zone` và
  `proxy_cache_path` phải khai báo ở http context trong `/etc/nginx/nginx.conf`
  nếu muốn rate limit/proxy cache ở edge; app đã rate-limit login trong
  `app/core/rate_limit.py`.

Với 30 user chỉ cần **1 Nginx reverse proxy + 1 backend worker**; không cần API
gateway. Nếu scale lên 100+ user, tăng số uvicorn worker (mỗi worker có pool 50
connection — kiểm tra `max_connections` của Postgres) hoặc chạy thêm backend
replica sau Nginx. CDN chỉ nên dùng cho static assets (`/uploads/`, `/sgk-images/`,
JS/CSS build), **không** cache API cá nhân (`Authorization`/`Cookie`).

### Load test

```bash
cd backend
..\.venv\Scripts\python.exe scripts\load_test.py \
  --base-url http://localhost:8000 \
  --users 30 --requests-per-user 20 \
  --phone 0999000002 --password 'Teacher@1234'
```

Script in ra latency p50/p95/p99, RPS, error rate và JSON. Chạy trực tiếp vào backend
(port 8000) để đo app; nếu đo qua Nginx, tắt/tăng rate limit trước.

### Migration index

Sau khi deploy code mới, chạy migration index (một lần):

```bash
cd backend
..\.venv\Scripts\python.exe -m alembic upgrade head
```

Migration `f4b8c2d6e9a1_add_concurrency_indexes.py` chỉ thêm index
(`IF NOT EXISTS`), không đổi schema; xem chi tiết trong `docs/performance.md`.
