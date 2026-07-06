import os
import uuid

import pytest

from lexflow_api.infrastructure.rabbitmq_smoke import consume_smoke_message, publish_smoke_message


@pytest.fixture
def rabbitmq_url() -> str:
    return os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")


def test_rabbitmq_publish_consume(rabbitmq_url: str) -> None:
    queue = f"platform.smoke.{uuid.uuid4().hex[:8]}"
    publish_smoke_message(rabbitmq_url, queue=queue)
    assert consume_smoke_message(rabbitmq_url, queue=queue) is True
