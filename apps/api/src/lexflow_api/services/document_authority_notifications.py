"""Route document OCR events to authorities (timeline) and notify clients by email."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from lexflow_api.models.cases import Case, Client
from lexflow_api.models.documents import Document
from lexflow_api.config import settings
from lexflow_api.services.email_service import send_email_sync
from lexflow_api.services.timeline import write_timeline_event_sync

logger = logging.getLogger(__name__)

# (authority label, timeline event type, notification subject template)
_AUTHORITY_RULES: list[tuple[tuple[str, ...], str, str, str]] = [
    (("police",), "Local Police Traffic Division", "authority.police.notified", "Police report received"),
    (("insurance", "claim"), "Insurance Claims Adjuster", "authority.insurance.notified", "Insurance claim form received"),
    (("medical", "hospital"), "Medical Records Department", "authority.medical.notified", "Medical report received"),
    (("license", "driver"), "DMV / Licensing Authority", "authority.dmv.notified", "Driver license copy received"),
    (("vehicle", "photo"), "Accident Reconstruction Unit", "authority.photos.notified", "Vehicle damage photos received"),
]


def _match_rule(title: str) -> tuple[str, str, str] | None:
    lowered = title.lower()
    for keywords, authority, event_type, subject in _AUTHORITY_RULES:
        if any(kw in lowered for kw in keywords):
            return authority, event_type, subject
    return None


def _client_for_case(session: Session, case_id: UUID) -> Client | None:
    case = session.execute(select(Case).where(Case.id == case_id)).scalar_one_or_none()
    if case is None or case.client_id is None:
        return None
    return session.execute(select(Client).where(Client.id == case.client_id)).scalar_one_or_none()


def notify_document_authorities_sync(session: Session, *, document: Document) -> None:
    """Timeline authority routing + optional Gmail notification to the client."""
    matched = _match_rule(document.title)
    if matched is None:
        return

    authority, event_type, subject = matched
    client = _client_for_case(session, document.case_id)

    write_timeline_event_sync(
        session,
        case_id=document.case_id,
        firm_id=document.firm_id,
        event_type=event_type,
        title=f"{subject}: {document.title}",
        payload={
            "documentId": str(document.id),
            "authority": authority,
            "documentTitle": document.title,
        },
    )

    logger.info(
        "AUTHORITY_NOTIFICATION authority=%s document=%s case=%s",
        authority,
        document.title,
        document.case_id,
    )

    if client and client.email:
        email_subject = f"LexFlow — {subject}"
        email_body = (
            f"Hello {client.name},\n\n"
            f"Your document \"{document.title}\" was received and routed to {authority}.\n\n"
            f"We will update you as your motor vehicle insurance claim progresses.\n\n"
            f"— LexFlow Legal\n"
        )
        result = send_email_sync(
            to=client.email,
            subject=email_subject,
            body=email_body,
            reply_to=settings.gmail_user,
        )
        logger.info(
            "CLIENT_EMAIL_NOTIFICATION to=%s subject=%s status=%s authority=%s",
            client.email,
            email_subject,
            result.get("status"),
            authority,
        )
