from typing import cast

import bcrypt


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str | None) -> bool:
    if not hashed_password:
        return False
    return cast(
        bool,
        bcrypt.checkpw(plain_password.encode(), hashed_password.encode()),
    )


def validate_portal_password(password: str) -> list[dict[str, str]]:
    """Return validation errors for client portal passwords."""
    from lexflow_api.config import settings

    errors: list[dict[str, str]] = []
    min_len = settings.portal_min_password_length
    if len(password) < min_len:
        errors.append(
            {
                "field": "password",
                "message": f"Password must be at least {min_len} characters.",
            }
        )
    if not any(c.isalpha() for c in password):
        errors.append({"field": "password", "message": "Password must include a letter."})
    if not any(c.isdigit() for c in password):
        errors.append({"field": "password", "message": "Password must include a number."})
    return errors
