from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "local"
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://lexflow:lexflow@postgres:5432/lexflow"
    redis_url: str = "redis://redis:6379/0"
    cors_origins: str = "http://localhost:3000"


settings = Settings()
