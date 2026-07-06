from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from lexflow_api.models.cases import ClientType
from lexflow_api.schemas.common import CamelModel


class ClientCreate(CamelModel):
    name: str = Field(min_length=1, max_length=255)
    type: ClientType = ClientType.INDIVIDUAL
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    metadata: dict[str, object] = Field(default_factory=dict)


class ClientUpdate(CamelModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    type: ClientType | None = None
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    metadata: dict[str, object] | None = None
    version: int | None = None


class ClientResponse(CamelModel):
    id: UUID
    firm_id: UUID
    name: str
    type: ClientType
    email: EmailStr | None = None
    phone: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)
    version: int
    created_at: datetime
    updated_at: datetime
