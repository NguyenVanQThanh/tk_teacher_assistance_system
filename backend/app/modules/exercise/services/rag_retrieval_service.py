"""
File Name: rag_retrieval_service.py
Description: Hybrid (dense + full-text, RRF-fused) retrieval over SGK textbook chunks and teacher document chunks.
Created At: 2026-11-11
Created By: AI Agent
Updated At: 2026-11-13
Updated By: AI Agent
"""
import json
import logging
import os
import re
import threading
import unicodedata
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core import config

logger = logging.getLogger(__name__)

POOL_SIZE = 50
RRF_K = 60
MAX_FTS_TERMS = 20

# Ordered (regex on ASCII-folded lowercase text, subject_key). First match wins.
_SUBJECT_PATTERNS: List[Tuple[str, str]] = [
    (r"\bcong nghe\b", "cong_nghe"),
    (r"\bkinh te\b|\bphap luat\b|\bgdktpl\b|\bgdcd\b", "gdktpl"),
    (r"\btoan\b", "toan"),
    (r"\bvat (ly|li)\b", "vat_li"),
    (r"\bhoa( hoc)?\b", "hoa_hoc"),
    (r"\bsinh( hoc)?\b", "sinh_hoc"),
    (r"\blich su\b", "lich_su"),
    (r"\bdia (ly|li)\b", "dia_li"),
    (r"\bngu van\b|\bvan hoc\b", "ngu_van"),
    (r"\btieng anh\b|\banh van\b", "tieng_anh"),
    (r"\btin hoc\b", "tin_hoc"),
]


@dataclass
class RagChunk:
    """One retrieved context chunk, from the SGK store or a teacher document."""
    source: str  # 'sgk' | 'teacher'
    ref: str
    page: Optional[int]
    modality: str  # text | table | image
    content: str
    image_path: Optional[str]
    score: float
    title: Optional[str] = None  # document title without page suffix
    document_id: Optional[str] = None  # teacher document id (None for SGK)


def to_image_url(path: Optional[str]) -> Optional[str]:
    """Map a stored figure path ('images/<doc_id>/pN_fK.png') to its public URL under the SGK image prefix."""
    if not path:
        return None
    rel = str(path).replace("\\", "/").lstrip("/")
    if rel.startswith("images/"):
        rel = rel[len("images/"):]
    return f"{config.SGK_IMAGE_URL_PREFIX}/{rel}"


def fold_text(value: str) -> str:
    """Lowercase and strip Vietnamese diacritics (including d-bar)."""
    value = (value or "").replace("đ", "d").replace("Đ", "D")
    value = unicodedata.normalize("NFD", value)
    value = "".join(c for c in value if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def subject_key_from_text(value: Optional[str]) -> Optional[str]:
    """Map a Vietnamese subject name or textbook file name to a normalized subject_key."""
    folded = fold_text(value or "")
    for pattern, key in _SUBJECT_PATTERNS:
        if re.search(pattern, folded):
            return key
    return None


def parse_grade(value: Any) -> Optional[int]:
    """Parse '10'/'11'/'12', 'Lop 12', 'Khoi 12' or an int into 10, 11 or 12."""
    match = re.search(r"(?<!\d)(10|11|12)(?!\d)", str(value if value is not None else ""))
    return int(match.group(1)) if match else None


def rrf_fuse(rank_lists: Sequence[Sequence[Any]], k: int = RRF_K) -> List[Tuple[Any, float]]:
    """Reciprocal Rank Fusion; returns (key, score) sorted by score desc (ties keep first-seen order)."""
    scores: Dict[Any, float] = {}
    for ranking in rank_lists:
        for rank, key in enumerate(ranking, start=1):
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda kv: -kv[1])


def build_fts_query(query: str, max_terms: int = MAX_FTS_TERMS) -> str:
    """Build an OR-joined to_tsquery('simple') string from free text; '' when no usable term."""
    seen: List[str] = []
    for tok in re.findall(r"\w+", (query or "").lower()):
        if tok not in seen:
            seen.append(tok)
        if len(seen) >= max_terms:
            break
    return " | ".join(seen)


