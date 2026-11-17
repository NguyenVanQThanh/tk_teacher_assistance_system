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
# Optional VERSION file next to vectors.dump: when it differs from sgk_meta.data_version the chunks are
# replaced by the dump, so improved labels/embeddings ship by swapping the dump + VERSION (no code change).
# Missing files are skipped. Unchanged data is not reloaded, so restarts are cheap.
# Requires migrate.sh to have run first (creates chunks and sgk_docs).
set -eu

DATA_DIR="${SGK_DATA_DIR:-/sgk_data}"
IMG_DIR="${SGK_IMAGE_DIR:-/app/uploads/sgk_images}"
export PGPASSWORD="${DB_PASSWORD:-}"
PSQL="psql -h ${DB_HOST:-localhost} -p ${DB_PORT:-5432} -U ${DB_USER:-postgres} -d ${DB_NAME:-teacher_assistance} -v ON_ERROR_STOP=1 -tA"

if [ -f "$DATA_DIR/vectors.dump" ]; then
  # Data version: contents of $DATA_DIR/VERSION (defaults to "0" when absent). A restore happens when
  # chunks is empty OR the loaded version differs, so relabelled/re-indexed dumps roll out by replacing
  # the dump + VERSION. `chunks` holds SGK only (teacher documents live in document_chunks).
  want="$(tr -d '[:space:]' < "$DATA_DIR/VERSION" 2>/dev/null || true)"
  want="${want:-0}"
  $PSQL -c "CREATE TABLE IF NOT EXISTS sgk_meta (key text PRIMARY KEY, value text NOT NULL)"
  have="$($PSQL -c "SELECT value FROM sgk_meta WHERE key = 'data_version'")"
  rows=$($PSQL -c "SELECT count(*) FROM chunks")
  if [ "$rows" = "0" ] || [ "$have" != "$want" ]; then
    echo "load_sgk: restoring chunks from vectors.dump (loaded=${have:-none} wanted=$want rows=$rows)"
    # A failed restore leaves chunks empty, so the next start retries and set -e fails this deploy loudly.
    [ "$rows" = "0" ] || $PSQL -c "TRUNCATE chunks"
    pg_restore --data-only --no-owner --no-privileges --exit-on-error --single-transaction -t chunks       -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}"       -d "${DB_NAME:-teacher_assistance}" "$DATA_DIR/vectors.dump"
    # Make figure paths relative and fill tsv, same as app/scripts/load_sgk_rag.py post_process
    $PSQL -c "UPDATE chunks SET meta = jsonb_set(meta, '{figure_path}', to_jsonb(regexp_replace(meta->>'figure_path', '^.*/(images/)', ''))) WHERE modality = 'image' AND meta->>'figure_path' ~ '/images/'"
    $PSQL -c "UPDATE chunks SET tsv = to_tsvector('simple', content) WHERE tsv IS NULL"
    $PSQL -c "ANALYZE chunks"
    $PSQL -c "INSERT INTO sgk_meta (key, value) VALUES ('data_version', '$want') ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value"
    echo "load_sgk: chunks rows = $($PSQL -c 'SELECT count(*) FROM chunks') version=$want"
  else
    echo "load_sgk: chunks up to date (version $have, $rows rows), skip restore"
  fi
fi

if [ -f "$DATA_DIR/images.tar" ] && [ -z "$(ls -A "$IMG_DIR" 2>/dev/null)" ]; then
  echo "load_sgk: extracting images.tar into $IMG_DIR"
  mkdir -p "$IMG_DIR"
  tar -xf "$DATA_DIR/images.tar" -C "$IMG_DIR" --strip-components=1
fi
