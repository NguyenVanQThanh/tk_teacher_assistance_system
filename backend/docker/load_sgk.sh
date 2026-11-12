#!/bin/sh
# File Name: load_sgk.sh
# Description: One-time load of the SGK RAG data: chunks from vectors.dump and figure images from images.tar.
# Created At: 2026-11-12
# Created By: AI Agent
# Updated At: 2026-11-12
# Updated By: AI Agent
#
# Inputs (mounted read-only at /sgk_data, override with SGK_DATA_DIR):
#   vectors.dump  pg_dump custom-format file with the `chunks` table (pg16)
#   images.tar    tar of the `images/` folder (gives images/<doc_id>/pN_fK.png)
# Missing files are skipped. Each load runs only when its target is empty, so restarts are cheap.
# Requires migrate.sh to have run first (creates chunks and sgk_docs).
set -eu

DATA_DIR="${SGK_DATA_DIR:-/sgk_data}"
IMG_DIR="${SGK_IMAGE_DIR:-/app/uploads/sgk_images}"
export PGPASSWORD="${DB_PASSWORD:-}"
PSQL="psql -h ${DB_HOST:-localhost} -p ${DB_PORT:-5432} -U ${DB_USER:-postgres} -d ${DB_NAME:-teacher_assistance} -v ON_ERROR_STOP=1 -tA"

if [ -f "$DATA_DIR/vectors.dump" ]; then
  rows=$($PSQL -c "SELECT count(*) FROM chunks")
  if [ "$rows" = "0" ]; then
    echo "load_sgk: restoring chunks from vectors.dump"
    pg_restore --data-only --no-owner --no-privileges --exit-on-error -t chunks \
      -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" \
      -d "${DB_NAME:-teacher_assistance}" "$DATA_DIR/vectors.dump"
    # Make figure paths relative and fill tsv, same as app/scripts/load_sgk_rag.py post_process
    $PSQL -c "UPDATE chunks SET meta = jsonb_set(meta, '{figure_path}', to_jsonb(regexp_replace(meta->>'figure_path', '^.*/(images/)', '\1'))) WHERE modality = 'image' AND meta->>'figure_path' ~ '/images/'"
    $PSQL -c "UPDATE chunks SET tsv = to_tsvector('simple', content) WHERE tsv IS NULL"
    $PSQL -c "ANALYZE chunks"
    echo "load_sgk: chunks rows = $($PSQL -c 'SELECT count(*) FROM chunks')"
  else
    echo "load_sgk: chunks already has $rows rows, skip restore"
  fi
fi

if [ -f "$DATA_DIR/images.tar" ] && [ -z "$(ls -A "$IMG_DIR" 2>/dev/null)" ]; then
  echo "load_sgk: extracting images.tar into $IMG_DIR"
  mkdir -p "$IMG_DIR"
  tar -xf "$DATA_DIR/images.tar" -C "$IMG_DIR" --strip-components=1
fi
