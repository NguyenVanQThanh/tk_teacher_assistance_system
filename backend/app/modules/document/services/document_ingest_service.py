# File Name: document_ingest_service.py
# Description: Background ingestion of uploaded documents: extract (PDF/DOCX/XLSX), VLM transcription, chunking, embedding into document_chunks.
# Created At: 2026-11-11
# Created By: AI Agent
# Updated At: 2026-11-11
# Updated By: AI Agent

import io
import json
import logging
import re
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import httpx
from PIL import Image
from sqlalchemy import text

from app.core import config
from app.modules.exercise.services.mistral_vision_parser_service import (
    MistralVisionParserService,
    flatten_content,
    raise_for_status_logged,
)

logger = logging.getLogger("smartlms.document.ingest")

UPLOAD_DIR = Path("uploads/documents")
MIN_TOK, MAX_TOK = 300, 500
MAX_RETRIES = 3
_MATH = re.compile(r"\$\$.+?\$\$|\$[^$\n]+?\$", re.S)
_FIGURE_LINE = re.compile(r"^\s*>?\s*\[(?:HINH|HÌNH|FIGURE)\s*:\s*(.+?)\]\s*$", re.I | re.M)

VLM_SYSTEM_PROMPT = (
    "Bạn là công cụ chép lại tài liệu giảng dạy từ ảnh trang. Hãy chép NGUYÊN VĂN toàn bộ nội dung trang "
    "dưới dạng markdown trung thực: giữ nguyên tiêu đề (dùng #), công thức toán/lý viết bằng LaTeX trong $...$ "
    "(công thức độc lập trong $$...$$), công thức hóa học viết đúng chỉ số và điện tích (ví dụ $H_2SO_4$, $Fe^{3+}$), "
    "bảng viết dạng bảng markdown. Với mỗi hình vẽ/đồ thị/sơ đồ, thêm MỘT dòng đúng dạng "
    "[HÌNH: chú thích ngắn bằng tiếng Việt mô tả hình] tại vị trí của hình. "
    "Không bịa, không tóm tắt, không giải thích thêm. Chỉ trả về markdown."
)


