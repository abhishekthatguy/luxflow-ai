from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from lexflow_api.auth.dependencies import CurrentUser, get_current_user
from lexflow_api.db.session import get_db
from lexflow_api.infrastructure.storage_factory import get_s3_client
from lexflow_api.schemas.common import Envelope, envelope, pagination_meta
from lexflow_api.schemas.documents import (
    DocumentConfirm,
    DocumentDownloadResponse,
    DocumentInitiate,
    DocumentInitiateResponse,
    DocumentResponse,
)
from lexflow_api.services.document_service import DocumentService

case_documents_router = APIRouter(prefix="/cases/{case_id}/documents", tags=["documents"])
documents_router = APIRouter(prefix="/documents", tags=["documents"])


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "correlation_id", None)


def _service(session: AsyncSession) -> DocumentService:
    return DocumentService(session, get_s3_client())


@case_documents_router.post("", response_model=Envelope[DocumentInitiateResponse], status_code=201)
async def initiate_document_upload(
    request: Request,
    case_id: UUID,
    body: DocumentInitiate,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[DocumentInitiateResponse]:
    result = await _service(session).initiate_upload(user, case_id, body)
    return envelope(result, _request_id(request))


@case_documents_router.get("", response_model=Envelope[list[DocumentResponse]])
async def list_case_documents(
    request: Request,
    case_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100, alias="pageSize"),
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[list[DocumentResponse]]:
    docs, total = await _service(session).list_documents(
        user, case_id, page=page, page_size=page_size
    )
    return envelope(docs, _request_id(request), pagination_meta(page, page_size, total))


@documents_router.get("/{document_id}", response_model=Envelope[DocumentResponse])
async def get_document(
    request: Request,
    document_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[DocumentResponse]:
    doc = await _service(session).get_document(user, document_id)
    return envelope(doc, _request_id(request))


@documents_router.post("/{document_id}/confirm", response_model=Envelope[DocumentResponse])
async def confirm_document_upload(
    request: Request,
    document_id: UUID,
    body: DocumentConfirm,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[DocumentResponse]:
    doc = await _service(session).confirm_upload(user, document_id, body)
    return envelope(doc, _request_id(request))


@documents_router.post("/{document_id}/retry-ocr", response_model=Envelope[DocumentResponse])
async def retry_document_ocr(
    request: Request,
    document_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[DocumentResponse]:
    doc = await _service(session).retry_ocr(user, document_id)
    return envelope(doc, _request_id(request))


@documents_router.get("/{document_id}/download", response_model=Envelope[DocumentDownloadResponse])
async def download_document(
    request: Request,
    document_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[DocumentDownloadResponse]:
    result = await _service(session).get_download_url(user, document_id)
    return envelope(result, _request_id(request))


@documents_router.get("/{document_id}/content")
async def preview_document_content(
    document_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Response:
    """Stream document bytes through the API for authenticated inline preview."""
    content, mime_type, filename = await _service(session).get_document_content(user, document_id)
    safe_name = filename.replace('"', "")
    return Response(
        content=content,
        media_type=mime_type,
        headers={
            "Content-Disposition": f'inline; filename="{safe_name}"',
            "Cache-Control": "private, max-age=120",
        },
    )
