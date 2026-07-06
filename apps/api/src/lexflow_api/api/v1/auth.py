from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from lexflow_api.auth.dependencies import CurrentUser, get_current_user
from lexflow_api.db.session import get_db
from lexflow_api.schemas.auth import LoginRequest, RefreshRequest, TokenResponse, UserResponse
from lexflow_api.schemas.common import Envelope, envelope
from lexflow_api.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "correlation_id", None)


@router.post("/login", response_model=Envelope[TokenResponse])
async def login(
    request: Request,
    body: LoginRequest,
    session: AsyncSession = Depends(get_db),
) -> Envelope[TokenResponse]:
    service = AuthService(session)
    tokens, _user = await service.login(body.email, body.password)
    return envelope(tokens, _request_id(request))


@router.post("/refresh", response_model=Envelope[TokenResponse])
async def refresh(
    request: Request,
    body: RefreshRequest,
    session: AsyncSession = Depends(get_db),
) -> Envelope[TokenResponse]:
    service = AuthService(session)
    tokens = await service.refresh(body.refresh_token)
    return envelope(tokens, _request_id(request))


@router.get("/me", response_model=Envelope[UserResponse])
async def me(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
) -> Envelope[UserResponse]:
    return envelope(AuthService.to_user_response(user), _request_id(request))
