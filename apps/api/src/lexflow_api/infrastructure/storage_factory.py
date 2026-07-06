from functools import lru_cache

from lexflow_api.config import settings
from lexflow_api.infrastructure.s3_storage import S3StorageClient


@lru_cache
def get_s3_client() -> S3StorageClient:
    return S3StorageClient(
        endpoint=settings.s3_endpoint,
        access_key=settings.s3_access_key,
        secret_key=settings.s3_secret_key,
        bucket=settings.s3_bucket,
        presign_endpoint=settings.s3_presign_endpoint,
    )
