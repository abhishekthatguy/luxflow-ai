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


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/login", response_model=Envelope[TokenResponse])
async def login(
    request: Request,
    body: LoginRequest,
    session: AsyncSession = Depends(get_db),
) -> Envelope[TokenResponse]:
    from lexflow_api.auth.rate_limit import check_login_rate_limit

    check_login_rate_limit(_client_ip(request))
    service = AuthService(session)
    tokens, user = await service.login(body.email, body.password)
    logger = __import__("logging").getLogger("lexflow.api")
    logger.info(
        "auth_login_success",
        extra={"userId": str(user.id), "firmId": str(user.firm_id), "correlationId": _request_id(request)},
    )
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
