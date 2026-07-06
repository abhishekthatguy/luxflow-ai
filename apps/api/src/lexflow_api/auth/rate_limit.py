"""Redis-backed rate limiting for auth endpoints."""

from __future__ import annotations

from lexflow_api.config import settings
from lexflow_api.exceptions import RateLimitError
from lexflow_api.infrastructure.cache import get_cache_client

_LOGIN_LIMIT = 10
_LOGIN_WINDOW_SEC = 60


def _client():
    return get_cache_client(settings.redis_url)


def check_auth_rate_limit(*, scope: str, identifier: str, limit: int, window_sec: int) -> None:
    key = f"ratelimit:{scope}:{identifier}"
    cache = _client()
    current = cache.get(key)
    count = int(current) if current else 0
    if count >= limit:
        raise RateLimitError(f"Rate limit exceeded for {scope}. Max {limit} requests per {window_sec}s.")
    cache.set(key, str(count + 1), ttl=window_sec)


def check_login_rate_limit(client_ip: str) -> None:
    check_auth_rate_limit(
        scope="login",
        identifier=client_ip,
        limit=_LOGIN_LIMIT,
        window_sec=_LOGIN_WINDOW_SEC,
    )
