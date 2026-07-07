from uuid import UUID

from pydantic import EmailStr

from lexflow_api.schemas.common import CamelModel


class AdminUserSummary(CamelModel):
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    status: str
    roles: list[str]
