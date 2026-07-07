"""Gather OCR text from all case documents for AI context."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from lexflow_api.models.cases import Case
from lexflow_api.models.documents import Document


def gather_case_document_context(session: Session, *, case_id: UUID) -> str:
    case = session.execute(select(Case).where(Case.id == case_id)).scalar_one()
    parts: list[str] = [f"Case title: {case.title}"]
    if case.description:
        parts.append(case.description)

    docs = session.execute(
        select(Document)
        .where(
            Document.case_id == case_id,
            Document.deleted_at.is_(None),
        )
        .order_by(Document.created_at.asc())
    ).scalars().all()

    for doc in docs:
        if doc.ocr_text:
            parts.append(f"\n--- {doc.title} ---\n{doc.ocr_text}")

    return "\n".join(parts)
