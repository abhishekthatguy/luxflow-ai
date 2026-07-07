"""Password reset and portal password validation tests."""

from unittest.mock import patch

import pytest

from lexflow_api.auth.password import validate_portal_password


def test_validate_portal_password_requires_length_and_mix() -> None:
    assert validate_portal_password("short1")
    assert validate_portal_password("longpasswordonly")
    assert validate_portal_password("123456789012")
    assert not validate_portal_password("ValidPass123")


@pytest.mark.asyncio
async def test_request_portal_reset_generic_when_unknown_email() -> None:
    from lexflow_api.services.password_reset_service import PasswordResetService

    class FakeSession:
        async def scalar(self, _stmt):
            return None

        async def execute(self, _stmt):
            class Result:
                def scalar_one_or_none(self):
                    return None

            return Result()

    service = PasswordResetService(FakeSession())  # type: ignore[arg-type]
    with patch.object(service, "_resolve_portal_user", return_value=None):
        result = await service.request_portal_reset("unknown@example.com", request_ip="127.0.0.1")
    assert "If an account exists" in result["message"]
