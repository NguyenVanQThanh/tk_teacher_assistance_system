#!/bin/sh
# File Name: remote-deploy.sh
# Description: Chạy TRÊN server. Được .github/workflows/deploy.yml gọi qua SSH
#              (Cloudflare Access): merge biến CI đẩy lên vào deploy/.env.prod,
#              login GHCR, pull image mới, restart stack, chờ backend healthy.
# Created At: 2026-11-14
# Created By: AI Agent
# Updated At: 2026-11-14
# Updated By: AI Agent
#
# Dùng (trên server):
#   bash deploy/scripts/remote-deploy.sh /opt/smartlms
#
# Input:
#   $1                    thư mục project trên server (mặc định: thư mục hiện tại)
#   <target>/.deploy.env  biến do CI đẩy lên: IMAGE_TAG, GHCR_USER, GHCR_TOKEN,
#                         PROFILE, ADMIN_*, STORAGE_BACKEND, R2_*
#                         File này bị xoá sau khi chạy xong.
#
# Không bao giờ in giá trị secret ra stdout.
set -eu

TARGET="${1:-$(pwd)}"
cd "$TARGET"

ENV_FILE="deploy/.env.prod"
OVERRIDES="$TARGET/.deploy.env"
COMPOSE_FILE="deploy/docker-compose.images.yml"
BACKEND_CONTAINER="smartlms_backend"
HEALTH_TIMEOUT_STEPS=60   # 60 x 2s = 120s

[ -f "$COMPOSE_FILE" ] || { echo "ERROR: thieu $COMPOSE_FILE trong $TARGET"; exit 1; }
[ -f "$ENV_FILE" ] || { echo "ERROR: thieu $ENV_FILE trong $TARGET"; exit 1; }

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Đọc 1 key từ .deploy.env. Không `source` file vì mật khẩu có thể chứa
# space, $, backtick... — cut -f2- giữ nguyên phần sau dấu = đầu tiên.
get_val() {
  [ -f "$OVERRIDES" ] || { printf ''; return 0; }
  grep -E "^$1=" "$OVERRIDES" 2>/dev/null | tail -1 | cut -d= -f2- || true
}

# Ghi đè 1 key trong .env.prod. Giá trị rỗng => giữ nguyên.
set_env() {
  key="$1"
  val="$2"
  if [ -z "$val" ]; then
    return 0
  fi
  if grep -q "^${key}=" "$ENV_FILE"; then
    grep -v "^${key}=" "$ENV_FILE" > "$ENV_FILE.tmp" || true
    mv "$ENV_FILE.tmp" "$ENV_FILE"
  fi
  # Tránh dán vào cuối dòng cuối khi file thiếu newline kết thúc.
  if [ -s "$ENV_FILE" ] && [ -n "$(tail -c 1 "$ENV_FILE")" ]; then
    printf '\n' >> "$ENV_FILE"
  fi
  printf '%s=%s\n' "$key" "$val" >> "$ENV_FILE"
  chmod 600 "$ENV_FILE"
}

# ---------------------------------------------------------------------------
# 1. Merge biến CI vào .env.prod (trừ các biến chỉ dùng lúc chạy)
# ---------------------------------------------------------------------------
if [ -f "$OVERRIDES" ]; then
  echo "==> merge bien tu .deploy.env vao $ENV_FILE"
  while IFS= read -r line; do
    case "$line" in
      ''|\#*) continue ;;
    esac
    key=${line%%=*}
    val=${line#*=}
    case "$key" in
      IMAGE_TAG|GHCR_USER|GHCR_TOKEN|PROFILE) continue ;;
    esac
    set_env "$key" "$val"
  done < "$OVERRIDES"
else
  echo "==> khong co .deploy.env, dung $ENV_FILE hien tai"
fi

IMAGE_TAG=$(get_val IMAGE_TAG)
GHCR_USER=$(get_val GHCR_USER)
GHCR_TOKEN=$(get_val GHCR_TOKEN)
PROFILE=$(get_val PROFILE)
PROFILE=${PROFILE:-tunnel}
IMAGE_TAG=${IMAGE_TAG:-latest}

# ---------------------------------------------------------------------------
# 2. Pre-flight: chặn cấu hình thiếu TRƯỚC khi restart (backend sẽ 500/không lên)
# ---------------------------------------------------------------------------
if [ "$PROFILE" = "tunnel" ] && ! grep -qE '^CLOUDFLARE_TUNNEL_TOKEN=.+' "$ENV_FILE"; then
  echo "ERROR: thieu CLOUDFLARE_TUNNEL_TOKEN trong $ENV_FILE"
  exit 1
fi

storage=$(grep -E '^STORAGE_BACKEND=' "$ENV_FILE" | tail -1 | cut -d= -f2- \
  | tr -d '\r' | tr '[:upper:]' '[:lower:]')
case "$storage" in
  ""|local) ;;
  r2|cloud|s3)
    missing=""
    for k in R2_ACCOUNT_ID R2_ACCESS_KEY_ID R2_SECRET_ACCESS_KEY R2_BUCKET R2_PUBLIC_BASE_URL; do
      grep -qE "^${k}=.+" "$ENV_FILE" || missing="$missing $k"
    done
    if [ -n "$missing" ]; then
      echo "ERROR: STORAGE_BACKEND=$storage nhung thieu:${missing} trong $ENV_FILE"
      exit 1
    fi
    echo "==> storage: $storage (du cau hinh R2)"
    ;;
  *)
    echo "ERROR: STORAGE_BACKEND=$storage khong hop le (local|r2)"
    exit 1
    ;;
esac

# ---------------------------------------------------------------------------
# 3. Pull image mới và restart
# ---------------------------------------------------------------------------
if [ -n "$GHCR_TOKEN" ] && [ -n "$GHCR_USER" ]; then
  echo "$GHCR_TOKEN" | docker login ghcr.io -u "$GHCR_USER" --password-stdin >/dev/null
fi
export IMAGE_TAG

COMPOSE="docker compose --project-directory . --env-file $ENV_FILE -f $COMPOSE_FILE --profile $PROFILE"

echo "==> pull (tag=$IMAGE_TAG)"
$COMPOSE pull

echo "==> up -d"
$COMPOSE up -d --remove-orphans
docker image prune -f >/dev/null 2>&1 || true

# ---------------------------------------------------------------------------
# 4. Chờ backend healthy (entrypoint chạy migrate + bootstrap_admin + load_sgk)
# ---------------------------------------------------------------------------
echo "==> doi $BACKEND_CONTAINER healthy (toi da $((HEALTH_TIMEOUT_STEPS * 2))s)"
status="unknown"
i=0
while [ "$i" -lt "$HEALTH_TIMEOUT_STEPS" ]; do
  status=$(docker inspect -f '{{.State.Health.Status}}' "$BACKEND_CONTAINER" 2>/dev/null || echo starting)
  if [ "$status" = "healthy" ]; then
    break
  fi
  sleep 2
  i=$((i + 1))
done
echo "backend health: $status"
if [ "$status" != "healthy" ]; then
  echo "LOI: backend khong healthy"
  docker logs --tail 100 "$BACKEND_CONTAINER" 2>&1 || true
  exit 1
fi

echo "==> ket qua bootstrap admin"
docker logs "$BACKEND_CONTAINER" 2>&1 | grep "bootstrap_admin:" || echo "(chua co log bootstrap_admin)"

$COMPOSE ps
rm -f "$OVERRIDES"
echo "==> deploy xong"