# ---------------------------------------------------------------- chunking
def est_tokens(s: str) -> int:
    """Cheap token estimate (~4 chars per token)."""
    return max(1, len(s) // 4)


def _blocks(md: str):
    """Yield (kind, text) with kind in heading|table|para; a $$ block never breaks on blank lines."""
    buf: List[str] = []
    in_math = False

    def flush():
        if buf:
            kind = "table" if buf[0].lstrip().startswith("|") else "para"
            out = (kind, "\n".join(buf))
            buf.clear()
            return out
        return None

    for line in md.splitlines():
        s = line.strip()
        if in_math:
            buf.append(line)
            if s.count("$$") % 2 == 1:
                in_math = False
            continue
        if not s:
            r = flush()
            if r:
                yield r
        elif s.startswith("#"):
            r = flush()
            if r:
                yield r
            yield "heading", s
        elif s.startswith("|"):
            if buf and not buf[0].lstrip().startswith("|"):
                r = flush()
                if r:
                    yield r
            buf.append(line)
        else:
            if buf and buf[0].lstrip().startswith("|"):
                r = flush()
                if r:
                    yield r
            buf.append(line)
            if s.count("$$") % 2 == 1:
                in_math = True
    r = flush()
    if r:
        yield r


def _split_big(t: str) -> List[str]:
    """Split an oversized paragraph at sentence ends outside math."""
    spans: List[str] = []

    def mask(m):
        spans.append(m.group(0))
        return f"\x00{len(spans) - 1}\x00"

    masked = _MATH.sub(mask, t)
    out: List[str] = []
    cur = ""
    for sent in re.split(r"(?<=[.!?])\s+", masked):
        if cur and est_tokens(cur + sent) > MAX_TOK:
            out.append(cur)
            cur = ""
        cur = f"{cur} {sent}".strip()
    if cur:
        out.append(cur)
    return [re.sub(r"\x00(\d+)\x00", lambda m: spans[int(m.group(1))], o) for o in out]


def extract_figures(markdown: str) -> Tuple[str, List[str]]:
    """Remove [HÌNH: caption] lines from markdown; return (clean markdown, captions)."""
    caps = [c.strip() for c in _FIGURE_LINE.findall(markdown or "") if c.strip()]
    return _FIGURE_LINE.sub("", markdown or ""), caps


def chunk_page(page: int, markdown: str, figures: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """Chunk one page into text/table/image chunks: dicts {page, modality, content, meta}."""
    out: List[Dict[str, Any]] = []
    buf: List[str] = []

    def add(modality, content, meta=None):
        out.append({"page": page, "modality": modality, "content": content, "meta": meta or {}})

    def flush():
        if buf:
            add("text", "\n\n".join(buf))
            buf.clear()

    for kind, t in _blocks(markdown or ""):
        if kind == "heading":
            flush()
            buf.append(t)
        elif kind == "table":
            flush()
            add("table", t)
        else:
            for p in (_split_big(t) if est_tokens(t) > MAX_TOK else [t]):
                cur = est_tokens("\n\n".join(buf))
                if buf and cur >= MIN_TOK and cur + est_tokens(p) > MAX_TOK:
                    flush()
                buf.append(p)
    flush()
    for f in figures or []:
        cap = (f.get("caption") or "").strip()
        if cap:
            add("image", cap, {"figure_path": f.get("path")})
    return out


# ---------------------------------------------------------------- extraction
def render_pdf_pages(file_bytes: bytes, dpi: int) -> List[Image.Image]:
    """Render every PDF page to a PIL image at the given DPI (pypdfium2, already a dependency)."""
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(file_bytes)
    return [page.render(scale=dpi / 72.0).to_pil() for page in pdf]


def vlm_transcribe(img: Image.Image, page_no: int, post: Optional[Callable[[dict, dict], str]] = None) -> str:
    """Send one page image to the VLM; return raw markdown. Retries with backoff, raises on final failure."""
    api_key = MistralVisionParserService.get_api_key()
    if not api_key:
        raise RuntimeError("MISTRAL_API_KEY is not configured.")
    payload = {
        "model": MistralVisionParserService.get_model_name(),
        "messages": [
            {"role": "system", "content": VLM_SYSTEM_PROMPT},
            {"role": "user", "content": [
                {"type": "text", "text": f"Trang {page_no}. Hãy chép lại toàn bộ nội dung trang này."},
                {"type": "image_url", "image_url": {"url": MistralVisionParserService._image_to_data_url(img)}},
            ]},
        ],
        "temperature": 0.02,
        "reasoning_effort": "low",
        "max_tokens": MistralVisionParserService.get_max_tokens(),
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    def _default_post(p: dict, h: dict) -> str:
        with httpx.Client(timeout=httpx.Timeout(connect=15.0, read=180.0, write=60.0, pool=15.0)) as c:
            r = c.post(MistralVisionParserService.get_api_url(), json=p, headers=h)
            raise_for_status_logged(r)
            return flatten_content(r.json()["choices"][0]["message"]["content"])

    return _with_retry(lambda: (post or _default_post)(payload, headers), f"VLM page {page_no}")


def _with_retry(fn: Callable[[], Any], label: str, base_delay: float = 2.0) -> Any:
    """Run fn with exponential backoff; re-raise the last error."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return fn()
        except Exception as exc:
            if attempt == MAX_RETRIES:
                raise
            delay = base_delay * (2 ** (attempt - 1))
            logger.warning("%s failed (attempt %d/%d): %s; retrying in %.1fs", label, attempt, MAX_RETRIES, exc, delay)
            time.sleep(delay)


def save_figure(img: Image.Image, document_id: str, page: int) -> str:
    """Store a page image under uploads/documents_figures/<document_id>/ and return its path."""
    folder = Path(config.DOCUMENT_FIGURE_DIR) / str(document_id)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"p{page}.png"
    img.save(path, format="PNG")
    return str(path).replace("\\", "/")


def pages_from_pdf(file_bytes: bytes, document_id: str, vlm: Callable = vlm_transcribe) -> List[Dict[str, Any]]:
    """VLM every PDF page -> [{page, markdown, figures}]."""
    pages = []
    for i, img in enumerate(render_pdf_pages(file_bytes, config.DOCUMENT_RENDER_DPI), 1):
        md, caps = extract_figures(vlm(img, i))
        figures = []
        if caps:
            fpath = save_figure(img, document_id, i)
            figures = [{"caption": c, "path": fpath} for c in caps]
        pages.append({"page": i, "markdown": md, "figures": figures})
    return pages


def pages_from_docx(file_bytes: bytes, document_id: str, vlm: Callable = vlm_transcribe) -> List[Dict[str, Any]]:
    """python-docx: paragraphs and tables as markdown; embedded images sent to the VLM as figures."""
    import docx

    d = docx.Document(io.BytesIO(file_bytes))
    lines = [p.text for p in d.paragraphs if p.text.strip()]
    for tbl in d.tables:
        rows = [[c.text.strip().replace("\n", " ") for c in r.cells] for r in tbl.rows]
        if rows:
            lines.append("")
            lines.append("| " + " | ".join(rows[0]) + " |")
            lines.append("|" + " --- |" * len(rows[0]))
            lines += ["| " + " | ".join(r) + " |" for r in rows[1:]]
            lines.append("")
    figures = []
    for n, rel in enumerate(r for r in d.part.rels.values() if "image" in r.reltype):
        try:
            img = Image.open(io.BytesIO(rel.target_part.blob)).convert("RGB")
        except Exception as exc:
            logger.warning("Skipping unreadable docx image %d: %s", n, exc)
            continue
        md, caps = extract_figures(vlm(img, n + 1))
        path = save_figure(img, document_id, 1000 + n)
        caption = " ".join(caps) or md.strip()
        if caption:
            figures.append({"caption": caption, "path": path})
    return [{"page": 1, "markdown": "\n".join(lines), "figures": figures}]


def pages_from_xlsx(file_bytes: bytes) -> List[Dict[str, Any]]:
    """openpyxl: one page per sheet, rendered as a markdown table."""
    import openpyxl

    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True, read_only=True)
    pages = []
    for i, ws in enumerate(wb.worksheets, 1):
        rows = [["" if v is None else str(v).replace("\n", " ") for v in r] for r in ws.iter_rows(values_only=True)]
        rows = [r for r in rows if any(c.strip() for c in r)]
        if not rows:
            continue
        w = max(len(r) for r in rows)
        rows = [r + [""] * (w - len(r)) for r in rows]
        md = [f"## {ws.title}", "", "| " + " | ".join(rows[0]) + " |", "|" + " --- |" * w]
        md += ["| " + " | ".join(r) + " |" for r in rows[1:]]
        pages.append({"page": i, "markdown": "\n".join(md), "figures": []})
    return pages


# ---------------------------------------------------------------- embedding
def embed_texts(texts: List[str], post: Optional[Callable[[dict, dict], List[List[float]]]] = None) -> List[List[float]]:
    """Embed texts with mistral-embed in batches; retry with backoff."""
    api_key = MistralVisionParserService.get_api_key()
    if not api_key:
        raise RuntimeError("MISTRAL_API_KEY is not configured.")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    def _default_post(p: dict, h: dict) -> List[List[float]]:
        with httpx.Client(timeout=60.0) as c:
            r = c.post(config.MISTRAL_EMBED_URL, json=p, headers=h)
            raise_for_status_logged(r)
            data = sorted(r.json()["data"], key=lambda x: x["index"])
            return [d["embedding"] for d in data]

    out: List[List[float]] = []
    size = max(1, config.EMBED_BATCH_SIZE)
    for i in range(0, len(texts), size):
        payload = {"model": config.MISTRAL_EMBED_MODEL, "input": texts[i:i + size]}
        out += _with_retry(lambda: (post or _default_post)(payload, headers), f"embed batch {i // size}")
    return out


def _vec_literal(v: List[float]) -> str:
    return "[" + ",".join(f"{x:.7g}" for x in v) + "]"


# ---------------------------------------------------------------- service
class DocumentIngestService:
    """Extract, VLM-read, chunk, embed and store a document into document_chunks."""

    @staticmethod
    def _set_status(db, document_id, ingest_status: str, error: Optional[str] = None) -> None:
        db.execute(
            text("UPDATE documents SET ingest_status = :s, ingest_error = :e WHERE document_id = :id"),
            {"s": ingest_status, "e": error, "id": str(document_id)},
        )
        db.commit()

    @staticmethod
    def mark_pending(db, document_id) -> None:
        """Set ingest_status = PENDING (used at upload and re-trigger)."""
        DocumentIngestService._set_status(db, document_id, "PENDING")

    @staticmethod
    def set_chunks_status(db, document_id, chunk_status: str) -> None:
        """Soft-delete (DELETED) or restore (ACTIVE) all chunks of a document. Caller commits."""
        src = "ACTIVE" if chunk_status == "DELETED" else "DELETED"
        db.execute(
            text("UPDATE document_chunks SET status = :s WHERE document_id = :id AND status = :src"),
            {"s": chunk_status, "id": str(document_id), "src": src},
        )

    @staticmethod
    def build_chunks(file_type: str, file_bytes: bytes, document_id: str, vlm: Callable = vlm_transcribe) -> List[Dict[str, Any]]:
        """Extract pages by file type and chunk them."""
        ft = (file_type or "").lower()
        if ft == "pdf":
            pages = pages_from_pdf(file_bytes, document_id, vlm)
        elif ft == "docx":
            pages = pages_from_docx(file_bytes, document_id, vlm)
        elif ft == "xlsx":
            pages = pages_from_xlsx(file_bytes)
        else:
            raise ValueError(f"Unsupported file type for ingestion: .{ft}")
        chunks: List[Dict[str, Any]] = []
        for p in sorted(pages, key=lambda x: x["page"]):
            chunks += chunk_page(p["page"], p["markdown"], p["figures"])
        return chunks

    @staticmethod
    def ingest(document_id, session_factory: Optional[Callable] = None) -> None:
        """Run full ingestion with its own DB session (FastAPI BackgroundTask entry point)."""
        if session_factory is None:
            from app.core.database import SessionLocal as session_factory
        db = session_factory()
        try:
            DocumentIngestService._run(db, document_id)
        finally:
            db.close()

    @staticmethod
    def _run(db, document_id) -> None:
        row = db.execute(
            text("SELECT file_url, file_type FROM documents WHERE document_id = :id"), {"id": str(document_id)}
        ).first()
        if row is None:
            logger.error("Ingest skipped, document not found: %s", document_id)
            return
        DocumentIngestService._set_status(db, document_id, "PROCESSING")
        try:
            path = UPLOAD_DIR / Path(row[0] or "").name
            if not path.exists():
                raise FileNotFoundError(f"Stored file missing: {path.name}")
            chunks = DocumentIngestService.build_chunks(row[1], path.read_bytes(), str(document_id))
            if not chunks:
                raise ValueError("No content could be extracted from the document.")
            vectors = embed_texts([c["content"] for c in chunks])
            if len(vectors) != len(chunks):
                raise RuntimeError("Embedding count does not match chunk count.")

            # Idempotent: soft-delete previous chunks, never hard delete.
            db.execute(
                text("UPDATE document_chunks SET status = 'DELETED' WHERE document_id = :id AND status <> 'DELETED'"),
                {"id": str(document_id)},
            )
            for c, v in zip(chunks, vectors):
                db.execute(
                    text(
                        "INSERT INTO document_chunks (chunk_id, document_id, page, modality, content, embedding, meta, tsv, status) "
                        "VALUES (:cid, :did, :page, :mod, :content, CAST(:emb AS vector), CAST(:meta AS jsonb), "
                        "to_tsvector('simple', :content), 'ACTIVE')"
                    ),
                    {"cid": str(uuid.uuid4()), "did": str(document_id), "page": c["page"], "mod": c["modality"],
                     "content": c["content"], "emb": _vec_literal(v), "meta": json.dumps(c["meta"], ensure_ascii=False)},
                )
            db.commit()
            DocumentIngestService._set_status(db, document_id, "DONE")
            logger.info("Ingest done: document=%s chunks=%d", document_id, len(chunks))
        except Exception as exc:
            db.rollback()
            logger.error("Ingest failed: document=%s error=%s", document_id, exc, exc_info=True)
            DocumentIngestService._set_status(db, document_id, "FAILED", str(exc)[:2000])
