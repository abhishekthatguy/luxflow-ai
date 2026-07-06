from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from lexflow_api.api.internal.platform import router as internal_platform_router
from lexflow_api.config import settings
from lexflow_api.middleware import CorrelationIdMiddleware, configure_logging
from lexflow_api.telemetry import instrument_fastapi, setup_telemetry


def create_app() -> FastAPI:
    configure_logging(settings.log_level)
    setup_telemetry(settings.otel_service_name, settings.otel_exporter_otlp_endpoint)

    app = FastAPI(
        title="LexFlow AI API",
        version="0.1.0",
        docs_url="/api/v1/docs" if settings.environment == "local" else None,
        redoc_url=None,
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
    app.include_router(internal_platform_router)
    instrument_fastapi(app)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "api"}

    return app


app = create_app()
