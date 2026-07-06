import json
import logging

import pika

logger = logging.getLogger("lexflow.api.rabbitmq")


def publish_smoke_message(url: str, queue: str = "platform.smoke") -> None:
    connection = pika.BlockingConnection(pika.URLParameters(url))
    channel = connection.channel()
    channel.queue_declare(queue=queue, durable=False)
    channel.basic_publish(exchange="", routing_key=queue, body=json.dumps({"smoke": True}))
    connection.close()
    logger.info("rabbitmq_smoke_published", extra={"queue": queue})


def consume_smoke_message(url: str, queue: str = "platform.smoke", timeout: int = 5) -> bool:
    connection = pika.BlockingConnection(pika.URLParameters(url))
    channel = connection.channel()
    channel.queue_declare(queue=queue, durable=False)
    method, _, body = channel.basic_get(queue=queue, auto_ack=True)
    connection.close()
    if method is None:
        return False
    payload = json.loads(body.decode())
    return payload.get("smoke") is True
