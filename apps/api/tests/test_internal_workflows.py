"""Internal workflow orchestration API tests."""

import json
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from lexflow_api.main import create_app
from lexflow_api.services.workflow_session_service import SESSION_KEY

TOKEN = "dev-n8n-webhook-secret"


class InMemoryCache:
    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self._store.get(key)

    def set(self, key: str, value: str, ttl: int = 60) -> None:
        del ttl
        self._store[key] = value

    def delete(self, key: str) -> None:
        self._store.pop(key, None)


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def memory_cache():
    cache = InMemoryCache()
    with patch(
        "lexflow_api.services.workflow_session_service.get_cache_client",
        return_value=cache,
    ):
        yield cache


@pytest.mark.asyncio
async def test_session_initialize(app, memory_cache) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/internal/workflows/session/initialize",
            headers={"X-Internal-Token": TOKEN},
        )
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["sessionValid"] is True
    assert body["authorized"] is True
    assert body["sessionToken"]
    assert SESSION_KEY in memory_cache._store


@pytest.mark.asyncio
async def test_session_heartbeat_with_token(app, memory_cache) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        init = await client.post(
            "/internal/workflows/session/initialize",
            headers={"X-Internal-Token": TOKEN},
        )
        token = init.json()["data"]["sessionToken"]
        response = await client.get(
            "/internal/workflows/session/heartbeat",
            headers={"X-Internal-Token": TOKEN, "X-Session-Token": token},
        )
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["sessionValid"] is True
    assert body["authorized"] is True


@pytest.mark.asyncio
async def test_session_heartbeat_rejects_bad_token(app) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/internal/workflows/session/heartbeat",
            headers={"X-Internal-Token": "wrong"},
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_session_verify_requires_active_session(app, memory_cache) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        init = await client.post(
            "/internal/workflows/session/initialize",
            headers={"X-Internal-Token": TOKEN},
        )
        token = init.json()["data"]["sessionToken"]
        response = await client.get(
            "/internal/workflows/session/verify",
            headers={"X-Internal-Token": TOKEN, "X-Session-Token": token},
        )
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["sessionValid"] is True
    assert body["authorized"] is True


@pytest.mark.asyncio
async def test_session_verify_rejects_without_session(app, memory_cache) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/internal/workflows/session/verify",
            headers={"X-Internal-Token": TOKEN},
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_session_heartbeat_requires_initialize_when_missing(app, memory_cache) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/internal/workflows/session/heartbeat",
            headers={"X-Internal-Token": TOKEN},
        )
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["sessionValid"] is False
    assert body["requiresInitialize"] is True

