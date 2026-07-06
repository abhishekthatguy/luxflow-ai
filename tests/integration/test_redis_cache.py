import os
import uuid

import pytest

from lexflow_api.infrastructure.cache import get_cache_client


@pytest.fixture
def redis_url() -> str:
    return os.getenv("REDIS_URL", "redis://localhost:6379/0")


def test_redis_cache_roundtrip(redis_url: str) -> None:
    cache = get_cache_client(redis_url)
    key = f"platform:smoke:{uuid.uuid4()}"
    cache.set(key, "ok", ttl=60)
    assert cache.get(key) == "ok"
    cache.delete(key)
    assert cache.get(key) is None
