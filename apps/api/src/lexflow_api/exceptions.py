from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import Request
from pydantic import BaseModel


class ProblemDetail(BaseModel):
    type: str
    title: str
    status: int
    detail: str
    instance: str | None = None
    errors: list[dict[str, str]] | None = None
    meta: dict[str, Any] | None = None


class AppError(Exception):
    def __init__(
        self,
        *,
        status: int,
        title: str,
        detail: str,
        type_suffix: str = "application-error",
        errors: list[dict[str, str]] | None = None,
    ) -> None:
        self.status = status
        self.title = title
        self.detail = detail
        self.type_suffix = type_suffix
        self.errors = errors
        super().__init__(detail)


class NotFoundError(AppError):
    def __init__(self, detail: str = "Resource not found.") -> None:
        super().__init__(status=404, title="Not Found", detail=detail, type_suffix="not-found")


class UnauthorizedError(AppError):
    def __init__(self, detail: str = "Authentication required.") -> None:
        super().__init__(
            status=401, title="Unauthorized", detail=detail, type_suffix="unauthorized"
        )


class ForbiddenError(AppError):
    def __init__(self, detail: str = "Insufficient permissions.") -> None:
        super().__init__(status=403, title="Forbidden", detail=detail, type_suffix="forbidden")


class ConflictError(AppError):
    def __init__(self, detail: str = "Resource conflict.") -> None:
        super().__init__(status=409, title="Conflict", detail=detail, type_suffix="conflict")


class ValidationAppError(AppError):
    def __init__(
        self,
        detail: str = "Validation failed.",
        errors: list[dict[str, str]] | None = None,
    ) -> None:
        super().__init__(
            status=422,
            title="Validation Failed",
            detail=detail,
            type_suffix="validation-failed",
            errors=errors,
        )


class RateLimitError(AppError):
    def __init__(self, detail: str = "Too many requests. Try again later.") -> None:
        super().__init__(
            status=429,
            title="Too Many Requests",
            detail=detail,
            type_suffix="rate-limit",
        )


def _request_meta(request: Request) -> dict[str, Any]:
    correlation_id = getattr(request.state, "correlation_id", None) or str(uuid4())
    return {
        "requestId": correlation_id,
        "timestamp": datetime.now(UTC).isoformat(),
    }


def problem_from_error(request: Request, exc: AppError) -> ProblemDetail:
    return ProblemDetail(
        type=f"https://lexflow.ai/errors/{exc.type_suffix}",
        title=exc.title,
        status=exc.status,
        detail=exc.detail,
        instance=str(request.url.path),
        errors=exc.errors,
        meta=_request_meta(request),
    )
