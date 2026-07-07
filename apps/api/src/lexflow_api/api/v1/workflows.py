from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from lexflow_api.auth.dependencies import CurrentUser, get_current_user
from lexflow_api.db.session import get_db
from lexflow_api.schemas.common import Envelope, envelope, pagination_meta
from lexflow_api.schemas.workflows import (
    WorkflowCatalogItem,
    WorkflowExecutionResponse,
    WorkflowStepResponse,
    WorkflowTriggerRequest,
    WorkflowTriggerResult,
)
from lexflow_api.services.workflow_catalog_service import WorkflowCatalogService
from lexflow_api.services.workflow_service import WorkflowService

router = APIRouter(prefix="/cases/{case_id}/workflows", tags=["workflows"])


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "correlation_id", None)


@router.get("/catalog", response_model=Envelope[list[WorkflowCatalogItem]])
async def list_case_workflow_catalog(
    request: Request,
    case_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[list[WorkflowCatalogItem]]:
    """All workflows for this case with RBAC — who can trigger and what is automated."""
    items = await WorkflowCatalogService(session).list_for_case(user, case_id)
    return envelope(items, _request_id(request))


@router.post("/trigger", response_model=Envelope[WorkflowTriggerResult], status_code=202)
async def trigger_workflow(
    request: Request,
    case_id: UUID,
    body: WorkflowTriggerRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[WorkflowTriggerResult]:
    result = await WorkflowService(session).trigger_workflow(
        user, case_id, body, idempotency_key=idempotency_key
    )
    return envelope(result, _request_id(request))


@router.delete("/executions/{execution_id}", status_code=204)
async def delete_workflow_execution(
    case_id: UUID,
    execution_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    await WorkflowService(session).delete_execution(user, case_id, execution_id)
    await session.commit()


@router.get("", response_model=Envelope[list[WorkflowExecutionResponse]])
async def list_workflow_executions(
    request: Request,
    case_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100, alias="pageSize"),
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[list[WorkflowExecutionResponse]]:
    executions, total = await WorkflowService(session).list_executions(
        user, case_id, page=page, page_size=page_size
    )
    return envelope(executions, _request_id(request), pagination_meta(page, page_size, total))


@router.get("/executions/{execution_id}/steps", response_model=Envelope[list[WorkflowStepResponse]])
async def list_workflow_steps(
    request: Request,
    case_id: UUID,
    execution_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[list[WorkflowStepResponse]]:
    steps = await WorkflowService(session).list_steps(user, execution_id)
    return envelope(steps, _request_id(request))
