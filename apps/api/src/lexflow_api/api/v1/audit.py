from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from lexflow_api.auth.dependencies import CurrentUser, get_current_user
from lexflow_api.db.session import get_db
from lexflow_api.schemas.audit import AuditLogResponse
from lexflow_api.schemas.common import Envelope, envelope, pagination_meta
from lexflow_api.services.audit_query_service import AuditQueryService

router = APIRouter(prefix="/audit", tags=["audit"])


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "correlation_id", None)


@router.get("/logs", response_model=Envelope[list[AuditLogResponse]])
async def list_audit_logs(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100, alias="pageSize"),
    action: str | None = None,
    resource_type: str | None = Query(None, alias="resourceType"),
    case_id: UUID | None = Query(None, alias="caseId"),
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[list[AuditLogResponse]]:
    service = AuditQueryService(session)
    logs, total = await service.list_logs(
        user,
        page=page,
        page_size=page_size,
        action=action,
        resource_type=resource_type,
        case_id=case_id,
    )
    return envelope(logs, _request_id(request), pagination_meta(page, page_size, total))
