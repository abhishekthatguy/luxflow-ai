from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from lexflow_api.auth.dependencies import CurrentUser
from lexflow_api.auth.jwt import create_access_token, generate_refresh_token, hash_token
from lexflow_api.auth.password import verify_password
from lexflow_api.config import settings
from lexflow_api.exceptions import UnauthorizedError, ValidationAppError
from lexflow_api.models.identity import RefreshToken, User
from lexflow_api.schemas.auth import TokenResponse, UserResponse


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def login(self, email: str, password: str) -> tuple[TokenResponse, User]:
        result = await self._session.execute(
            select(User).options(selectinload(User.roles)).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        if user is None or user.deleted_at is not None or user.status != "active":
            raise UnauthorizedError("Invalid email or password.")
        if not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid email or password.")

        roles = [role.name for role in user.roles]
        access_token = create_access_token(
            user_id=user.id,
            firm_id=user.firm_id,
            roles=roles,
            email=user.email,
        )
        refresh_raw = generate_refresh_token()
        refresh = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh_raw),
            expires_at=datetime.now(UTC) + timedelta(days=30),
        )
        user.last_login_at = datetime.now(UTC)
        self._session.add(refresh)
        await self._session.flush()

        tokens = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_raw,
            expires_in=settings.jwt_access_ttl_minutes * 60,
        )
        return tokens, user

    async def refresh(self, refresh_token: str) -> TokenResponse:
        token_hash = hash_token(refresh_token)
        result = await self._session.execute(
            select(RefreshToken)
            .options(selectinload(RefreshToken.user).selectinload(User.roles))
            .where(RefreshToken.token_hash == token_hash, RefreshToken.revoked_at.is_(None))
        )
        stored = result.scalar_one_or_none()
        if stored is None or stored.expires_at < datetime.now(UTC):
            raise UnauthorizedError("Invalid or expired refresh token.")

        user = stored.user
        if user.deleted_at is not None or user.status != "active":
            raise UnauthorizedError("User not active.")

        stored.revoked_at = datetime.now(UTC)
        new_raw = generate_refresh_token()
        new_refresh = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(new_raw),
            expires_at=datetime.now(UTC) + timedelta(days=30),
        )
        self._session.add(new_refresh)

        roles = [role.name for role in user.roles]
        access_token = create_access_token(
            user_id=user.id,
            firm_id=user.firm_id,
            roles=roles,
            email=user.email,
        )
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_raw,
            expires_in=settings.jwt_access_ttl_minutes * 60,
        )

    @staticmethod
    def to_user_response(user: User | CurrentUser) -> UserResponse:
        if isinstance(user, CurrentUser):
            return UserResponse(
                id=user.id,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                firm_id=user.firm_id,
                roles=sorted(user.roles),
            )
        return UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            title=user.title,
            firm_id=user.firm_id,
            roles=sorted(role.name for role in user.roles),
            last_login_at=user.last_login_at,
        )

    async def get_user_by_id(self, user_id: UUID) -> User:
        result = await self._session.execute(
            select(User).options(selectinload(User.roles)).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise ValidationAppError("User not found.")
        return user
