#!/usr/bin/env bash
# File Name: setup_sgk.sh
# Description: Start the stack with SGK RAG data and verify the load (chunks, docs, images, API key).
# Created At: 2026-11-13
# Created By: AI Agent
# Updated At: 2026-11-13
# Updated By: AI Agent
#
# Usage (from anywhere):
#   bash deploy/scripts/setup_sgk.sh dev    # uses docker-compose.yml
#   bash deploy/scripts/setup_sgk.sh prod   # uses deploy/docker-compose.prod.yml + deploy/.env.prod
# Prerequisite: sgk_data/vectors.dump and sgk_data/images.tar exist at the repo root.
# This script never reads .env files; compose loads them itself.
set -euo pipefail

MODE="${1:-dev}"
cd "$(dirname "$0")/../.."

case "$MODE" in
  dev)  DC=(docker compose) ;;
  prod) DC=(docker compose --project-directory . --env-file deploy/.env.prod -f deploy/docker-compose.prod.yml) ;;
  *) echo "usage: $0 [dev|prod]" >&2; exit 2 ;;
esac

# 1. Data files
for f in sgk_data/vectors.dump sgk_data/images.tar; do
  [ -f "$f" ] || { echo "missing $f (copy from RAG_SGK/output/)" >&2; exit 1; }
done
echo "step 1: data files present"

# 2. Build and start (entrypoint runs migrate.sh then load_sgk.sh)
"${DC[@]}" up -d --build postgres backend
echo "step 2: waiting for backend to become healthy"
for _ in $(seq 1 120); do
  state=$(docker inspect -f '{{.State.Health.Status}}' smartlms_backend 2>/dev/null || echo none)
  [ "$state" = "healthy" ] && break
  sleep 5
done
[ "$state" = "healthy" ] || { echo "backend not healthy; see: ${DC[*]} logs backend" >&2; exit 1; }
"${DC[@]}" logs backend | grep "load_sgk" || true

# 3. Verify DB (runs inside the postgres container; creds come from its own env)
psql_q() { "${DC[@]}" exec -T postgres sh -c "psql -U \"\$POSTGRES_USER\" -d \"\$POSTGRES_DB\" -tA -c \"$1\""; }
chunks=$(psql_q "select count(*) from chunks")
docs=$(psql_q "select count(*) from sgk_docs")
echo "step 3: chunks=$chunks sgk_docs=$docs"
[ "$chunks" -gt 0 ] || { echo "chunks empty" >&2; exit 1; }

# 4. Verify images and API key (value is not printed)
imgs=$("${DC[@]}" exec -T backend sh -c 'find /app/uploads/sgk_images -name "*.png" | wc -l')
echo "step 4: sgk images=$imgs"
"${DC[@]}" exec -T backend sh -c '[ -n "${MISTRAL_API_KEY:-}" ]' \
  && echo "MISTRAL_API_KEY set" \
  || echo "WARNING: MISTRAL_API_KEY empty; query embedding will fail" >&2
echo "done"
