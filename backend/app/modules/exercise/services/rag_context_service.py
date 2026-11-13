# File Name: rag_context_service.py
# Description: Builds the labeled RAG context (SGK textbook + teacher documents) fed to the AI exercise generator.
# Created At: 2026-11-11
# Created By: AI Agent
# Updated At: 2026-11-13
# Updated By: AI Agent

import logging
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from models.models import StudentClass, TeacherSubject, User
from app.modules.exercise.services.rag_retrieval_service import RagChunk, RagRetrievalService

logger = logging.getLogger("smartlms.exercise.rag_context")

SGK_K_PER_QUERY = 4
DOC_K_PER_QUERY = 3
MAX_CONTEXT_CHARS = 12000

# Student generation budgets (characters): textbook / class-teacher documents; the uploaded file budget
# (STUDENT_FILE_CHARS) is applied by the caller because the file goes into its own prompt block.
SGK_QUOTA_CHARS = 7000
TEACHER_QUOTA_CHARS = 3000
STUDENT_FILE_CHARS = 4000
SGK_K_PER_CHAPTER = 4
JACCARD_DUP_THRESHOLD = 0.8


class RagContextService:
    """Retrieve and format grounding context for AI question generation."""

    @classmethod
    def build_context(cls, db: Session, **kwargs) -> str:
        """Return only the context string (see build_context_with_sources)."""
        return cls.build_context_with_sources(db, **kwargs)[0]

    @classmethod
    def build_context_with_sources(
        cls,
        db: Session,
        *,
        topic_prompt: str,
        subject_name: str,
        grade_name: str,
        subject_id: Optional[UUID],
        role_name: str,
        class_id: Optional[UUID],
        document_ids: Optional[Sequence[UUID]] = None,
    ) -> Tuple[str, List[dict]]:
        """
        Return (context, sources); context is "" and sources [] when nothing is found or retrieval fails.

        SGK is always searched (filtered by grade and subject). Teacher documents are added as follows:
        Teacher/Admin -> only the documents they picked; Student -> documents of teachers who teach the same
        subject in the student's class (same subject only). Retrieval runs inside a savepoint so a SQL failure
        cannot poison the caller's transaction.
        """
        try:
            with db.begin_nested():
                queries = RagRetrievalService.expand_query(topic_prompt)
                chunks: List[RagChunk] = []
                for q in queries:
                    chunks += RagRetrievalService.search_sgk(db, q, subject_name, grade_name, k=SGK_K_PER_QUERY)

                doc_kwargs = cls._teacher_scope(db, role_name, subject_id, class_id, document_ids)
                if doc_kwargs is not None:
                    for q in queries:
                        chunks += RagRetrievalService.search_documents(db, q, k=DOC_K_PER_QUERY, **doc_kwargs)
            return cls.format_with_sources(chunks)
        except Exception as e:
            logger.warning("RAG retrieval failed, generating without context: %s", e)
            return "", []

    @classmethod
    def class_teacher_ids(cls, db: Session, student_id: UUID, subject_id: UUID) -> List[UUID]:
        """Active teachers of the student's own ACTIVE classes for the subject (never other classes' teachers)."""
        class_ids = [r[0] for r in db.query(StudentClass.class_id).filter(
            StudentClass.student_id == student_id, StudentClass.status == "ACTIVE").all()]
        if not class_ids:
            return []
        rows = db.query(TeacherSubject.teacher_id).join(User, User.user_id == TeacherSubject.teacher_id).filter(
            TeacherSubject.class_id.in_(class_ids),
            TeacherSubject.subject_id == subject_id,
            TeacherSubject.status == "ACTIVE",
            User.status == "Active",
        ).distinct().all()
        return [r[0] for r in rows]

    @classmethod
    def build_student_context(
        cls,
        db: Session,
        *,
        student_id: UUID,
        subject_id: UUID,
        subject_name: str,
        grade: Any,
        chapters: Sequence[str],
        topic_prompt: str,
    ) -> Tuple[str, List[dict]]:
        """
        Context for a student request: SGK restricted to the chosen chapters (pushed into SQL, round-robin across
        chapters) plus documents of the teachers of the student's own classes for that subject.
        No LLM query expansion; the queries are embedded in a single batched call. Returns ("", []) on failure.
        """
        try:
            with db.begin_nested():
                query = (topic_prompt or "").strip() or "; ".join(chapters)
                embedding = RagRetrievalService._embed_query(query)
                per_chapter: List[List[RagChunk]] = [
                    RagRetrievalService.search_sgk(db, query, subject_name, grade, k=SGK_K_PER_CHAPTER,
                                                   chapters=[ch], embedding=embedding)
                    for ch in chapters
                ]
                sgk_chunks = cls.round_robin(per_chapter)
                teacher_chunks: List[RagChunk] = []
                teacher_ids = cls.class_teacher_ids(db, student_id, subject_id)
                if teacher_ids:
                    teacher_chunks = RagRetrievalService.search_documents(
                        db, query, teacher_subject_scope=(subject_id, teacher_ids),
                        k=DOC_K_PER_QUERY * 2, embedding=embedding)
            return cls.pack_with_quotas(sgk_chunks, teacher_chunks)
        except Exception as e:  # noqa: BLE001
            logger.warning("Student RAG retrieval failed, generating without context: %s", e)
            return "", []

    @staticmethod
    def round_robin(lists: Sequence[Sequence[RagChunk]]) -> List[RagChunk]:
        """Interleave chunk lists (one per chapter) so every chapter is represented before any gets a second chunk."""
        out: List[RagChunk] = []
        for i in range(max((len(x) for x in lists), default=0)):
            out += [x[i] for x in lists if i < len(x)]
        return out

    @staticmethod
    def _norm(content: str) -> str:
        return re.sub(r"\s+", " ", (content or "").lower()).strip()

    @classmethod
    def is_duplicate(cls, content: str, kept: List[Tuple[str, set]]) -> bool:
        """True when content matches a kept chunk by normalised first 80 chars or token Jaccard >= 0.8."""
        norm = cls._norm(content)
        tokens = set(re.findall(r"\w+", norm))
        for k_norm, k_tokens in kept:
            if norm[:80] == k_norm[:80]:
                return True
            union = tokens | k_tokens
            if union and len(tokens & k_tokens) / len(union) >= JACCARD_DUP_THRESHOLD:
                return True
        return False

    @classmethod
    def pack_with_quotas(
        cls, sgk: Sequence[RagChunk], teacher: Sequence[RagChunk],
        sgk_quota: Optional[int] = None, teacher_quota: Optional[int] = None,
    ) -> Tuple[str, List[dict]]:
        """Pack SGK then teacher chunks (input order preserved) into per-source character quotas with dedup."""
        sgk_quota = SGK_QUOTA_CHARS if sgk_quota is None else sgk_quota
        teacher_quota = TEACHER_QUOTA_CHARS if teacher_quota is None else teacher_quota
        kept: List[Tuple[str, set]] = []
        selected: List[RagChunk] = []
        for chunks, quota in ((sgk, sgk_quota), (teacher, teacher_quota)):
            used = 0
            for c in chunks:
                if cls.is_duplicate(c.content, kept):
                    continue
                size = len(c.content.strip()) + len(c.ref) + 10
                if used + size > quota:
                    continue
                used += size
                norm = cls._norm(c.content)
                kept.append((norm, set(re.findall(r"\w+", norm))))
                selected.append(c)
        return cls.format_with_sources(selected, preserve_order=True)

    @staticmethod
    def _teacher_scope(db, role_name, subject_id, class_id, document_ids) -> Optional[dict]:
        """Search kwargs for teacher documents, or None when there is nothing to search."""
        if role_name == "Student":
            # Students get textbook theory only: teacher documents may be exams/matrices, and the
            # generated questions must not mirror them.
            return None
        return {"document_ids": list(document_ids)} if document_ids else None

    @staticmethod
    def format_context(chunks: Sequence[RagChunk]) -> str:
        """Dedupe, order SGK first, label each chunk with its source and cap the total size."""
        return RagContextService.format_with_sources(chunks)[0]

    @staticmethod
    def format_with_sources(chunks: Sequence[RagChunk], preserve_order: bool = False) -> Tuple[str, List[dict]]:
        """Like format_context, also returning deduped source dicts for chunks that made it into the context."""
        seen, parts, total = set(), [], 0
        sources: List[dict] = []
        seen_src = set()
        for c in (chunks if preserve_order else sorted(chunks, key=lambda c: (c.source != "sgk", -c.score))):
            key = (c.source, c.ref, c.page, c.content[:80])
            if key in seen:
                continue
            seen.add(key)
            tag = "SGK" if c.source == "sgk" else "GV"
            page = f" tr.{c.page}" if c.page else ""
            part = f"[{tag} {c.ref}{page}]\n{c.content.strip()}"
            if total + len(part) > (10**9 if preserve_order else MAX_CONTEXT_CHARS):
                break
            parts.append(part)
            total += len(part)
            label = f"{c.title or c.ref}, tr.{c.page}" if c.page else (c.title or c.ref)
            image_url = c.image_path if c.source == "sgk" else None
            skey = (c.source, label, c.modality, image_url, c.document_id)
            if skey not in seen_src:
                seen_src.add(skey)
                sources.append({
                    "source": c.source, "label": label, "page": c.page, "modality": c.modality,
                    "image_url": image_url, "document_id": c.document_id,
                })
        return "\n\n".join(parts), sources
