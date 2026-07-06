from dataclasses import dataclass, field
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from lexflow_api.auth.jwt import decode_access_token
from lexflow_api.db.session import get_db
from lexflow_api.exceptions import UnauthorizedError
from lexflow_api.models.identity import User

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    id: UUID
    firm_id: UUID
    email: str
    first_name: str
    last_name: str
    roles: set[str] = field(default_factory=set)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db),
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Missing or invalid authorization header.")

    try:
        payload = decode_access_token(credentials.credentials)
    except Exception as exc:
        raise UnauthorizedError("Invalid or expired access token.") from exc

    if payload.get("type") != "access":
        raise UnauthorizedError("Invalid token type.")

    user_id = UUID(str(payload["sub"]))
    result = await session.execute(
        select(User)
        .options(selectinload(User.roles))
        .where(User.id == user_id, User.deleted_at.is_(None), User.status == "active")
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise UnauthorizedError("User not found or inactive.")

    roles = {role.name for role in user.roles}
    current = CurrentUser(
        id=user.id,
        firm_id=user.firm_id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        roles=roles,
    )
    request.state.current_user = current
    return current
