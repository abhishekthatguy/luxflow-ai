import time

import httpx

from lexflow_api.celery_app import celery_app


def test_n8n_internal_callback_to_api() -> None:
    import os

    api_url = os.getenv("API_INTERNAL_URL", "http://localhost:8000")
    response = httpx.post(
        f"{api_url}/internal/platform/smoke",
        json={"source": "integration-test", "correlationId": "n8n-smoke-test"},
        timeout=10.0,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["received"] is True


def test_celery_ping_async() -> None:
    import os

    api_url = os.getenv("API_INTERNAL_URL", "http://localhost:8000")
    dispatch = httpx.post(
        f"{api_url}/internal/platform/celery-ping",
        json={"correlationId": "celery-smoke-test"},
        timeout=10.0,
    )
    assert dispatch.status_code == 200
    task_id = dispatch.json()["taskId"]

    result = celery_app.AsyncResult(task_id)
    for _ in range(30):
        if result.ready():
            assert result.get(timeout=1) == "pong"
            return
        time.sleep(1)
    raise AssertionError(f"Celery task {task_id} did not complete with pong")
