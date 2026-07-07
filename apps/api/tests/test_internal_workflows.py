"""Internal workflow orchestration API tests."""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from lexflow_api.auth.internal_hmac import sign_payload
from lexflow_api.main import create_app

TOKEN = "dev-n8n-webhook-secret"


@pytest.fixture
def app():
    return create_app()


@pytest.mark.asyncio
async def test_workflow_heartbeat_with_token(app) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/internal/workflows/heartbeat",
            headers={"X-Internal-Token": TOKEN},
        )
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["status"] == "ok"
    assert body["authorized"] is True


@pytest.mark.asyncio
async def test_workflow_heartbeat_rejects_bad_token(app) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/internal/workflows/heartbeat",
            headers={"X-Internal-Token": "wrong"},
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_workflow_heartbeat_with_signature(app) -> None:
    transport = ASGITransport(app=app)
    sig = sign_payload(b"")
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/internal/workflows/heartbeat",
            headers={"X-LexFlow-Signature": sig},
        )
    assert response.status_code == 200