def vector_literal(embedding: Sequence[float]) -> str:
    """Format an embedding as a pgvector text literal."""
    return "[" + ",".join(repr(float(x)) for x in embedding) + "]"


def build_search_sql(source: str, scope: bool = False, filter_docs: bool = False,
                     chapters: bool = False) -> Tuple[str, str]:
    """Return (dense_sql, fts_sql) for 'sgk' or 'teacher'.

    Filters live inside the query so HNSW iterative scan can keep scanning until enough rows match.
    Bind params: :pool, :vec (dense) or :q (fts); :doc_ids for sgk; for teacher optionally
    :document_ids, and :subject_id + :teacher_ids when scope is set. For sgk, chapters=True also pushes
    `c.chuong = ANY(:chapters)` into both queries.
    """
    if source == "sgk":
        cols = ("SELECT c.id AS cid, c.doc_id AS doc, c.page, c.modality, c.content, c.meta, "
                "(SELECT s.title FROM sgk_docs s WHERE s.doc_id = c.doc_id) AS title FROM chunks c ")
        where = "WHERE c.doc_id = ANY(:doc_ids) "
        if chapters:
            where += "AND c.chuong = ANY(:chapters) "
    else:
        cols = ("SELECT c.chunk_id::text AS cid, c.document_id::text AS doc, c.page, c.modality, c.content, "
                "c.meta, d.title AS title FROM document_chunks c "
                "JOIN documents d ON d.document_id = c.document_id ")
        where = "WHERE c.status = 'ACTIVE' AND d.status = 'Uploaded' "
        if filter_docs:
            where += "AND c.document_id = ANY(CAST(:document_ids AS uuid[])) "
        if scope:
            where += ("AND d.subject_id = CAST(:subject_id AS uuid) "
                      "AND d.uploaded_by = ANY(CAST(:teacher_ids AS uuid[])) ")
    dense = cols + where + "ORDER BY c.embedding <=> CAST(:vec AS vector) LIMIT :pool"
    fts = (cols + where + "AND c.tsv @@ to_tsquery('simple', :q) "
           "ORDER BY ts_rank(c.tsv, to_tsquery('simple', :q)) DESC LIMIT :pool")
    return dense, fts


def _mistral_key() -> Optional[str]:
    return os.environ.get("MISTRAL_API_KEY") or os.environ.get("MISTRAL_KEY")


def _gemini_key() -> Optional[str]:
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_KEY")


# Query -> embedding cache (bounded LRU). Manual instead of functools.lru_cache so one batched API call
# can fill several entries at once.
_EMBED_CACHE_SIZE = 512
_embed_cache: "OrderedDict[str, List[float]]" = OrderedDict()
_embed_lock = threading.Lock()

def _embed_many(queries: Sequence[str]) -> List[Optional[List[float]]]:
    """Embed queries with ONE Mistral call for all cache misses; None entries mean FTS-only fallback."""
    out: List[Optional[List[float]]] = [None] * len(queries)
    missing: List[str] = []
    with _embed_lock:
        for i, q in enumerate(queries):
            if q in _embed_cache:
                _embed_cache.move_to_end(q)
                out[i] = _embed_cache[q]
            elif q not in missing:
                missing.append(q)
    if missing:
        key = _mistral_key()
        if not key:
            logger.warning("RAG embedding skipped: Mistral API key not configured")
            return out
        try:
            from mistralai.client import Mistral
            resp = Mistral(api_key=key).embeddings.create(model=config.MISTRAL_EMBED_MODEL, inputs=list(missing))
            fresh = {q: list(d.embedding) for q, d in zip(missing, resp.data)}
        except Exception as exc:  # noqa: BLE001 - degrade to FTS-only
            logger.warning("RAG embedding failed, using full-text only: %s", exc)
            return out
        with _embed_lock:
            for q, emb in fresh.items():
                _embed_cache[q] = emb
                _embed_cache.move_to_end(q)
            while len(_embed_cache) > _EMBED_CACHE_SIZE:
                _embed_cache.popitem(last=False)
        for i, q in enumerate(queries):
            if out[i] is None:
                out[i] = fresh.get(q)
    return out

