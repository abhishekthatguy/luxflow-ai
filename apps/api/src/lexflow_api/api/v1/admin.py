from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from lexflow_api.auth.dependencies import CurrentUser
from lexflow_api.auth.permissions import PERM_MANAGE_USERS
from lexflow_api.auth.require_permission import require_permission
from lexflow_api.db.session import get_db
from lexflow_api.schemas.admin import AdminUserSummary
from lexflow_api.schemas.common import Envelope, envelope
from lexflow_api.services.admin_user_service import AdminUserService

router = APIRouter(prefix="/admin", tags=["admin"])

_admin_user = require_permission(PERM_MANAGE_USERS)


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "correlation_id", None)


@router.get("/users", response_model=Envelope[list[AdminUserSummary]])
async def list_firm_users(
    request: Request,
    user: CurrentUser = Depends(_admin_user),
    session: AsyncSession = Depends(get_db),
) -> Envelope[list[AdminUserSummary]]:
    items = await AdminUserService(session).list_users(user)
    return envelope(items, _request_id(request))
