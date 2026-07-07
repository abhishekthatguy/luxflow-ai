from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from lexflow_api.auth.dependencies import CurrentUser
from lexflow_api.auth.permissions import PERM_MANAGE_WORKFLOWS
from lexflow_api.auth.require_permission import require_permission
from lexflow_api.db.session import get_db
from lexflow_api.schemas.common import Envelope, envelope
from lexflow_api.schemas.workflows import (
    WorkflowCatalogExecutionItem,
    WorkflowCatalogItem,
    WorkflowExecutionDetailResponse,
    WorkflowTriggerRequest,
    WorkflowTriggerResult,
)
from lexflow_api.services.workflow_catalog_service import WorkflowCatalogService
from lexflow_api.services.workflow_service import WorkflowService

router = APIRouter(prefix="/workflows", tags=["workflow-catalog"])

_wf_admin = require_permission(PERM_MANAGE_WORKFLOWS)


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "correlation_id", None)


@router.post("/trigger", response_model=Envelope[WorkflowTriggerResult], status_code=202)
async def trigger_firm_workflow(
    request: Request,
    body: WorkflowTriggerRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    user: CurrentUser = Depends(_wf_admin),
    session: AsyncSession = Depends(get_db),
) -> Envelope[WorkflowTriggerResult]:
    """Manual/test trigger for firm-scoped workflows (scheduled jobs, smoke tests)."""
    result = await WorkflowService(session).trigger_firm_workflow(
        user, body, idempotency_key=idempotency_key
    )
    return envelope(result, _request_id(request))


@router.get("/catalog", response_model=Envelope[list[WorkflowCatalogItem]])
async def list_workflow_catalog(
    request: Request,
    user: CurrentUser = Depends(_wf_admin),
    session: AsyncSession = Depends(get_db),
) -> Envelope[list[WorkflowCatalogItem]]:
    items = await WorkflowCatalogService(session).list_catalog(user)
    return envelope(items, _request_id(request))


@router.get(
    "/catalog/{slug}/executions",
    response_model=Envelope[list[WorkflowCatalogExecutionItem]],
)
async def list_workflow_executions_by_slug(
    request: Request,
    slug: str,
    limit: int = Query(20, ge=1, le=100),
    user: CurrentUser = Depends(_wf_admin),
    session: AsyncSession = Depends(get_db),
) -> Envelope[list[WorkflowCatalogExecutionItem]]:
    items = await WorkflowCatalogService(session).list_executions(user, slug, limit=limit)
    return envelope(items, _request_id(request))


@router.get(
    "/executions/{execution_id}",
    response_model=Envelope[WorkflowExecutionDetailResponse],
)
async def get_workflow_execution_detail(
    request: Request,
    execution_id: UUID,
    user: CurrentUser = Depends(_wf_admin),
    session: AsyncSession = Depends(get_db),
) -> Envelope[WorkflowExecutionDetailResponse]:
    detail = await WorkflowCatalogService(session).get_execution(user, execution_id)
    return envelope(detail, _request_id(request))
