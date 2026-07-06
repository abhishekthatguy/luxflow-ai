import os
import uuid

import httpx


def test_correlation_id_in_api_logs_via_header() -> None:
    api_url = os.getenv("API_INTERNAL_URL", "http://localhost:8000")
    correlation_id = str(uuid.uuid4())
    response = httpx.get(
        f"{api_url}/health",
        headers={"X-Correlation-ID": correlation_id},
        timeout=10.0,
    )
    assert response.status_code == 200
    assert response.headers.get("X-Correlation-ID") == correlation_id
