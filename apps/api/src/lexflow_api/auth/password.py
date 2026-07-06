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
