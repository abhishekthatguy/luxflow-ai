from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "local"
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://lexflow:lexflow@postgres:5432/lexflow"
    redis_url: str = "redis://redis:6379/0"
    rabbitmq_url: str = "amqp://guest:guest@rabbitmq:5672/"
    celery_broker_url: str = "amqp://guest:guest@rabbitmq:5672/"
    celery_result_backend: str = "redis://redis:6379/1"
    s3_endpoint: str = "http://minio:9000"
    s3_access_key: str = "lexflow"
    s3_secret_key: str = "lexflowsecret"
    s3_bucket: str = "lexflow-local-documents"
    s3_presign_endpoint: str = "http://localhost:9000"
    n8n_internal_url: str = "http://n8n:5678"
    n8n_webhook_secret: str = "dev-n8n-webhook-secret"
    llm_provider: str = "stub"
    otel_exporter_otlp_endpoint: str | None = None
    otel_service_name: str = "lexflow-api"
    cors_origins: str = "http://localhost:3000"
    jwt_secret: str = "change-me-in-production-use-secrets-manager"
    jwt_access_ttl_minutes: int = 60

    @property
    def database_url_sync(self) -> str:
        return self.database_url.replace("+asyncpg", "")


settings = Settings()
