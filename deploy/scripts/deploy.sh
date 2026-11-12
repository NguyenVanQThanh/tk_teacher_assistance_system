#!/usr/bin/env bash
# Deploy thủ công lên server Linux, chạy từ bất kỳ đâu trong repo:
#   bash deploy/scripts/deploy.sh            # build từ source rồi up -d
#   bash deploy/scripts/deploy.sh --no-build # chỉ up bằng image hiện có trên máy
#   bash deploy/scripts/deploy.sh --proxy    # bật thêm nginx reverse proxy (mở port 80)
set -euo pipefail

# Về repo root (script nằm ở deploy/scripts/)
cd "$(dirname "$0")/../.."

ENV_FILE="deploy/.env.prod"
if [ ! -f "$ENV_FILE" ]; then
  echo "LỖI: thiếu $ENV_FILE — copy từ deploy/.env.prod.example rồi điền giá trị thật." >&2
  exit 1
fi

# --env-file ở project level: để compose đọc luôn VITE_API_BASE_URL cho build arg của frontend
COMPOSE=(docker compose --project-directory . --env-file deploy/.env.prod -f deploy/docker-compose.prod.yml)
PROFILE_ARGS=()
BUILD_FLAG="--build"
for arg in "$@"; do
  case "$arg" in
    --proxy)    PROFILE_ARGS=(--profile proxy) ;;
    --no-build) BUILD_FLAG="" ;;
    *) echo "Tham số không rõ: $arg (chỉ hỗ trợ --proxy / --no-build)" >&2; exit 2 ;;
  esac
done

"${COMPOSE[@]}" "${PROFILE_ARGS[@]}" up -d $BUILD_FLAG
"${COMPOSE[@]}" "${PROFILE_ARGS[@]}" ps
