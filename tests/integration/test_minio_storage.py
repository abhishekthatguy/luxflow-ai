import os
import uuid

import pytest

from lexflow_api.infrastructure.s3_storage import S3StorageClient


@pytest.fixture
def storage() -> S3StorageClient:
    return S3StorageClient(
        endpoint=os.getenv("S3_ENDPOINT", "http://localhost:9000"),
        access_key=os.getenv("S3_ACCESS_KEY", "lexflow"),
        secret_key=os.getenv("S3_SECRET_KEY", "lexflowsecret"),
        bucket=os.getenv("S3_BUCKET", "lexflow-local-documents"),
    )


def test_minio_put_get(storage: S3StorageClient) -> None:
    key = f"platform/smoke-{uuid.uuid4()}.txt"
    payload = b"lexflow-platform-smoke"
    storage.put_object(key, payload, content_type="text/plain")
    assert storage.get_object(key) == payload
