from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from lexflow_api.api.internal.n8n import router as internal_n8n_router
from lexflow_api.api.internal.platform import router as internal_platform_router
from lexflow_api.api.v1.router import v1_router
from lexflow_api.config import settings
from lexflow_api.exceptions import AppError, ProblemDetail, problem_from_error
from lexflow_api.middleware import CorrelationIdMiddleware, configure_logging
from lexflow_api.telemetry import instrument_fastapi, setup_telemetry


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        problem = problem_from_error(request, exc)
        return JSONResponse(
            status_code=exc.status,
            content=problem.model_dump(by_alias=True, exclude_none=True),
            media_type="application/problem+json",
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = [
            {"field": ".".join(str(loc) for loc in err["loc"]), "message": err["msg"]}
            for err in exc.errors()
        ]
        detail = "One or more fields failed validation."
        if errors:
            first = errors[0]
            if "email" in first["field"] and "email" in first["message"].lower():
                detail = (
                    "Invalid email address. Dev seed accounts use @example.com "
                    "(e.g. jane@example.com), not @lexflow.local."
                )
            elif len(errors) == 1:
                detail = f"{first['field']}: {first['message']}"
        problem = ProblemDetail(
            type="https://lexflow.ai/errors/validation-failed",
            title="Validation Failed",
            status=422,
            detail=detail,
            instance=str(request.url.path),
            errors=errors,
            meta={
                "requestId": getattr(request.state, "correlation_id", None),
            },
        )
        return JSONResponse(
            status_code=422,
            content=problem.model_dump(by_alias=True, exclude_none=True),
            media_type="application/problem+json",
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        problem = ProblemDetail(
            type="https://lexflow.ai/errors/http-error",
            title="HTTP Error",
            status=exc.status_code,
            detail=str(exc.detail),
            instance=str(request.url.path),
            meta={
                "requestId": getattr(request.state, "correlation_id", None),
            },
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=problem.model_dump(by_alias=True, exclude_none=True),
            media_type="application/problem+json",
        )


def create_app() -> FastAPI:
    configure_logging(settings.log_level)
    setup_telemetry(settings.otel_service_name, settings.otel_exporter_otlp_endpoint)

    docs_enabled = settings.environment == "local"
    app = FastAPI(
        title="LexFlow AI API",
        version="0.1.0",
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
    )
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(CorrelationIdMiddleware)
    register_exception_handlers(app)
    app.include_router(internal_platform_router)
    app.include_router(internal_n8n_router)
    app.include_router(v1_router)
    instrument_fastapi(app)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "api"}

    if docs_enabled:

        @app.get("/api/v1/docs", include_in_schema=False)
        async def legacy_docs_redirect() -> RedirectResponse:
            return RedirectResponse(url="/docs", status_code=307)

    return app


app = create_app()
