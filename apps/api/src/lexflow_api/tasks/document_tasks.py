"""OCR and document processing Celery tasks."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select

from lexflow_api.celery_app import celery_app
from lexflow_api.config import settings
from lexflow_api.db.sync_session import SyncSessionLocal
from lexflow_api.infrastructure.s3_storage import S3StorageClient
from lexflow_api.models.documents import Document, DocumentStatus, OcrStatus
from lexflow_api.services.document_authority_notifications import (
    notify_document_authorities_sync,
)
from lexflow_api.services.document_indexing import index_document_chunks
from lexflow_api.services.ocr import extract_text
from lexflow_api.services.outbox import write_outbox_event_sync
from lexflow_api.services.timeline import write_timeline_event_sync

logger = logging.getLogger(__name__)


def _s3() -> S3StorageClient:
    return S3StorageClient(
        endpoint=settings.s3_endpoint,
        access_key=settings.s3_access_key,
        secret_key=settings.s3_secret_key,
        bucket=settings.s3_bucket,
        presign_endpoint=settings.s3_presign_endpoint,
    )


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
        ocr_result = extract_text(content, document.mime_type)

        document = session.execute(
            select(Document).where(Document.id == doc_uuid)
        ).scalar_one()
        chunk_count = 0
        if ocr_result.text:
            document.ocr_text = ocr_result.text
            document.ocr_status = OcrStatus.COMPLETED
            document.status = DocumentStatus.READY
            write_timeline_event_sync(
                session,
                case_id=document.case_id,
                firm_id=document.firm_id,
                event_type="document.ocr.completed",
                title=f"OCR complete: {document.title}",
                payload={
                    "documentId": str(document.id),
                    "method": ocr_result.method,
                },
            )
            chunk_count = 0
            try:
                chunk_count = index_document_chunks(
                    session, document=document, ocr_method=ocr_result.method
                )
            except Exception:
                logger.warning(
                    "Chunk indexing failed for %s — OCR text still saved",
                    document_id,
                    exc_info=True,
                )
            write_timeline_event_sync(
                session,
                case_id=document.case_id,
                firm_id=document.firm_id,
                event_type="document.chunking.completed",
                title=f"Chunking complete: {document.title}",
                payload={
                    "documentId": str(document.id),
                    "chunks": chunk_count,
                    "method": ocr_result.method,
                },
            )
            notify_document_authorities_sync(session, document=document)
        else:
            document.ocr_status = OcrStatus.SKIPPED
            document.status = DocumentStatus.READY
            notify_document_authorities_sync(session, document=document)
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
                "ocrMethod": ocr_result.method,
                "chunkCount": chunk_count,
            },
        )
        session.commit()

        from lexflow_api.services.notifications.helpers import queue_notification_event

        queue_notification_event(
            {
                "event_type": "ocr.completed",
                "firm_id": str(document.firm_id),
                "case_id": str(document.case_id),
                "title": "OCR completed",
                "description": f"Text extraction finished for {document.title}.",
                "status_badge": "OCR Complete",
                "context": {
                    "document_title": document.title,
                    "current_stage": "OCR",
                    "recent_activity": [
                        f"{document.title} uploaded",
                        "OCR completed",
                    ],
                },
            }
        )

        from lexflow_api.tasks.workflow_tasks import trigger_document_upload_workflow

        trigger_document_upload_workflow.delay(str(document.id))

        return {"status": "ready", "documentId": document_id, "ocrMethod": ocr_result.method}
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
