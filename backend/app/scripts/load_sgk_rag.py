"""
File Name: load_sgk_rag.py
Description: Populate sgk_docs and load the SGK textbook RAG chunks (from RAG_SGK) into the main database.
Created At: 2026-11-11
Created By: AI Agent
Updated At: 2026-11-13
Updated By: AI Agent

Prerequisite: run `alembic upgrade head` first (creates extension vector, chunks, sgk_docs).

Usage (from backend/):
    python -m app.scripts.load_sgk_rag --rag-root D:/Code/RAG_SGK --dump D:/Code/RAG_SGK/output/export/vectors_20261110.dump
    python -m app.scripts.load_sgk_rag --rag-root D:/Code/RAG_SGK --csv  D:/Code/RAG_SGK/output/export/chunks.csv
    python -m app.scripts.load_sgk_rag --rag-root D:/Code/RAG_SGK --docs-only

Equivalent manual restore of the data (what --dump runs; needs pg_restore 16+ on PATH):
    pg_restore --data-only --no-owner --no-privileges -t chunks -d "$DSN" vectors_20261110.dump

Connection: --dsn, else env SGK_LOAD_DSN, else built from DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME
(process environment only; no .env file is read). Chunks are only loaded into an empty table unless --force.
After load, meta.figure_path is rewritten to 'images/<doc_id>/pN_fK.png' and missing tsv values are filled.
CSV columns: id,doc_id,page,chuong,bai,modality,content,embedding,meta (no header, no tsv).
"""
import argparse
import csv
import hashlib
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import psycopg2

from app.modules.exercise.services.rag_retrieval_service import subject_key_from_text

logger = logging.getLogger("load_sgk_rag")

# Equal to the filesystem root of RAG_SGK; relative path hash must match scripts/ocr_all.py doc_id_of().
GRADES = (10, 11, 12)

FIX_FIGURE_PATH_SQL = r"""
UPDATE chunks
SET meta = jsonb_set(meta, '{figure_path}', to_jsonb(regexp_replace(meta->>'figure_path', '^.*/(images/)', '\1')))
WHERE modality = 'image' AND meta->>'figure_path' ~ '/images/'
"""


def doc_id_of(pdf: Path, root: Path) -> str:
    """sha1 of the posix relative path (to the RAG_SGK root), first 12 hex chars."""
    return hashlib.sha1(pdf.relative_to(root).as_posix().encode("utf-8")).hexdigest()[:12]


def discover_docs(root: Path) -> List[Tuple[str, int, str, str]]:
    """Return (doc_id, grade, subject_key, title) for each PDF under data/Grade{10,11,12}."""
    docs = []
    for grade in GRADES:
        for pdf in sorted((root / "data" / f"Grade{grade}").glob("*.pdf")):
            key = subject_key_from_text(pdf.stem)
            if key is None:
                logger.warning("Skipping PDF with unknown subject: %s", pdf.name)
                continue
            docs.append((doc_id_of(pdf, root), grade, key, pdf.stem))
    return docs


def upsert_docs(conn, docs) -> int:
    with conn.cursor() as cur:
        for d in docs:
            cur.execute(
                "INSERT INTO sgk_docs (doc_id, grade, subject_key, title, status) VALUES (%s,%s,%s,%s,'ACTIVE') "
                "ON CONFLICT (doc_id) DO UPDATE SET grade=EXCLUDED.grade, subject_key=EXCLUDED.subject_key, "
                "title=EXCLUDED.title",
                d,
            )
    conn.commit()
    return len(docs)


def load_csv(conn, csv_path: Path) -> int:
    csv.field_size_limit(sys.maxsize)
    n = 0
    with conn.cursor() as cur, open(csv_path, encoding="utf-8", newline="") as fh:
        for row in csv.reader(fh):
            cid, doc_id, page, chuong, bai, modality, content, emb, meta = row[:9]
            cur.execute(
                "INSERT INTO chunks (id, doc_id, page, chuong, bai, modality, content, embedding, meta, tsv) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s::vector,%s::jsonb,to_tsvector('simple', %s)) "
                "ON CONFLICT (id) DO NOTHING",
                (cid, doc_id, int(page), chuong or None, bai or None, modality, content, emb, meta or None, content),
            )
            n += 1
            if n % 1000 == 0:
                conn.commit()
    conn.commit()
    return n


def restore_dump(dsn: str, dump_path: Path) -> None:
    subprocess.run(
        ["pg_restore", "--data-only", "--no-owner", "--no-privileges", "--exit-on-error",
         "-t", "chunks", "-d", dsn, str(dump_path)],
        check=True,
    )


def post_process(conn) -> None:
    """Make figure paths relative and fill tsv where missing."""
    with conn.cursor() as cur:
        cur.execute(FIX_FIGURE_PATH_SQL)
        cur.execute("UPDATE chunks SET tsv = to_tsvector('simple', content) WHERE tsv IS NULL")
        cur.execute("ANALYZE chunks")
    conn.commit()


def default_dsn() -> str:
    env = os.environ
    return env.get("SGK_LOAD_DSN") or (
        f"postgresql://{env.get('DB_USER', 'postgres')}:{env.get('DB_PASSWORD', '')}"
        f"@{env.get('DB_HOST', 'localhost')}:{env.get('DB_PORT', '5432')}/{env.get('DB_NAME', 'teacher_assistance')}"
    )


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rag-root", default=os.environ.get("RAG_SGK_ROOT"), help="RAG_SGK project root")
    ap.add_argument("--dsn", default=None)
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--dump", help="pg_dump custom-format file (needs pg_restore)")
    src.add_argument("--csv", help="chunks.csv fallback")
    ap.add_argument("--docs-only", action="store_true")
    ap.add_argument("--force", action="store_true", help="load chunks even if the table is not empty")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if not args.rag_root:
        ap.error("--rag-root (or env RAG_SGK_ROOT) is required")
    dsn = args.dsn or default_dsn()
    conn = psycopg2.connect(dsn)
    try:
        docs = discover_docs(Path(args.rag_root))
        logger.info("sgk_docs upserted: %d", upsert_docs(conn, docs))
        if args.docs_only or not (args.dump or args.csv):
            return 0
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM chunks")
            existing = cur.fetchone()[0]
        if existing and not args.force:
            logger.warning("chunks already has %d rows; skipping load (use --force)", existing)
        elif args.dump:
            restore_dump(dsn, Path(args.dump))
        else:
            logger.info("chunks loaded from csv: %d", load_csv(conn, Path(args.csv)))
        post_process(conn)
        from app.scripts.backfill_sgk_chapters import backfill
        logger.info("chapter backfill: %d chunks updated", sum(backfill(conn).values()))
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM chunks")
            logger.info("chunks rows: %d", cur.fetchone()[0])
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
