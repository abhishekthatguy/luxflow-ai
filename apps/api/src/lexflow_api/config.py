from pathlib import Path

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
    llm_allow_stub: bool = False
    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_deployment: str = "gpt-4o"
    azure_openai_api_version: str = "2024-02-15-preview"
    # Phase 1 — local OCR / LLM / embeddings
    ocr_provider: str = "local"
    ocr_enable_paddle: bool = True
    ollama_base_url: str = "http://ollama:11434"
    ollama_chat_model: str = "qwen2.5:latest"
    ollama_embedding_model: str = "nomic-embed-text"
    embedding_enabled: bool = True
    embedding_dimensions: int = 768
    # Phase 2 — Azure Document Intelligence
    azure_di_endpoint: str | None = None
    azure_di_api_key: str | None = None
    otel_exporter_otlp_endpoint: str | None = None
    otel_service_name: str = "lexflow-api"
    cors_origins: str = "http://localhost:3000"
    jwt_secret: str = "change-me-in-production-use-secrets-manager"
    jwt_access_ttl_minutes: int = 60
    admin_notification_emails: str = ""
    admin_notification_emails_file: str = "/config/admin-notification-emails.txt"
    # Gmail SMTP — client + admin emails (optional; logs only when unset)
    gmail_user: str | None = None
    gmail_app_password: str | None = None
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587

    # Notification Engine — sender & channel config (no hardcoded recipients in code)
    mail_from_name: str = "LexFlow AI Workflow Engine"
    mail_from_address: str = ""
    teams_webhook_url: str = ""
    notification_web_base_url: str = "http://localhost:3000"
    n8n_notification_email_slug: str = "notification-email-v1"
    n8n_notification_teams_slug: str = "notification-teams-v1"
    n8n_notification_slack_slug: str = "notification-slack-v1"
    notification_max_retries: int = 4
    notification_retry_base_seconds: int = 2
    # Local dev — route all workflow notification emails to one inbox (original To in subject)
    notification_redirect_email: str = ""

    password_reset_ttl_minutes: int = 60
    portal_invite_ttl_hours: int = 72
    portal_min_password_length: int = 12
    password_reset_ip_limit: int = 10
    password_reset_email_limit: int = 5
    password_reset_window_sec: int = 3600

    # Role email fallbacks — used only when no DB user matches role (seed overrides)
    managing_partner_email: str = ""
    attorney_email: str = ""
    associate_email: str = ""
    paralegal_email: str = ""
    system_administrator_email: str = ""

    # Slack team follow-up channel — credentials forwarded to n8n notification-slack-v1
    slack_webhook_url: str = ""
    slack_bot_token: str = ""
    slack_app_token: str = ""  # Socket Mode only; not used for channel posts
    slack_team_channel_id: str = "C0BF67RKS3Z"

    @property
    def slack_configured(self) -> bool:
        if self.slack_webhook_url.strip():
            return True
        return bool(self.slack_bot_token.strip() and self.slack_team_channel_id.strip())

    @property
    def mail_from(self) -> str:
        addr = self.mail_from_address.strip() or self.gmail_user or "notifications@lexflow.local"
        return f"{self.mail_from_name} <{addr}>"

    @property
    def role_email_fallbacks(self) -> dict[str, str]:
        mapping: dict[str, str] = {}
        if self.managing_partner_email.strip():
            mapping["ManagingPartner"] = self.managing_partner_email.strip()
        if self.attorney_email.strip():
            mapping["Attorney"] = self.attorney_email.strip()
        if self.associate_email.strip():
            mapping["Associate"] = self.associate_email.strip()
        if self.paralegal_email.strip():
            mapping["Paralegal"] = self.paralegal_email.strip()
        if self.system_administrator_email.strip():
            mapping["SystemAdministrator"] = self.system_administrator_email.strip()
        return mapping

    @property
    def admin_emails(self) -> list[str]:
        if self.admin_notification_emails.strip():
            return [e.strip() for e in self.admin_notification_emails.split(",") if e.strip()]
        path = Path(self.admin_notification_emails_file)
        if path.is_file():
            emails: list[str] = []
            for line in path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    emails.append(line)
            return emails
        return []

    def is_deliverable_notification_email(self, email: str) -> bool:
        """Reject seed/demo addresses that cannot receive real SMTP mail."""
        addr = email.strip().lower()
        if not addr or "@" not in addr:
            return False
        blocked_suffixes = ("@example.com", "@lexflow.local", "@test.lexflow.ai")
        if any(addr.endswith(suffix) for suffix in blocked_suffixes):
            return False
        return True

    def resolve_notification_email(self, intended_to: str) -> tuple[str, str, bool]:
        """Return (smtp_to, subject_prefix, redirected)."""
        intended = intended_to.strip()
        redirect = self.notification_redirect_email.strip()
        if redirect and redirect.lower() != intended.lower():
            return redirect, f"[For {intended}] ", True
        return intended, "", False

    @property
    def database_url_sync(self) -> str:
        return self.database_url.replace("+asyncpg", "")


settings = Settings()
