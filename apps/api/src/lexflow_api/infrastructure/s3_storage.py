from datetime import UTC, datetime
from typing import Any, BinaryIO

import boto3
from botocore.client import BaseClient
from botocore.config import Config


class S3StorageClient:
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        *,
        presign_endpoint: str | None = None,
    ) -> None:
        self._bucket = bucket
        self._presign_endpoint = presign_endpoint or endpoint
        client_kwargs: dict[str, Any] = {
            "endpoint_url": endpoint,
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "region_name": "us-east-1",
            "config": Config(signature_version="s3v4"),
        }
        self._client: BaseClient = boto3.client("s3", **client_kwargs)
        presign_kwargs = dict(client_kwargs)
        presign_kwargs["endpoint_url"] = self._presign_endpoint
        self._presign_client: BaseClient = boto3.client("s3", **presign_kwargs)

    @property
    def bucket(self) -> str:
        return self._bucket

    def put_object(
        self,
        key: str,
        body: bytes,
        content_type: str = "application/octet-stream",
    ) -> None:
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=body,
            ContentType=content_type,
        )

    def get_object(self, key: str) -> bytes:
        response = self._client.get_object(Bucket=self._bucket, Key=key)
        body = response["Body"].read()
        if isinstance(body, bytes):
            return body
        return bytes(body)

    def upload_fileobj(self, key: str, fileobj: BinaryIO) -> None:
        self._client.upload_fileobj(fileobj, self._bucket, key)

    def head_object(self, key: str) -> dict[str, Any]:
        return self._client.head_object(Bucket=self._bucket, Key=key)

    def generate_presigned_put(
        self,
        key: str,
        content_type: str,
        *,
        expires_in: int = 900,
    ) -> tuple[str, datetime]:
        url = self._presign_client.generate_presigned_url(
            "put_object",
            Params={"Bucket": self._bucket, "Key": key, "ContentType": content_type},
            ExpiresIn=expires_in,
        )
        expires_at = datetime.now(UTC).timestamp() + expires_in
        return url, datetime.fromtimestamp(expires_at, tz=UTC)

    def generate_presigned_get(self, key: str, *, expires_in: int = 300) -> tuple[str, datetime]:
        url = self._presign_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in,
        )
        expires_at = datetime.now(UTC).timestamp() + expires_in
        return url, datetime.fromtimestamp(expires_at, tz=UTC)
