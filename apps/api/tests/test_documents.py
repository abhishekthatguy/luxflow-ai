from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from lexflow_api.auth.dependencies import CurrentUser
from lexflow_api.exceptions import NotFoundError
from lexflow_api.infrastructure.s3_storage import S3StorageClient
from lexflow_api.models.documents import DocumentStatus
from lexflow_api.schemas.documents import DocumentConfirm, DocumentInitiate
from lexflow_api.services.document_service import DocumentService


def _user() -> CurrentUser:
    return CurrentUser(
        id=uuid4(),
        firm_id=uuid4(),
        email="jane@example.com",
        first_name="Jane",
        last_name="Attorney",
        roles={"Attorney"},
    )


@pytest.mark.asyncio
async def test_initiate_upload_creates_pending_document() -> None:
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()

    case_id = uuid4()
    mock_case = MagicMock()
    mock_case.id = case_id

    s3 = MagicMock(spec=S3StorageClient)
    s3.generate_presigned_put.return_value = ("https://minio/upload", MagicMock())

    service = DocumentService(session, s3)
    with patch.object(service._cases, "_get_accessible_case", AsyncMock(return_value=mock_case)):
        with patch(
            "lexflow_api.services.document_service.write_audit_log", AsyncMock()
        ):
            result = await service.initiate_upload(
                _user(),
                case_id,
                DocumentInitiate(
                    title="Test Doc",
                    filename="test.txt",
                    mime_type="text/plain",
                    file_size_bytes=100,
                    checksum_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                ),
            )

    assert result.status == DocumentStatus.PENDING_UPLOAD
    s3.generate_presigned_put.assert_called_once()


@pytest.mark.asyncio
async def test_get_document_matter_wall_not_found() -> None:
    session = AsyncMock()
    s3 = MagicMock(spec=S3StorageClient)
    service = DocumentService(session, s3)

    scalar = MagicMock()
    scalar.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=scalar)

    with pytest.raises(NotFoundError):
        await service.get_document(_user(), uuid4())
