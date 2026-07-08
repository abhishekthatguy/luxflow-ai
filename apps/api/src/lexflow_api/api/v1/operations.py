from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from lexflow_api.auth.dependencies import CurrentUser, get_current_user
from lexflow_api.auth.permissions import PERM_OPERATIONS
from lexflow_api.auth.require_permission import require_permission
from lexflow_api.db.session import get_db
from lexflow_api.schemas.common import Envelope, envelope, pagination_meta
from lexflow_api.services.operations_service import (
    CaseProcessingPipeline,
    ComponentHealth,
    JobListItem,
    OperationsDashboard,
    OperationsOverview,
    OperationsService,
    QueueMetric,
    WorkflowRunItem,
)

router = APIRouter(prefix="/operations", tags=["operations"])

_ops_user = require_permission(PERM_OPERATIONS)


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "correlation_id", None)


@router.get("/dashboard", response_model=Envelope[OperationsDashboard])
async def operations_dashboard(
    request: Request,
    user: CurrentUser = Depends(_ops_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[OperationsDashboard]:
    data = await OperationsService(session).dashboard(user)
    return envelope(data, _request_id(request))


@router.get("/overview", response_model=Envelope[OperationsOverview])
async def operations_overview(
    request: Request,
    user: CurrentUser = Depends(_ops_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[OperationsOverview]:
    data = await OperationsService(session).overview(user)
    return envelope(data, _request_id(request))


@router.get("/health", response_model=Envelope[list[ComponentHealth]])
async def operations_health(
    request: Request,
    user: CurrentUser = Depends(_ops_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[list[ComponentHealth]]:
    data = await OperationsService(session).health_components()
    return envelope(data, _request_id(request))


@router.get("/queues", response_model=Envelope[list[QueueMetric]])
async def operations_queues(
    request: Request,
    user: CurrentUser = Depends(_ops_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[list[QueueMetric]]:
    data = await OperationsService(session).queue_metrics()
    return envelope(data, _request_id(request))


@router.get("/jobs", response_model=Envelope[list[JobListItem]])
async def operations_jobs(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100, alias="pageSize"),
    user: CurrentUser = Depends(_ops_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[list[JobListItem]]:
    items, total = await OperationsService(session).list_jobs(user, page=page, page_size=page_size)
    return envelope(items, _request_id(request), pagination_meta(page, page_size, total))


@router.get("/workflow-runs", response_model=Envelope[list[WorkflowRunItem]])
async def operations_workflow_runs(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100, alias="pageSize"),
    user: CurrentUser = Depends(_ops_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[list[WorkflowRunItem]]:
    items, total = await OperationsService(session).list_workflow_runs(
        user, page=page, page_size=page_size
    )
    return envelope(items, _request_id(request), pagination_meta(page, page_size, total))


@router.get("/cases/{case_id}/pipeline", response_model=Envelope[CaseProcessingPipeline])
async def case_processing_pipeline(
    request: Request,
    case_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[CaseProcessingPipeline]:
    """Case processing timeline — any user with matter access (not admin-only)."""
    data = await OperationsService(session).case_processing_pipeline(user, case_id)
    return envelope(data, _request_id(request))
