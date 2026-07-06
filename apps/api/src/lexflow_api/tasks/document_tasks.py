"""OCR and document processing Celery tasks."""

from __future__ import annotations

import io
import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select

from lexflow_api.celery_app import celery_app
from lexflow_api.config import settings
from lexflow_api.db.sync_session import SyncSessionLocal
from lexflow_api.infrastructure.s3_storage import S3StorageClient
from lexflow_api.models.cases import Case
from lexflow_api.models.documents import Document, DocumentStatus, OcrStatus
from lexflow_api.services.outbox import write_outbox_event_sync

logger = logging.getLogger(__name__)


def _s3() -> S3StorageClient:
    return S3StorageClient(
        endpoint=settings.s3_endpoint,
        access_key=settings.s3_access_key,
        secret_key=settings.s3_secret_key,
        bucket=settings.s3_bucket,
        presign_endpoint=settings.s3_presign_endpoint,
    )


def _extract_text(content: bytes, mime_type: str) -> str:
    if mime_type == "application/pdf":
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(content))
            parts = [page.extract_text() or "" for page in reader.pages]
            text = "\n".join(parts).strip()
            if text:
                return text
        except Exception:
            logger.exception("PDF text extraction failed")
    if mime_type.startswith("text/"):
        return content.decode("utf-8", errors="replace")
    return ""


@celery_app.task(name="lexflow_api.tasks.document_tasks.process_document_ocr")  # type: ignore[untyped-decorator]
def process_document_ocr(document_id: str) -> dict[str, str]:
    doc_uuid = UUID(document_id)
    session = SyncSessionLocal()
    try:
        document = session.execute(
            select(Document).where(Document.id == doc_uuid)
        ).scalar_one_or_none()
        if document is None:
            return {"status": "not_found"}

        document.status = DocumentStatus.PROCESSING
        document.ocr_status = OcrStatus.PROCESSING
        document.updated_at = datetime.now(UTC)
        session.commit()

        content = _s3().get_object(document.s3_key)
        text = _extract_text(content, document.mime_type)

        document = session.execute(
            select(Document).where(Document.id == doc_uuid)
        ).scalar_one()
        if text:
            document.ocr_text = text
            document.ocr_status = OcrStatus.COMPLETED
            document.status = DocumentStatus.READY
        else:
            document.ocr_status = OcrStatus.SKIPPED
            document.status = DocumentStatus.READY
        document.updated_at = datetime.now(UTC)

        write_outbox_event_sync(
            session,
            firm_id=document.firm_id,
            aggregate_type="document",
            aggregate_id=document.id,
            event_type="DocumentProcessed",
            payload={
                "caseId": str(document.case_id),
                "documentId": str(document.id),
                "ocrStatus": document.ocr_status,
            },
        )
        session.commit()

        from lexflow_api.tasks.workflow_tasks import trigger_document_upload_workflow

        trigger_document_upload_workflow.delay(str(document.id))

        return {"status": "ready", "documentId": document_id}
    except Exception as exc:
        session.rollback()
        logger.exception("OCR failed for %s", document_id)
        document = session.execute(
            select(Document).where(Document.id == doc_uuid)
        ).scalar_one_or_none()
        if document:
            document.status = DocumentStatus.FAILED
            document.ocr_status = OcrStatus.FAILED
            document.updated_at = datetime.now(UTC)
            session.commit()
        return {"status": "failed", "error": str(exc)}
    finally:
        session.close()
