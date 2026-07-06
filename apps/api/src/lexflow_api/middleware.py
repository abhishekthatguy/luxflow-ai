import json
import logging
import re
import sys
import time
import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("lexflow.api")

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b")


def redact_pii(text: str) -> str:
    text = _EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    return _PHONE_RE.sub("[REDACTED_PHONE]", text)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S.%fZ"),
            "level": record.levelname,
            "message": redact_pii(record.getMessage()),
            "service": "api",
        }
        for key in (
            "correlationId",
            "method",
            "path",
            "statusCode",
            "durationMs",
            "userId",
            "firmId",
            "caseId",
        ):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload)


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = int((time.perf_counter() - start) * 1000)
        response.headers["X-Correlation-ID"] = correlation_id
        logger.info(
            "request_completed",
            extra={
                "correlationId": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "statusCode": response.status_code,
                "durationMs": duration_ms,
            },
        )
        return response
