# File Name: rag_context_service.py
# Description: Builds the labeled RAG context (SGK textbook + teacher documents) fed to the AI exercise generator.
# Created At: 2026-11-11
# Created By: AI Agent
# Updated At: 2026-11-11
# Updated By: AI Agent

import logging
from typing import List, Optional, Sequence, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from models.models import TeacherSubject
from app.modules.exercise.services.rag_retrieval_service import RagChunk, RagRetrievalService

logger = logging.getLogger("smartlms.exercise.rag_context")

SGK_K_PER_QUERY = 4
DOC_K_PER_QUERY = 3
MAX_CONTEXT_CHARS = 12000


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

    @staticmethod
    def _teacher_scope(db, role_name, subject_id, class_id, document_ids) -> Optional[dict]:
        """Search kwargs for teacher documents, or None when there is nothing to search."""
        if role_name == "Student":
            if not (subject_id and class_id):
                return None
            teacher_ids = [
                t for (t,) in db.query(TeacherSubject.teacher_id).filter(
                    TeacherSubject.class_id == class_id,
                    TeacherSubject.subject_id == subject_id,
                    TeacherSubject.status == "ACTIVE",
                ).all()
            ]
            return {"teacher_subject_scope": (subject_id, teacher_ids)} if teacher_ids else None
        return {"document_ids": list(document_ids)} if document_ids else None

    @staticmethod
    def format_context(chunks: Sequence[RagChunk]) -> str:
        """Dedupe, order SGK first, label each chunk with its source and cap the total size."""
        return RagContextService.format_with_sources(chunks)[0]

    @staticmethod
    def format_with_sources(chunks: Sequence[RagChunk]) -> Tuple[str, List[dict]]:
        """Like format_context, also returning deduped source dicts for chunks that made it into the context."""
        seen, parts, total = set(), [], 0
        sources: List[dict] = []
        seen_src = set()
        for c in sorted(chunks, key=lambda c: (c.source != "sgk", -c.score)):
            key = (c.source, c.ref, c.page, c.content[:80])
            if key in seen:
                continue
            seen.add(key)
            tag = "SGK" if c.source == "sgk" else "GV"
            page = f" tr.{c.page}" if c.page else ""
            part = f"[{tag} {c.ref}{page}]\n{c.content.strip()}"
            if total + len(part) > MAX_CONTEXT_CHARS:
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
