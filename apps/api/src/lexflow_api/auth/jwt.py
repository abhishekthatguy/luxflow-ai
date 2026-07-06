import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt

from lexflow_api.config import settings

ALGORITHM = "HS256"


def create_access_token(
    *,
    user_id: UUID,
    firm_id: UUID,
    roles: list[str],
    email: str,
) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "firm_id": str(firm_id),
        "email": email,
        "roles": roles,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_access_ttl_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
