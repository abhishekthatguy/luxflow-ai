from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest

from lexflow_api.auth.jwt import create_access_token, decode_access_token, hash_token
from lexflow_api.auth.password import hash_password, verify_password
from lexflow_api.auth.rbac import (
    ROLE_MANAGING_PARTNER,
    ROLE_PARALEGAL,
    can_manage_participants,
    has_any_role,
)
from lexflow_api.config import settings


def test_hash_and_verify_password() -> None:
    hashed = hash_password("password123")
    assert hashed != "password123"
    assert verify_password("password123", hashed)
    assert not verify_password("wrong", hashed)


def test_create_and_decode_access_token() -> None:
    user_id = uuid4()
    firm_id = uuid4()
    token = create_access_token(
        user_id=user_id,
        firm_id=firm_id,
        roles=["Attorney"],
        email="jane@lexflow.local",
    )
    payload = decode_access_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["firm_id"] == str(firm_id)
    assert payload["type"] == "access"
    assert payload["roles"] == ["Attorney"]


def test_expired_token_raises() -> None:
    now = datetime.now(UTC)
    payload = {
        "sub": str(uuid4()),
        "type": "access",
        "iat": now - timedelta(hours=2),
        "exp": now - timedelta(hours=1),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    with pytest.raises(jwt.PyJWTError):
        decode_access_token(token)


def test_hash_token_is_deterministic() -> None:
    assert hash_token("abc") == hash_token("abc")
    assert hash_token("abc") != hash_token("def")


def test_has_any_role() -> None:
    assert has_any_role({"Attorney", "Paralegal"}, {"Attorney"})
    assert not has_any_role({"Paralegal"}, {"Attorney"})


def test_can_manage_participants_lead() -> None:
    assert can_manage_participants({ROLE_PARALEGAL}, "lead")


def test_can_manage_participants_admin() -> None:
    assert can_manage_participants({ROLE_MANAGING_PARTNER}, None)


def test_cannot_manage_participants_associate() -> None:
    assert not can_manage_participants({ROLE_PARALEGAL}, "associate")
    assert not can_manage_participants({"Associate"}, "associate")
