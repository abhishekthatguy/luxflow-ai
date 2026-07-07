"""Secure password setup and reset for client portal users."""

from __future__ import annotations

import logging
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from urllib.parse import quote

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from lexflow_api.auth.jwt import hash_token
from lexflow_api.auth.password import hash_password, validate_portal_password
from lexflow_api.auth.rbac import ROLE_CLIENT
from lexflow_api.config import settings
from lexflow_api.domain.notification_events import NotificationEventType
from lexflow_api.exceptions import UnauthorizedError, ValidationAppError
from lexflow_api.models.cases import Client
from lexflow_api.models.identity import RefreshToken, User
from lexflow_api.models.password_reset import PasswordResetPurpose, PasswordResetToken
from lexflow_api.services.audit import write_audit_log
from lexflow_api.services.notifications.email_template_service import render_email, render_plain_summary
from lexflow_api.services.portal_user_service import PortalUserService

logger = logging.getLogger(__name__)

GENERIC_RESET_MESSAGE = (
    "If an account exists for this email, we sent a secure link to set or reset your password."
)


class PasswordResetService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._portal_users = PortalUserService(session)

    def _reset_url(self, raw_token: str) -> str:
        base = settings.notification_web_base_url.rstrip("/")
        return f"{base}/portal/reset-password?token={quote(raw_token, safe='')}"

    async def _invalidate_all_active_tokens(self, user_id: UUID) -> None:
        """After a successful reset, revoke any remaining unused links."""
        await self._session.execute(
            update(PasswordResetToken)
            .where(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.used_at.is_(None),
            )
            .values(used_at=datetime.now(UTC))
        )

    async def _create_token(
        self,
        user: User,
        *,
        purpose: PasswordResetPurpose,
        request_ip: str | None,
    ) -> str:
        raw = secrets.token_urlsafe(32)
        ttl = (
            timedelta(hours=settings.portal_invite_ttl_hours)
            if purpose == PasswordResetPurpose.INVITE
            else timedelta(minutes=settings.password_reset_ttl_minutes)
        )
        token = PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(raw),
            purpose=purpose.value,
            expires_at=datetime.now(UTC) + ttl,
            request_ip=request_ip,
        )
        self._session.add(token)
        await self._session.flush()
        return raw

    async def _queue_reset_email(
        self,
        *,
        user: User,
        raw_token: str,
        purpose: PasswordResetPurpose,
        firm_id: UUID,
    ) -> None:
        reset_url = self._reset_url(raw_token)
        event_type = (
            NotificationEventType.PORTAL_PASSWORD_SETUP
            if purpose == PasswordResetPurpose.INVITE
            else NotificationEventType.PASSWORD_RESET
        )
        ctx = {
            "headline": "Set your LexFlow portal password"
            if purpose == PasswordResetPurpose.INVITE
            else "Reset your LexFlow portal password",
            "client_name": f"{user.first_name} {user.last_name}".strip(),
            "client_email": user.email,
            "reset_url": reset_url,
            "expires_minutes": settings.password_reset_ttl_minutes,
            "expires_hours": settings.portal_invite_ttl_hours,
            "status_badge": "Secure link",
        }
        subject, html_body = render_email(event_type, ctx)
        plain_body = render_plain_summary({**ctx, "description": reset_url})

        from lexflow_api.tasks.notification_tasks import deliver_email_notification

        deliver_email_notification.delay(
            {
                "to": user.email,
                "subject": subject,
                "html_body": html_body,
                "plain_body": plain_body,
                "firm_id": str(firm_id),
                "correlation_id": str(user.id),
                "event_type": event_type.value,
                "workflow_slug": None,
                "workflow_execution_id": None,
                "user_id": str(user.id),
                "case_id": None,
            }
        )

    async def _resolve_portal_user(self, email: str, *, allow_provision: bool) -> User | None:
        normalized = email.strip().lower()
        user = await self._portal_users.get_portal_user_by_email(normalized)
        if user is not None:
            return user if self._portal_users.is_portal_user(user) else None

        if not allow_provision:
            return None

        client = await self._session.scalar(
            select(Client).where(
                func.lower(Client.email) == normalized,
                Client.deleted_at.is_(None),
            )
        )
        if client is None:
            return None
        return await self._portal_users.provision_for_client(client)

    async def request_portal_reset(
        self,
        email: str,
        *,
        request_ip: str | None,
        allow_provision: bool = True,
    ) -> dict[str, str]:
        user = await self._resolve_portal_user(email, allow_provision=allow_provision)
        if user is None:
            logger.info("password_reset_noop email=%s ip=%s", email.strip().lower(), request_ip)
            return {"message": GENERIC_RESET_MESSAGE}

        purpose = (
            PasswordResetPurpose.INVITE
            if not user.password_hash
            else PasswordResetPurpose.RESET
        )
        raw = await self._create_token(user, purpose=purpose, request_ip=request_ip)
        await self._queue_reset_email(
            user=user,
            raw_token=raw,
            purpose=purpose,
            firm_id=user.firm_id,
        )
        await write_audit_log(
            self._session,
            firm_id=user.firm_id,
            actor_id=None,
            action="auth.password_reset.requested",
            resource_type="user",
            resource_id=user.id,
            details={"purpose": purpose.value, "requestIp": request_ip},
        )
        logger.info(
            "password_reset_queued user_id=%s purpose=%s ip=%s",
            user.id,
            purpose.value,
            request_ip,
        )
        return {"message": GENERIC_RESET_MESSAGE}

    async def send_portal_invite_for_client(
        self,
        client: Client,
        *,
        request_ip: str | None = None,
        send_email: bool = True,
    ) -> dict[str, object]:
        user = await self._portal_users.provision_for_client(client)
        if user is None:
            return {"skipped": True, "reason": "Could not provision portal user."}

        purpose = (
            PasswordResetPurpose.INVITE
            if not user.password_hash
            else PasswordResetPurpose.RESET
        )
        raw = await self._create_token(user, purpose=purpose, request_ip=request_ip)
        reset_url = self._reset_url(raw)
        if send_email:
            await self._queue_reset_email(
                user=user,
                raw_token=raw,
                purpose=purpose,
                firm_id=client.firm_id,
            )
        await write_audit_log(
            self._session,
            firm_id=client.firm_id,
            actor_id=None,
            action="auth.portal_invite.sent",
            resource_type="client",
            resource_id=client.id,
            details={"userId": str(user.id), "purpose": purpose.value, "emailSent": send_email},
        )
        return {
            "skipped": False,
            "userId": str(user.id),
            "setupUrl": reset_url,
            "emailQueued": 1 if send_email else 0,
            "purpose": purpose.value,
        }

    async def confirm_reset(
        self,
        raw_token: str,
        new_password: str,
        *,
        request_ip: str | None,
    ) -> dict[str, str]:
        errors = validate_portal_password(new_password)
        if errors:
            raise ValidationAppError("Password does not meet security requirements.", errors=errors)

        token_hash = hash_token(raw_token.strip())
        now = datetime.now(UTC)
        result = await self._session.execute(
            select(PasswordResetToken)
            .options(selectinload(PasswordResetToken.user).selectinload(User.roles))
            .where(PasswordResetToken.token_hash == token_hash)
        )
        stored = result.scalar_one_or_none()
        if stored is None:
            raise UnauthorizedError("This link is invalid or has expired. Request a new one.")
        if stored.used_at is not None:
            raise UnauthorizedError(
                "This link was already used. Sign in or request a new password reset link."
            )
        expires_at = stored.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at < now:
            raise UnauthorizedError("This link has expired. Request a new one from the portal.")

        user = stored.user
        if user.deleted_at is not None or user.status != "active":
            raise UnauthorizedError("This link is invalid or has expired. Request a new one.")
        if ROLE_CLIENT not in {role.name for role in user.roles}:
            raise UnauthorizedError("This link is invalid or has expired. Request a new one.")

        stored.used_at = datetime.now(UTC)
        user.password_hash = hash_password(new_password)
        user.updated_at = datetime.now(UTC)

        await self._invalidate_all_active_tokens(user.id)

        await self._session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
        )
        await write_audit_log(
            self._session,
            firm_id=user.firm_id,
            actor_id=user.id,
            action="auth.password_reset.completed",
            resource_type="user",
            resource_id=user.id,
            details={"purpose": stored.purpose, "requestIp": request_ip},
        )
        logger.info("password_reset_completed user_id=%s ip=%s", user.id, request_ip)
        return {"message": "Password updated. You can sign in to the client portal."}
