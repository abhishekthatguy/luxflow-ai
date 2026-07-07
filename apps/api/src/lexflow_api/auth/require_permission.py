"""FastAPI dependencies for enterprise permission checks."""

from collections.abc import Callable

from fastapi import Depends

from lexflow_api.auth.dependencies import CurrentUser, get_current_user
from lexflow_api.auth.permissions import require_permission_message
from lexflow_api.exceptions import ForbiddenError


def require_permission(permission: str) -> Callable[..., CurrentUser]:
    from lexflow_api.auth.permissions import has_permission

    async def _dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not has_permission(user.roles, permission):
            raise ForbiddenError(require_permission_message(permission))
        return user

    return _dependency