def _embed(query: str) -> Optional[List[float]]:
    """Embed one query (cached); None (FTS-only fallback) on any failure."""
    return _embed_many([query])[0]

_UNSET: Any = object()

def _llm_text(prompt: str) -> Optional[str]:
    """One short LLM completion (Gemini first, then Mistral); None when no key is configured."""
    key = _gemini_key()
    if key:
        from google import genai
        resp = genai.Client(api_key=key).models.generate_content(
            model=config.RAG_QUERY_EXPANSION_GEMINI_MODEL, contents=prompt)
        return resp.text
    key = _mistral_key()
    if key:
        from mistralai.client import Mistral
        resp = Mistral(api_key=key).chat.complete(
            model=config.RAG_QUERY_EXPANSION_MISTRAL_MODEL, messages=[{"role": "user", "content": prompt}])
        return resp.choices[0].message.content
    return None


class RagRetrievalService:
    """Hybrid retrieval over SGK textbooks and teacher-uploaded documents."""

    @staticmethod
    def resolve_sgk_filter(db: Session, subject_name: Optional[str], grade: Any) -> List[str]:
        """Return sgk_docs doc_ids matching subject + grade (may be several, e.g. Math vol. 1 and 2)."""
        key = subject_key_from_text(subject_name)
        grade_num = parse_grade(grade)
        if not key or not grade_num:
            return []
        rows = db.execute(
            text("SELECT doc_id FROM sgk_docs WHERE subject_key = :k AND grade = :g AND status = 'ACTIVE'"),
            {"k": key, "g": grade_num},
        ).fetchall()
        return [r[0] for r in rows]

    @staticmethod
    def _hybrid(db: Session, source: str, query: str, params: Dict[str, Any], k: int,
                scope: bool = False, filter_docs: bool = False, chapters: bool = False,
                embedding: Any = _UNSET) -> List[RagChunk]:
        dense_sql, fts_sql = build_search_sql(source, scope=scope, filter_docs=filter_docs, chapters=chapters)
        params = {**params, "pool": POOL_SIZE}
        rows: Dict[str, Any] = {}
        rankings: List[List[str]] = []

        if embedding is _UNSET:
            embedding = _embed(query)
        if embedding is not None:
            try:
                # SET LOCAL lasts until the surrounding transaction ends; older pgvector lacks the setting.
                try:
                    with db.begin_nested():
                        db.execute(text("SET LOCAL hnsw.iterative_scan = relaxed_order"))
                except Exception:  # noqa: BLE001
                    logger.warning("hnsw.iterative_scan unavailable, filtered recall may drop")
                res = db.execute(text(dense_sql), {**params, "vec": vector_literal(embedding)}).fetchall()
                rankings.append([r.cid for r in res])
                rows.update({r.cid: r for r in res})
            except Exception as exc:  # noqa: BLE001
                logger.warning("RAG dense search failed: %s", exc)

        fts_q = build_fts_query(query)
        if fts_q:
            try:
                res = db.execute(text(fts_sql), {**params, "q": fts_q}).fetchall()
                rankings.append([r.cid for r in res])
                rows.update({r.cid: r for r in res})
            except Exception as exc:  # noqa: BLE001
                logger.warning("RAG full-text search failed: %s", exc)

        out: List[RagChunk] = []
        for cid, score in rrf_fuse(rankings)[:k]:
            r = rows[cid]
            meta = r.meta or {}
            label = str(r.title or r.doc)
            out.append(RagChunk(
                source=source,
                ref=f"{label}, p.{r.page}" if r.page is not None else label,
                page=r.page,
                modality=r.modality,
                content=r.content,
                image_path=to_image_url(meta.get("figure_path") or meta.get("image_path")) if source == "sgk"
                else (meta.get("figure_path") or meta.get("image_path")),
                score=score,
                title=label,
                document_id=str(r.doc) if source == "teacher" else None,
            ))
        return out

    @staticmethod
    def _embed_query(query: str) -> Optional[List[float]]:
        """Embed once (cached) so several searches can share the vector."""
        return _embed_many([query])[0]

    @staticmethod
    def list_chapters(db: Session, doc_ids: Sequence[str]) -> List[Dict[str, Any]]:
        """Return [{chapter, doc_id, page_start}] for the given SGK docs, ordered by doc then first page."""
        if not doc_ids:
            return []
        rows = db.execute(
            text("SELECT doc_id, chuong, min(page) AS page_start FROM chunks "
                 "WHERE doc_id = ANY(:ids) AND chuong IS NOT NULL GROUP BY doc_id, chuong "
                 "ORDER BY doc_id, 3"),
            {"ids": list(doc_ids)},
        ).fetchall()
        return [{"chapter": r[1], "doc_id": r[0], "page_start": r[2]} for r in rows]

    @classmethod
    def search_sgk(cls, db: Session, query: str, subject_name: Optional[str], grade: Any,
                   k: int = 5, chapters: Optional[Sequence[str]] = None,
                   embedding: Any = _UNSET) -> List[RagChunk]:
        """Search textbook chunks for the given subject and grade; [] when no matching textbook.

        chapters, when given, is pushed down into the SQL (`chuong = ANY(:chapters)`).
        """
        if not (query or "").strip():
            return []
        doc_ids = cls.resolve_sgk_filter(db, subject_name, grade)
        if not doc_ids:
            return []
        params: Dict[str, Any] = {"doc_ids": doc_ids}
        if chapters:
            params["chapters"] = list(chapters)
        return cls._hybrid(db, "sgk", query, params, k, chapters=bool(chapters), embedding=embedding)

    @classmethod
    def search_documents(
        cls,
        db: Session,
        query: str,
        document_ids: Optional[Sequence[Any]] = None,
        teacher_subject_scope: Optional[Tuple[Any, Sequence[Any]]] = None,
        k: int = 5,
        embedding: Any = _UNSET,
    ) -> List[RagChunk]:
        """Search teacher document chunks (ACTIVE chunks of Uploaded documents).

        teacher_subject_scope=(subject_id, teacher_ids) keeps only documents of that subject uploaded by those
        teachers. document_ids, when given, further restricts to those documents.
        """
        if not (query or "").strip():
            return []
        params: Dict[str, Any] = {}
        scope = teacher_subject_scope is not None
        if scope:
            subject_id, teacher_ids = teacher_subject_scope
            if not teacher_ids:
                return []
            params["subject_id"] = str(subject_id)
            params["teacher_ids"] = [str(t) for t in teacher_ids]
        filter_docs = document_ids is not None
        if filter_docs:
            if not document_ids:
                return []
            params["document_ids"] = [str(d) for d in document_ids]
        return cls._hybrid(db, "teacher", query, params, k, scope=scope, filter_docs=filter_docs,
                           embedding=embedding)

    @staticmethod
    def expand_query(topic_prompt: str) -> List[str]:
        """Return up to 3 sub-queries for a topic prompt; falls back to [topic_prompt]. Never raises."""
        fallback = [topic_prompt]
        if not config.RAG_QUERY_EXPANSION_ENABLED or not (topic_prompt or "").strip():
            return fallback
        try:
            raw = _llm_text(
                "Split this exam topic request into at most 3 short, distinct search queries for a textbook "
                "search. Keep the original language. Return only a JSON array of strings.\n\nRequest: "
                + topic_prompt)
            if not raw:
                return fallback
            match = re.search(r"\[.*\]", raw, re.S)
            items = json.loads(match.group(0)) if match else []
            subs = [s.strip() for s in items if isinstance(s, str) and s.strip()][:3]
            return subs or fallback
        except Exception as exc:  # noqa: BLE001
            logger.warning("RAG query expansion failed, using raw prompt: %s", exc)
            return fallback
