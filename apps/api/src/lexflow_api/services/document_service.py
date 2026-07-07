from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lexflow_api.auth.dependencies import CurrentUser
from lexflow_api.exceptions import ConflictError, NotFoundError
from lexflow_api.infrastructure.s3_storage import S3StorageClient
from lexflow_api.models.documents import Document, DocumentStatus, DocumentVersion, OcrStatus
from lexflow_api.schemas.documents import (
    DocumentConfirm,
    DocumentDownloadResponse,
    DocumentInitiate,
    DocumentInitiateResponse,
    DocumentResponse,
)
from lexflow_api.services.audit import write_audit_log
from lexflow_api.services.case_service import CaseService
from lexflow_api.services.outbox import write_outbox_event
from lexflow_api.services.timeline import write_timeline_event


class DocumentService:
    def __init__(self, session: AsyncSession, s3: S3StorageClient) -> None:
        self._session = session
        self._s3 = s3
        self._cases = CaseService(session)

    @staticmethod
    def to_response(document: Document) -> DocumentResponse:
        return DocumentResponse(
            id=document.id,
            case_id=document.case_id,
            firm_id=document.firm_id,
            title=document.title,
            document_type=document.document_type,  # type: ignore[arg-type]
            status=document.status,
            mime_type=document.mime_type,
            file_size_bytes=document.file_size_bytes,
            checksum_sha256=document.checksum_sha256,
            ocr_status=document.ocr_status,
            ocr_text=document.ocr_text,
            version=document.version,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

    def _build_s3_key(
        self, firm_id: UUID, case_id: UUID, document_id: UUID, filename: str
    ) -> str:
        safe_name = filename.replace("/", "_").replace("\\", "_")
        return f"{firm_id}/{case_id}/{document_id}/v1/{safe_name}"

    async def initiate_upload(
        self, user: CurrentUser, case_id: UUID, data: DocumentInitiate
    ) -> DocumentInitiateResponse:
        case = await self._cases._get_accessible_case(user, case_id)
        document_id = uuid4()
        s3_key = self._build_s3_key(user.firm_id, case_id, document_id, data.filename)

        document = Document(
            id=document_id,
            case_id=case_id,
            firm_id=user.firm_id,
            title=data.title,
            document_type=data.document_type,
            status=DocumentStatus.PENDING_UPLOAD,
            s3_key=s3_key,
            mime_type=data.mime_type,
            file_size_bytes=data.file_size_bytes,
            checksum_sha256=data.checksum_sha256.lower(),
            uploaded_by=user.id,
        )
        self._session.add(document)
        await self._session.flush()

        upload_url, expires_at = self._s3.generate_presigned_put(
            s3_key, data.mime_type, expires_in=900
        )
        await write_audit_log(
            self._session,
            firm_id=user.firm_id,
            actor_id=user.id,
            action="document.upload.initiated",
            resource_type="document",
            resource_id=document.id,
            details={"caseId": str(case_id), "title": data.title},
        )
        return DocumentInitiateResponse(
            id=document.id,
            status=document.status,
            upload_url=upload_url,
            upload_expires_at=expires_at,
            s3_key=s3_key,
        )

    async def confirm_upload(
        self, user: CurrentUser, document_id: UUID, data: DocumentConfirm
    ) -> DocumentResponse:
        document = await self._get_accessible_document(user, document_id)
        if document.status != DocumentStatus.PENDING_UPLOAD:
            raise ConflictError("Document upload already confirmed.")

        expected = data.checksum_sha256.lower()
        if expected != document.checksum_sha256:
            raise ConflictError("Checksum does not match initiated upload.")

        try:
            head = self._s3.head_object(document.s3_key)
        except Exception as exc:
            raise ConflictError("File not found in storage. Complete the S3 upload first.") from exc

        size = int(head.get("ContentLength", 0))
        if size != document.file_size_bytes:
            raise ConflictError("Uploaded file size does not match declared size.")

        from lexflow_api.services.virus_scan import scan_object_stub

        scan = scan_object_stub(s3_key=document.s3_key, mime_type=document.mime_type)
        if not scan.clean:
            raise ConflictError(f"Virus scan failed: {scan.detail or 'infected file'}")

        version = DocumentVersion(
            document_id=document.id,
            version_number=1,
            s3_key=document.s3_key,
            file_size_bytes=document.file_size_bytes,
            checksum_sha256=document.checksum_sha256,
            created_by=user.id,
        )
        self._session.add(version)
        await self._session.flush()

        document.current_version_id = version.id
        document.status = DocumentStatus.UPLOADED
        document.updated_at = datetime.now(UTC)

        await write_outbox_event(
            self._session,
            firm_id=user.firm_id,
            aggregate_type="document",
            aggregate_id=document.id,
            event_type="DocumentUploaded",
            payload={
                "caseId": str(document.case_id),
                "documentId": str(document.id),
                "title": document.title,
                "mimeType": document.mime_type,
            },
        )
        await write_timeline_event(
            self._session,
            case_id=document.case_id,
            firm_id=user.firm_id,
            event_type="document.virus_scan.passed",
            title=f"Virus scan passed: {document.title}",
            payload={"documentId": str(document.id)},
            actor_id=user.id,
        )
        await write_timeline_event(
            self._session,
            case_id=document.case_id,
            firm_id=user.firm_id,
            event_type="document.uploaded",
            title=f"{document.title} uploaded",
            payload={"documentId": str(document.id)},
            actor_id=user.id,
        )
        await write_audit_log(
            self._session,
            firm_id=user.firm_id,
            actor_id=user.id,
            action="document.upload.confirmed",
            resource_type="document",
            resource_id=document.id,
            details={"caseId": str(document.case_id), "title": document.title},
        )
        from lexflow_api.domain.notification_events import NotificationEventType
        from lexflow_api.services.notifications.helpers import emit_case_notification

        await emit_case_notification(
            self._session,
            event_type=NotificationEventType.DOCUMENT_UPLOADED,
            firm_id=user.firm_id,
            case_id=document.case_id,
            title="Document uploaded",
            description=f"{document.title} is ready for processing.",
            status_badge="Processing",
            actor_id=user.id,
            recipient_user_ids={user.id},
            context={
                "document_title": document.title,
                "current_stage": "Uploaded",
                "recent_activity": [f"{document.title} uploaded"],
            },
        )

        from lexflow_api.tasks.document_tasks import process_document_ocr

        process_document_ocr.delay(str(document.id))

        return self.to_response(document)

    async def list_documents(
        self, user: CurrentUser, case_id: UUID, *, page: int = 1, page_size: int = 25
    ) -> tuple[list[DocumentResponse], int]:
        await self._cases._get_accessible_case(user, case_id)
        query = select(Document).where(
            Document.case_id == case_id,
            Document.firm_id == user.firm_id,
            Document.deleted_at.is_(None),
        )
        count_result = await self._session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = int(count_result.scalar_one())
        offset = (page - 1) * page_size
        result = await self._session.execute(
            query.order_by(Document.created_at.desc()).offset(offset).limit(page_size)
        )
        docs = [self.to_response(d) for d in result.scalars().all()]
        return docs, total

    async def get_document(self, user: CurrentUser, document_id: UUID) -> DocumentResponse:
        document = await self._get_accessible_document(user, document_id)
        return self.to_response(document)

    async def get_download_url(
        self, user: CurrentUser, document_id: UUID
    ) -> DocumentDownloadResponse:
        document = await self._get_accessible_document(user, document_id)
        if document.status == DocumentStatus.PENDING_UPLOAD:
            raise ConflictError("Document upload not yet confirmed.")
        url, expires_at = self._s3.generate_presigned_get(document.s3_key, expires_in=300)
        await write_audit_log(
            self._session,
            firm_id=user.firm_id,
            actor_id=user.id,
            action="document.download.url_issued",
            resource_type="document",
            resource_id=document.id,
        )
        return DocumentDownloadResponse(download_url=url, expires_at=expires_at)

    async def get_document_content(
        self, user: CurrentUser, document_id: UUID
    ) -> tuple[bytes, str, str]:
        """Return raw bytes, mime type, and filename for inline preview."""
        document = await self._get_accessible_document(user, document_id)
        if document.status == DocumentStatus.PENDING_UPLOAD:
            raise ConflictError("Document upload not yet confirmed.")
        content = self._s3.get_object(document.s3_key)
        filename = document.s3_key.rsplit("/", 1)[-1]
        await write_audit_log(
            self._session,
            firm_id=user.firm_id,
            actor_id=user.id,
            action="document.preview",
            resource_type="document",
            resource_id=document.id,
        )
        return content, document.mime_type, filename

    async def retry_ocr(self, user: CurrentUser, document_id: UUID) -> DocumentResponse:
        document = await self._get_accessible_document(user, document_id)
        if document.status == DocumentStatus.PENDING_UPLOAD:
            raise ConflictError("Confirm the upload before retrying OCR.")
        if document.ocr_status in (OcrStatus.COMPLETED, OcrStatus.SKIPPED) and document.status == DocumentStatus.READY:
            raise ConflictError("OCR already completed for this document.")

        document.status = DocumentStatus.UPLOADED
        document.ocr_status = OcrStatus.PENDING
        document.ocr_text = None
        document.updated_at = datetime.now(UTC)
        await self._session.commit()

        from lexflow_api.tasks.document_tasks import process_document_ocr

        process_document_ocr.delay(str(document.id))
        return self.to_response(document)

    async def _get_accessible_document(self, user: CurrentUser, document_id: UUID) -> Document:
        result = await self._session.execute(
            select(Document).where(
                Document.id == document_id,
                Document.firm_id == user.firm_id,
                Document.deleted_at.is_(None),
            )
        )
        document = result.scalar_one_or_none()
        if document is None:
            raise NotFoundError("Document not found.")
        await self._cases._get_accessible_case(user, document.case_id)
        return document
