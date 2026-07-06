from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from lexflow_api.schemas.common import CamelModel


class LoginRequest(CamelModel):
    email: EmailStr
    password: str = Field(min_length=8)


class RefreshRequest(CamelModel):
    refresh_token: str = Field(alias="refreshToken")


class TokenResponse(CamelModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(CamelModel):
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    title: str | None = None
    firm_id: UUID
    roles: list[str]
    last_login_at: datetime | None = None
