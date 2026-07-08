from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from lexflow_api.auth.dependencies import CurrentUser, get_current_user
from lexflow_api.db.session import get_db
from lexflow_api.schemas.auth import (
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetMessage,
    PasswordResetRequest,
    RefreshRequest,
    TokenResponse,
    UserResponse,
)
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
    tokens, user = await service.login(body.email, body.password, audience=body.audience)
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


@router.post("/password-reset/request", response_model=Envelope[PasswordResetMessage])
async def password_reset_request(
    request: Request,
    body: PasswordResetRequest,
    session: AsyncSession = Depends(get_db),
) -> Envelope[PasswordResetMessage]:
    from lexflow_api.auth.rate_limit import check_password_reset_rate_limit
    from lexflow_api.services.password_reset_service import PasswordResetService

    ip = _client_ip(request)
    check_password_reset_rate_limit(client_ip=ip, email=body.email)
    service = PasswordResetService(session)
    result = await service.request_portal_reset(body.email, request_ip=ip, allow_provision=True)
    await session.commit()
    return envelope(PasswordResetMessage(**result), _request_id(request))


@router.post("/password-reset/confirm", response_model=Envelope[PasswordResetMessage])
async def password_reset_confirm(
    request: Request,
    body: PasswordResetConfirm,
    session: AsyncSession = Depends(get_db),
) -> Envelope[PasswordResetMessage]:
    from lexflow_api.auth.rate_limit import check_auth_rate_limit
    from lexflow_api.config import settings
    from lexflow_api.services.password_reset_service import PasswordResetService

    ip = _client_ip(request)
    check_auth_rate_limit(
        scope="password-reset-confirm-ip",
        identifier=ip,
        limit=settings.password_reset_ip_limit,
        window_sec=settings.password_reset_window_sec,
    )
    service = PasswordResetService(session)
    result = await service.confirm_reset(body.token, body.password, request_ip=ip)
    await session.commit()
    return envelope(PasswordResetMessage(**result), _request_id(request))
