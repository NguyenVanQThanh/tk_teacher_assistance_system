# File Name: apply_sgk_labels.py
# Description: Apply table-of-contents chapter/lesson labels (data/sgk_labels.csv) to SGK chunks, idempotent.
# Created At: 2026-11-17
# Created By: AI Agent
# Updated At: 2026-11-17
# Updated By: AI Agent
"""Relabel `chunks.chuong` / `chunks.bai` per (doc_id, page) from a CSV built by RAG_SGK/scripts/relabel_db.py.

The restored vectors.dump carries the OCR-heading labels, which are wrong for many books. The CSV is
authoritative. Rows already correct are not touched, so running this on every start is cheap.
"""
import csv
import sys
from pathlib import Path

backend_root = str(Path(__file__).resolve().parent.parent.parent)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from sqlalchemy import text

CSV_PATH = Path(backend_root) / "data" / "sgk_labels.csv"
UPDATE = text(
    "UPDATE chunks SET chuong = :chuong, bai = :bai "
    "WHERE doc_id = :doc_id AND page = :page "
    "AND (chuong IS DISTINCT FROM :chuong OR bai IS DISTINCT FROM :bai)"
)


def apply_labels(db, path: Path = CSV_PATH) -> int:
    """Update chunks from the CSV; return the number of changed rows. Caller commits."""
    if not path.exists():
        return 0
    with path.open(encoding="utf-8", newline="") as fh:
        rows = [
            {"doc_id": r["doc_id"], "page": int(r["page"]),
             "chuong": r["chuong"] or None, "bai": r["bai"] or None}
            for r in csv.DictReader(fh)
        ]
    changed = 0
    for r in rows:
        changed += db.execute(UPDATE, r).rowcount
    return changed


def main() -> int:
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        if not db.execute(text("SELECT 1 FROM chunks LIMIT 1")).first():
            print("apply_sgk_labels: chunks empty, nothing to label")
            return 0
        changed = apply_labels(db)
        db.commit()
    except Exception as exc:  # noqa: BLE001 - labels are cosmetic; never block startup
        db.rollback()
        print(f"apply_sgk_labels: WARNING - skipped: {exc}")
        return 0
    finally:
        db.close()
    print(f"apply_sgk_labels: updated {changed} chunk row(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
