"""
File Name: backfill_sgk_chapters.py
Description: Idempotent backfill of chunks.chuong for SGK textbook chunks from chapter headings found in the text.
Created At: 2026-11-13
Created By: AI Agent
Updated At: 2026-11-13
Updated By: AI Agent

Usage (from backend/ or inside smartlms_backend):
    python -m app.scripts.backfill_sgk_chapters [--dsn DSN] [--force]

Rules: a page "starts" chapter N when one of its text chunks begins with a heading such as
"CHUONG 1 ...", "Chuong II. ..." or "CHU DE 3 ...". Start pages are resolved in sequence (start(1) = first page with
chapter 1, start(n) = first page after start(n-1) with chapter n), which drops table-of-contents and running-header
noise. Page p gets the latest chapter n with start(n) <= p, stored as "Chuong N: TITLE". Documents with fewer than two
chapter numbers fall back to "Bai N" / "Unit N" headings. Pages before chapter 1 stay NULL. Documents that already
have chuong values are skipped unless --force. Connection comes from --dsn, env SGK_LOAD_DSN or DB_* env vars only.
"""
import argparse
import logging
import re
from collections import Counter
from typing import Dict, List, Optional, Sequence, Tuple

import psycopg2

from app.scripts.load_sgk_rag import default_dsn

logger = logging.getLogger("backfill_sgk_chapters")

# Heading keyword -> display label. Matching is on the first line of a text chunk.
_PRIMARY_RE = re.compile(r"^\W*(CHƯƠNG|Chương|CHỦ ĐỀ|Chủ đề|PHẦN|Phần)\s+([IVXLC]+|\d+)\b[\s.:\-–—]*(.*)$")
_FALLBACK_RE = re.compile(r"^\W*(BÀI|Bài|UNIT|Unit)\s+(\d+)\b[\s.:\-–—]*(.*)$")
_LABELS = {"chương": "Chương", "chủ đề": "Chủ đề", "phần": "Phần", "bài": "Bài", "unit": "Unit"}
_ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}
MAX_TITLE_CHARS = 120


def parse_number(token: str) -> Optional[int]:
    """Parse an Arabic or Roman numeral token."""
    if token.isdigit():
        return int(token)
    total, prev = 0, 0
    for ch in reversed(token.upper()):
        value = _ROMAN.get(ch)
        if value is None:
            return None
        total += -value if value < prev else value
        prev = max(prev, value)
    return total or None


def match_heading(first_line: str, pattern: "re.Pattern[str]") -> Optional[Tuple[str, int, str]]:
    """Return (label, number, title) when the line is a chapter heading."""
    m = pattern.match((first_line or "").strip())
    if not m:
        return None
    number = parse_number(m.group(2))
    if number is None or number > 60:
        return None
    return _LABELS[m.group(1).lower()], number, m.group(3).strip(" .:-–—*#_")[:MAX_TITLE_CHARS]


def _resolve(page_lines: Dict[int, List[str]], pattern: "re.Pattern[str]") -> Dict[int, str]:
    """Map page -> chapter label using sequential start pages; {} when fewer than two chapter numbers exist."""
    found: Dict[int, List[Tuple[str, int, str]]] = {}
    for page, lines in page_lines.items():
        for line in lines:
            hit = match_heading(line, pattern)
            if hit:
                found.setdefault(page, []).append(hit)
    if not found:
        return {}
    # Use the dominant keyword (e.g. "Chương") so a stray "Phần" heading cannot derail the sequence.
    label = Counter(h[0] for hits in found.values() for h in hits).most_common(1)[0][0]
    numbers = sorted({h[1] for hits in found.values() for h in hits if h[0] == label})
    if len(numbers) < 2:
        return {}
    starts: List[Tuple[int, int, str]] = []  # (page, number, title)
    last_page = -1
    expected = numbers[0]
    for n in numbers:
        if n < expected:
            continue
        candidates = sorted(p for p, hits in found.items() if p >= last_page and any(h[0] == label and h[1] == n for h in hits))
        if n == numbers[0]:
            candidates = sorted(p for p, hits in found.items() if any(h[0] == label and h[1] == n for h in hits))
        else:
            candidates = [p for p in candidates if p > last_page]
        if not candidates:
            continue
        page = candidates[0]
        title = next(h[2] for h in found[page] if h[0] == label and h[1] == n)
        starts.append((page, n, title))
        last_page = page
    if len(starts) < 2:
        return {}
    out: Dict[int, str] = {}
    for page in sorted(page_lines):
        current = None
        for start_page, n, title in starts:
            if start_page <= page:
                current = (n, title)
        if current:
            out[page] = f"{label} {current[0]}: {current[1]}" if current[1] else f"{label} {current[0]}"
    return out


def compute_page_chapters(page_lines: Dict[int, Sequence[str]]) -> Dict[int, str]:
    """Compute page -> chuong for one document from the first lines of its text chunks per page."""
    lines = {p: list(v) for p, v in page_lines.items()}
    return _resolve(lines, _PRIMARY_RE) or _resolve(lines, _FALLBACK_RE)


def backfill(conn, force: bool = False) -> Dict[str, int]:
    """Backfill every sgk_docs document; returns {doc_id: chunks updated}."""
    result: Dict[str, int] = {}
    with conn.cursor() as cur:
        cur.execute("SELECT doc_id FROM sgk_docs ORDER BY doc_id")
        doc_ids = [r[0] for r in cur.fetchall()]
    for doc_id in doc_ids:
        with conn.cursor() as cur:
            if not force:
                cur.execute("SELECT 1 FROM chunks WHERE doc_id = %s AND chuong IS NOT NULL LIMIT 1", (doc_id,))
                if cur.fetchone():
                    result[doc_id] = 0
                    continue
            cur.execute(
                "SELECT page, split_part(content, E'\\n', 1) FROM chunks "
                "WHERE doc_id = %s AND modality = 'text' AND page IS NOT NULL", (doc_id,))
            page_lines: Dict[int, List[str]] = {}
            for page, first in cur.fetchall():
                page_lines.setdefault(page, []).append(first)
            cur.execute("SELECT DISTINCT page FROM chunks WHERE doc_id = %s AND page IS NOT NULL", (doc_id,))
            for (page,) in cur.fetchall():
                page_lines.setdefault(page, [])
            mapping = compute_page_chapters(page_lines)
            updated = 0
            if force:
                cur.execute("UPDATE chunks SET chuong = NULL WHERE doc_id = %s", (doc_id,))
            for page, chapter in mapping.items():
                cur.execute("UPDATE chunks SET chuong = %s WHERE doc_id = %s AND page = %s AND chuong IS NULL",
                            (chapter, doc_id, page))
                updated += cur.rowcount
        conn.commit()
        result[doc_id] = updated
        logger.info("doc %s: %d chapters, %d chunks updated", doc_id, len(set(mapping.values())), updated)
    return result


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dsn", default=None)
    ap.add_argument("--force", action="store_true", help="recompute even for documents that already have chuong")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    conn = psycopg2.connect(args.dsn or default_dsn())
    try:
        backfill(conn, force=args.force)
        with conn.cursor() as cur:
            cur.execute("ANALYZE chunks")
        conn.commit()
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
