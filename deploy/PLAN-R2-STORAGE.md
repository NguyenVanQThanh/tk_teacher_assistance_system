# Kế hoạch: chuyển lưu trữ file upload sang Cloudflare R2 (S3-compatible)

> Quyết định ngày 2026-11-12: dùng **Cloudflare R2** thay vì lưu local trên đĩa EBS
> của EC2 (và thay vì S3 của AWS) cho giai đoạn deploy test 1-2 tuần.

## 1. Lý do chọn R2

Người dùng vừa **upload** (đề, ảnh câu hỏi) vừa **download** (tải file về) nên tiền
**egress** (băng thông tải ra) là thứ quan trọng nhất:

| | AWS S3 | Cloudflare R2 |
|---|---|---|
| Storage free | 5GB (12 tháng đầu) / theo $100 credit | **10GB vĩnh viễn** |
| Egress (download) | ~$0.09/GB — tính tiền theo lượt tải | **$0, miễn phí vĩnh viễn** |
| Read operations | tính phí theo request | **10 triệu lượt/tháng free** |
| API | S3 | **S3-compatible** — dùng nguyên `boto3`, chỉ đổi endpoint + key |

Nguồn: [Cloudflare R2](https://www.cloudflare.com/products/r2/), [R2 + boto3](https://developers.cloudflare.com/r2/examples/aws/boto3/)

Với R2, toàn bộ chi phí lưu trữ + tải file trong 2 tuần test gần như **bằng 0**,
không đụng đến credit AWS (chỉ tốn tiền chạy EC2 t3.micro).

## 2. Kiến trúc mục tiêu

```
Browser ──upload──► EC2 (FastAPI) ──put_object──► Cloudflare R2 bucket
Browser ◄──URL tải về──────────────────────────────┘ (qua domain Cloudflare, HTTPS free)
```

- **Upload**: browser → backend → R2 (kiểu đơn giản, không cần CORS trên bucket).
- **Download**: backend trả về **URL công khai của object trên R2** (custom domain
  Cloudflare hoặc `*.r2.dev`). **Không proxy byte file qua backend/EC2** để tránh
  tốn băng thông out của EC2.
- App hiện đang serve ảnh qua FastAPI `StaticFiles` tại `/uploads/questions`
  (xem `QUESTION_IMAGE_URL_PREFIX` trong `backend/.env.example`) — sẽ chuyển sang
  trả URL của R2.

## 3. Checklist implement (code backend)

> Trạng thái 2026-11-13: **đã implement** — xem `backend/app/core/storage.py`.
> Bật bằng `STORAGE_BACKEND=r2` (alias `cloud`/`s3`), rollback bằng `STORAGE_BACKEND=local`.

- [x] Thêm `boto3>=1.34` vào `backend/requirements.txt`
- [x] Tạo module storage (`backend/app/core/storage.py`): `LocalStorage` + `R2Storage`
      (`boto3.client("s3", endpoint_url="https://<ACCOUNT_ID>.r2.cloudflarestorage.com", region_name="auto")`)
- [x] Đọc config từ biến môi trường: `STORAGE_BACKEND`, `R2_ACCOUNT_ID`,
  `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`, `R2_PUBLIC_BASE_URL`
- [x] Sửa chỗ ghi file upload (`QUESTION_IMAGE_DIR`, `uploads/documents`) sang `storage.put`;
      DB vẫn lưu URL string như cũ
- [x] Sửa chỗ đọc/serve `/uploads/...` sang `storage.get` / URL R2.
      `/sgk-images/` vẫn là static local vì là dữ liệu SGK giải nén từ `images.tar`
- [x] Không cần Alembic migration: cột `file_url`/`image_url` vẫn là string
- [x] Nối vào CD: `.github/workflows/deploy.yml` nhận secret `STORAGE_BACKEND` + `R2_*`,
      ghi đè vào `deploy/.env.prod` trên server, và **chặn deploy** nếu `STORAGE_BACKEND=r2`
      mà thiếu bất kỳ biến `R2_*` nào
- [ ] Test đầu-cuối với bucket thật: upload đề PDF/ảnh → lưu DB → tải về bằng URL R2 →
      kiểm tra Cloudflare analytics (cần credential thật, chưa chạy)
- [ ] Điền `R2_*` thật — hoặc trong `deploy/.env.prod` trên server, hoặc trong GitHub
      Secrets (không commit cả hai)

## 4. Biến môi trường cần thêm (đã khai báo sẵn trong `deploy/.env.prod.example`)

```
STORAGE_BACKEND=r2            # "r2" hoặc "local" (rollback về đĩa EC2)
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...          # R2 API token
R2_SECRET_ACCESS_KEY=...
R2_BUCKET=smartlms-uploads
R2_PUBLIC_BASE_URL=https://files.<domain-cua-ban>
```

Cả 5 biến `R2_*` đều **bắt buộc** khi `STORAGE_BACKEND=r2` — `get_storage()` ném
`RuntimeError` liệt kê tên biến thiếu nếu không đủ, nên đừng coi `R2_PUBLIC_BASE_URL` là
tuỳ chọn.

## 5. Cấu hình cần tạo trên Cloudflare

1. Tạo **R2 bucket** (vd: `smartlms-uploads`).
2. Bật **public access** cho bucket + gắn **custom domain** (vd: `files.<domain>`)
   — HTTPS free qua Cloudflare; hoặc tạm dùng `*.r2.dev` khi test.
3. Tạo **R2 API token** (Access Key ID + Secret Access Key), giới hạn quyền chỉ đúng
   bucket đó (read/write cho backend; public chỉ GET).
4. Domain chính trỏ về EC2 bằng bản ghi DNS **proxy (cam)** để có HTTPS + CDN,
   hoặc chạy **Cloudflare Tunnel (`cloudflared`)** trên EC2 nếu không muốn mở port 80.

## 6. Bảo mật

- `R2_SECRET_ACCESS_KEY` chỉ nằm trong `deploy/.env.prod` trên server và trong
  secret của GitHub Actions — **không commit** (đã có trong `.gitignore`).
- Bucket để public-read (chỉ GET), mọi thao tác ghi chỉ đi qua backend bằng API token.
- Nếu cần riêng tư tuyệt đối: tắt public access, dùng **presigned URL** cho cả
  upload lẫn download (thêm một ít code ở backend).

## 7. Timeline & rollback

- Giai đoạn test: **1-2 tuần**. Nhớ đặt billing alarm ~$5 trên AWS và tắt/xoá
  tài nguyên (EC2, EBS, bucket) sau khi hết đợt test.
- Rollback về lưu local trên EC2 chỉ bằng cách đổi `STORAGE_BACKEND=local`
  trong `deploy/.env.prod` (code cũ vẫn còn trong nhánh git).
