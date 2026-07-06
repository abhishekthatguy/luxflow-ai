from fastapi.testclient import TestClient

from lexflow_api.main import app


def test_health_returns_ok() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "api"}


def test_health_includes_correlation_id() -> None:
    client = TestClient(app)
    response = client.get("/health", headers={"X-Correlation-ID": "test-correlation-id"})
    assert response.headers.get("X-Correlation-ID") == "test-correlation-id"
