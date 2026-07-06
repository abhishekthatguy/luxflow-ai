from typing import BinaryIO

import boto3
from botocore.client import BaseClient


class S3StorageClient:
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
    ) -> None:
        self._bucket = bucket
        self._client: BaseClient = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="us-east-1",
        )

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
