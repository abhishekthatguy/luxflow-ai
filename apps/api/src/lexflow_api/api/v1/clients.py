from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from lexflow_api.auth.dependencies import CurrentUser, get_current_user
from lexflow_api.auth.permissions import PERM_MANAGE_CLIENTS
from lexflow_api.auth.require_permission import require_permission
from lexflow_api.db.session import get_db
from lexflow_api.schemas.cases import CaseResponse
from lexflow_api.schemas.clients import ClientCreate, ClientResponse, ClientUpdate
from lexflow_api.schemas.common import Envelope, envelope, pagination_meta
from lexflow_api.services.case_service import CaseService
from lexflow_api.services.client_service import ClientService

router = APIRouter(prefix="/clients", tags=["clients"])


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "correlation_id", None)


@router.get("", response_model=Envelope[list[ClientResponse]])
async def list_clients(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100, alias="pageSize"),
    search: str | None = None,
    user: CurrentUser = Depends(require_permission(PERM_MANAGE_CLIENTS)),
    session: AsyncSession = Depends(get_db),
) -> Envelope[list[ClientResponse]]:
    service = ClientService(session)
    clients, total = await service.list_clients(user, page=page, page_size=page_size, search=search)
    return envelope(
        clients,
        _request_id(request),
        pagination_meta(page, page_size, total),
    )


@router.post("", response_model=Envelope[ClientResponse], status_code=201)
async def create_client(
    request: Request,
    body: ClientCreate,
    user: CurrentUser = Depends(require_permission(PERM_MANAGE_CLIENTS)),
    session: AsyncSession = Depends(get_db),
) -> Envelope[ClientResponse]:
    service = ClientService(session)
    client = await service.create_client(user, body)
    return envelope(client, _request_id(request))


@router.get("/{client_id}", response_model=Envelope[ClientResponse])
async def get_client(
    request: Request,
    client_id: UUID,
    user: CurrentUser = Depends(require_permission(PERM_MANAGE_CLIENTS)),
    session: AsyncSession = Depends(get_db),
) -> Envelope[ClientResponse]:
    service = ClientService(session)
    client = await service.get_client(user, client_id)
    return envelope(client, _request_id(request))


@router.patch("/{client_id}", response_model=Envelope[ClientResponse])
async def update_client(
    request: Request,
    client_id: UUID,
    body: ClientUpdate,
    user: CurrentUser = Depends(require_permission(PERM_MANAGE_CLIENTS)),
    session: AsyncSession = Depends(get_db),
) -> Envelope[ClientResponse]:
    service = ClientService(session)
    client = await service.update_client(user, client_id, body)
    return envelope(client, _request_id(request))


@router.get("/{client_id}/cases", response_model=Envelope[list[CaseResponse]])
async def list_client_cases(
    request: Request,
    client_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100, alias="pageSize"),
    user: CurrentUser = Depends(require_permission(PERM_MANAGE_CLIENTS)),
    session: AsyncSession = Depends(get_db),
) -> Envelope[list[CaseResponse]]:
    client_service = ClientService(session)
    case_service = CaseService(session)
    cases, total = await client_service.list_client_cases(
        user, client_id, page=page, page_size=page_size
    )
    responses = [case_service.to_case_response(c) for c in cases]
    return envelope(
        responses,
        _request_id(request),
        pagination_meta(page, page_size, total),
    )
