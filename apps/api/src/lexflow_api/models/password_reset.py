"""Password reset / portal invite tokens."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lexflow_api.db.base import Base

password_reset_purpose_enum = PG_ENUM(
    "invite",
    "reset",
    name="password_reset_purpose",
    schema="identity",
    create_type=False,
)


class PasswordResetPurpose(StrEnum):
    INVITE = "invite"
    RESET = "reset"


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    __table_args__ = {"schema": "identity"}

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("identity.users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    purpose: Mapped[str] = mapped_column(
        password_reset_purpose_enum,
        nullable=False,
        server_default="reset",
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    request_ip: Mapped[str | None] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    user: Mapped["User"] = relationship("User", back_populates="password_reset_tokens")
