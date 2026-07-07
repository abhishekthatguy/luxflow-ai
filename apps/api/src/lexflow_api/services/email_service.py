"""Outbound email — HTML + plain text via configurable SMTP."""

from __future__ import annotations

import asyncio
import logging
import smtplib
from email.message import EmailMessage

from lexflow_api.config import settings

logger = logging.getLogger(__name__)


def smtp_configured() -> bool:
    return bool(settings.gmail_user and settings.gmail_app_password)


def send_email_sync(
    *,
    to: str,
    subject: str,
    body: str,
    html_body: str | None = None,
    reply_to: str | None = None,
) -> dict[str, object]:
    """Send email. Returns {status, channel, to, latency_ms}."""
    import time

    started = time.perf_counter()
    if not smtp_configured():
        logger.info(
            "EMAIL_STUB to=%s subject=%s html=%s",
            to,
            subject,
            bool(html_body),
        )
        return {
            "status": "stub",
            "channel": "log",
            "provider": "stub",
            "to": to,
            "latency_ms": int((time.perf_counter() - started) * 1000),
        }

    message = EmailMessage()
    message["From"] = settings.mail_from
    message["To"] = to
    message["Subject"] = subject
    if reply_to:
        message["Reply-To"] = reply_to
    message.set_content(body)
    if html_body:
        message.add_alternative(html_body, subtype="html")

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(settings.gmail_user, settings.gmail_app_password)
            server.send_message(message)
        latency = int((time.perf_counter() - started) * 1000)
        logger.info(
            "EMAIL_SENT to=%s subject=%s via=%s latency_ms=%s",
            to,
            subject,
            settings.smtp_host,
            latency,
        )
        return {
            "status": "sent",
            "channel": "smtp",
            "provider": "gmail_smtp",
            "to": to,
            "latency_ms": latency,
        }
    except Exception as exc:
        logger.exception("EMAIL_FAILED to=%s subject=%s", to, subject)
        return {
            "status": "failed",
            "channel": "smtp",
            "provider": "gmail_smtp",
            "to": to,
            "error": str(exc)[:500],
            "latency_ms": int((time.perf_counter() - started) * 1000),
        }


async def send_email(
    *,
    to: str,
    subject: str,
    body: str,
    html_body: str | None = None,
    reply_to: str | None = None,
) -> dict[str, object]:
    return await asyncio.to_thread(
        send_email_sync,
        to=to,
        subject=subject,
        body=body,
        html_body=html_body,
        reply_to=reply_to,
    )
