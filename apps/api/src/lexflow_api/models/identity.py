from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lexflow_api.db.base import Base

user_status_enum = PG_ENUM(
    "active", "inactive", "locked", name="user_status", schema="identity", create_type=False
)


class UserStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"


class Firm(Base):
    __tablename__ = "firms"
    __table_args__ = {"schema": "identity"}

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    settings: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    users: Mapped[list["User"]] = relationship(back_populates="firm")
    roles: Mapped[list["Role"]] = relationship(back_populates="firm")


class Role(Base):
    __tablename__ = "roles"
    __table_args__ = {"schema": "identity"}

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    firm_id: Mapped[UUID | None] = mapped_column(ForeignKey("identity.firms.id"))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    firm: Mapped["Firm | None"] = relationship(back_populates="roles")
    users: Mapped[list["User"]] = relationship(
        secondary="identity.user_roles", back_populates="roles"
    )


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "identity"}

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    firm_id: Mapped[UUID] = mapped_column(ForeignKey("identity.firms.id"), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(user_status_enum, nullable=False, server_default="active")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    firm: Mapped["Firm"] = relationship(back_populates="users")
    roles: Mapped[list["Role"]] = relationship(
        secondary="identity.user_roles", back_populates="users"
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user")
    password_reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(
        back_populates="user"
    )


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = {"schema": "identity"}

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("identity.users.id", ondelete="CASCADE"), primary_key=True
    )
    role_id: Mapped[UUID] = mapped_column(
        ForeignKey("identity.roles.id", ondelete="CASCADE"), primary_key=True
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = {"schema": "identity"}

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("identity.users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")
