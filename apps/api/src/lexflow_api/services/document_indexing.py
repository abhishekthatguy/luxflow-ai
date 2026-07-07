"""Index OCR text into pgvector chunks after document processing."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.orm import Session

from lexflow_api.models.document_chunks import DocumentChunk
from lexflow_api.models.documents import Document
from lexflow_api.services.document_chunking import chunk_text
from lexflow_api.services.embeddings.ollama import embed_texts

logger = logging.getLogger(__name__)


def index_document_chunks(
    session: Session,
    *,
    document: Document,
    ocr_method: str | None = None,
) -> int:
    """Replace existing chunks for a document and optionally embed via Ollama."""
    if not document.ocr_text:
        session.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
        session.flush()
        return 0

    chunks = chunk_text(document.ocr_text)
    session.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
    session.flush()

    vectors = embed_texts(chunks)
    for index, (content, vector) in enumerate(zip(chunks, vectors, strict=True)):
        session.add(
            DocumentChunk(
                document_id=document.id,
                case_id=document.case_id,
                firm_id=document.firm_id,
                chunk_index=index,
                content=content,
                embedding=vector,
                ocr_method=ocr_method,
            )
        )
    session.flush()
    logger.info(
        "Indexed %s chunks for document %s (embeddings=%s)",
        len(chunks),
        document.id,
        sum(1 for v in vectors if v is not None),
    )
    return len(chunks)
