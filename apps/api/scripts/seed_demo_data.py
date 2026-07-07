"""Seed realistic demo data — clients, cases, documents, AI, workflows, audit (idempotent)."""

from __future__ import annotations

import asyncio
import hashlib
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sqlalchemy import func, select

from lexflow_api.db.session import async_session_factory
from lexflow_api.models.ai import AISummary, SummaryStatus, SummaryType
from lexflow_api.models.audit import AuditLog
from lexflow_api.models.cases import Case, CaseParticipant, CaseTimelineEvent, Client, ClientType, ParticipantRole
from lexflow_api.models.documents import Document, DocumentStatus, DocumentVersion, OcrStatus
from lexflow_api.models.identity import Firm, User
from lexflow_api.models.notifications import Notification, NotificationChannel, NotificationStatus
from lexflow_api.models.shared import AsyncJob, JobStatus, JobType
from lexflow_api.models.workflows import ExecutionStatus, WorkflowDefinition, WorkflowExecution

CLIENTS = [
    ("John Doe", ClientType.INDIVIDUAL, "john.doe@gmail.com", "+1-404-555-0101"),
    ("Sarah Johnson", ClientType.INDIVIDUAL, "sarah.j@example.com", "+1-404-555-0102"),
    ("Emily Davis", ClientType.INDIVIDUAL, "emily.davis@example.com", "+1-404-555-0103"),
    ("Michael Chen", ClientType.INDIVIDUAL, "michael.chen@example.com", "+1-404-555-0104"),
    ("Lisa Martinez", ClientType.INDIVIDUAL, "lisa.martinez@example.com", "+1-404-555-0105"),
    ("Robert Williams", ClientType.INDIVIDUAL, "r.williams@example.com", "+1-404-555-0106"),
    ("Acme Insurance", ClientType.ORGANIZATION, "claims@acme-insurance.example", "+1-800-555-0100"),
    ("Blue Cross Health", ClientType.ORGANIZATION, "legal@bluecross.example", "+1-800-555-0200"),
    ("Metro Construction", ClientType.ORGANIZATION, "legal@metroconstruction.example", "+1-404-555-0300"),
    ("Global Logistics", ClientType.ORGANIZATION, "compliance@globallogistics.example", "+1-404-555-0400"),
    ("Summit Retail Group", ClientType.ORGANIZATION, "legal@summitretail.example", "+1-404-555-0500"),
    ("Pacific Medical Center", ClientType.ORGANIZATION, "risk@pacificmed.example", "+1-404-555-0600"),
]

CASES = [
    ("Motor Vehicle Claim", "John Doe", "litigation", "active", "high"),
    ("Wrongful Termination", "Sarah Johnson", "employment", "active", "normal"),
    ("Construction Defect", "Metro Construction", "litigation", "active", "high"),
    ("Cyber Incident Response", "Global Logistics", "regulatory", "active", "urgent"),
    ("Medical Negligence", "Emily Davis", "litigation", "intake", "normal"),
    ("Property Damage Claim", "Acme Insurance", "other", "active", "normal"),
    ("Slip and Fall — Retail", "Summit Retail Group", "litigation", "intake", "normal"),
    ("HIPAA Breach Review", "Pacific Medical Center", "regulatory", "active", "high"),
    ("Contract Dispute", "Blue Cross Health", "corporate", "on_hold", "normal"),
    ("Workers Comp Appeal", "Michael Chen", "employment", "active", "normal"),
    ("Estate Planning Review", "Lisa Martinez", "family", "closed", "low"),
    ("Product Liability", "Summit Retail Group", "litigation", "intake", "high"),
    ("Insurance Coverage Dispute", "Acme Insurance", "litigation", "active", "normal"),
    ("Employment Harassment", "Sarah Johnson", "employment", "active", "high"),
    ("Data Privacy Audit", "Global Logistics", "regulatory", "active", "normal"),
    ("Medical Malpractice — Surgery", "Emily Davis", "litigation", "active", "urgent"),
    ("Commercial Lease Dispute", "Metro Construction", "real_estate", "intake", "normal"),
    ("Whistleblower Retaliation", "Michael Chen", "employment", "active", "high"),
    ("Premises Liability", "Robert Williams", "litigation", "intake", "normal"),
    ("Vendor Contract Breach", "Blue Cross Health", "corporate", "active", "normal"),
    ("FMLA Interference", "Lisa Martinez", "employment", "closed", "low"),
    ("Construction Injury", "Metro Construction", "litigation", "active", "high"),
    ("Insurance Bad Faith", "John Doe", "litigation", "intake", "normal"),
    ("Regulatory Filing — OSHA", "Global Logistics", "regulatory", "active", "normal"),
    ("Patient Consent Review", "Pacific Medical Center", "regulatory", "active", "normal"),
]

DOC_TITLES = [
    "Police Report",
    "Medical Records Summary",
    "Insurance Correspondence",
    "Witness Statement",
    "Expert Report Draft",
    "Demand Letter",
    "Settlement Offer",
    "Court Filing",
    "Deposition Transcript Excerpt",
    "Email Chain — Client",
]

OCR_SNIPPETS = [
    "On March 12, 2026, the insured vehicle was struck at the intersection of Peachtree St and 10th Ave.",
    "Patient presented with cervical strain and lumbar contusion following the motor vehicle collision.",
    "We acknowledge receipt of your claim and assign reference number CLM-2026-88421.",
    "I observed the defendant run the red light while traveling approximately 45 mph.",
    "Based on my review, total economic damages are estimated at $47,500.",
]

AUDIT_ACTIONS = [
    ("case.created", "case"),
    ("document.upload.confirmed", "document"),
    ("ai.summary.generated", "ai_summary"),
    ("ai.summary.approved", "ai_summary"),
    ("workflow.execution.started", "workflow_execution"),
    ("workflow.execution.completed", "workflow_execution"),
    ("client.updated", "client"),
    ("case.status.changed", "case"),
]

NOTIFICATION_TITLES = [
    ("AI summary ready for review", "A new AI-generated case summary is awaiting attorney approval."),
    ("Document processed", "OCR and virus scan completed for an uploaded document."),
    ("Workflow completed", "The document notification workflow finished successfully."),
    ("Approval required", "Managing partner approval is required before workflow trigger."),
    ("Case assigned", "You have been assigned as lead attorney on a new matter."),
]


def _checksum(seed: str) -> str:
    return hashlib.sha256(seed.encode()).hexdigest()


async def _ensure_client(session, firm_id, name, ctype, email, phone) -> Client:
    existing = (
        await session.execute(
            select(Client).where(
                Client.firm_id == firm_id,
                Client.name == name,
                Client.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if existing:
        return existing
    client = Client(firm_id=firm_id, name=name, type=ctype.value, email=email, phone=phone)
    session.add(client)
    await session.flush()
    print(f"OK  Client {name}")
    return client


async def _ensure_case(session, firm_id, jane_id, title, client, practice, status, priority, seq: int) -> Case:
    existing = (
        await session.execute(
            select(Case).where(
                Case.firm_id == firm_id,
                Case.client_id == client.id,
                Case.title == title,
                Case.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if existing:
        return existing
    case_number = f"2026-{seq:05d}"
    case = Case(
        firm_id=firm_id,
        client_id=client.id,
        case_number=case_number,
        title=title,
        practice_area=practice,
        status=status,
        priority=priority,
        lead_attorney_id=jane_id,
    )
    session.add(case)
    await session.flush()
    session.add(
        CaseParticipant(
            case_id=case.id,
            user_id=jane_id,
            role=ParticipantRole.LEAD.value,
            added_by=jane_id,
        )
    )
    print(f"OK  Case {case_number} — {title}")
    return case


async def _ensure_document(
    session,
    *,
    firm_id,
    case_id,
    user_id,
    title: str,
    doc_index: int,
    ocr_done: bool,
    when: datetime,
) -> Document | None:
    existing = (
        await session.execute(
            select(Document).where(
                Document.case_id == case_id,
                Document.title == title,
                Document.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if existing:
        return existing

    doc_id = uuid4()
    s3_key = f"{firm_id}/{case_id}/{doc_id}/v1/{title.replace(' ', '_')}.pdf"
    checksum = _checksum(f"{case_id}-{title}")
    doc = Document(
        id=doc_id,
        case_id=case_id,
        firm_id=firm_id,
        title=title,
        document_type="evidence" if doc_index % 2 == 0 else "correspondence",
        status=DocumentStatus.READY if ocr_done else DocumentStatus.PROCESSING,
        s3_key=s3_key,
        mime_type="application/pdf",
        file_size_bytes=120_000 + doc_index * 4096,
        checksum_sha256=checksum,
        ocr_status=OcrStatus.COMPLETED if ocr_done else OcrStatus.PROCESSING,
        ocr_text=OCR_SNIPPETS[doc_index % len(OCR_SNIPPETS)] if ocr_done else None,
        uploaded_by=user_id,
        created_at=when,
        updated_at=when,
    )
    session.add(doc)
    await session.flush()
    version = DocumentVersion(
        document_id=doc.id,
        version_number=1,
        s3_key=s3_key,
        file_size_bytes=doc.file_size_bytes,
        checksum_sha256=checksum,
        change_summary="Initial upload",
        created_by=user_id,
        created_at=when,
    )
    session.add(version)
    await session.flush()
    doc.current_version_id = version.id
    return doc


async def seed() -> None:
    async with async_session_factory() as session:
        firm = (
            await session.execute(select(Firm).where(Firm.slug == "lexflow-dev"))
        ).scalar_one_or_none()
        if firm is None:
            print("Run make seed first.")
            return

        jane = (
            await session.execute(select(User).where(User.email == "jane@example.com"))
        ).scalar_one_or_none()
        partner = (
            await session.execute(select(User).where(User.email == "partner@example.com"))
        ).scalar_one_or_none()
        if jane is None:
            print("Run make seed first (jane@example.com missing).")
            return

        wf_def = (
            await session.execute(
                select(WorkflowDefinition).where(
                    WorkflowDefinition.slug == "document-upload-v1"
                )
            )
        ).scalar_one_or_none()
        if wf_def is None:
            print("Run make seed-sprint4 first (workflow definition missing).")
            return

        client_map: dict[str, Client] = {}
        for row in CLIENTS:
            client_map[row[0]] = await _ensure_client(session, firm.id, *row)

        case_rows: list[Case] = []
        seq = 1
        for title, client_name, practice, status, priority in CASES:
            client = client_map.get(client_name)
            if client is None:
                continue
            case = await _ensure_case(
                session, firm.id, jane.id, title, client, practice, status, priority, seq
            )
            case_rows.append(case)
            seq += 1

        now = datetime.now(UTC)
        doc_count = 0
        for idx, case in enumerate(case_rows):
            docs_for_case = 2 + (idx % 3)
            for d in range(docs_for_case):
                title = f"{DOC_TITLES[(idx + d) % len(DOC_TITLES)]} — {case.title[:20]}"
                when = now - timedelta(days=30 - idx, hours=d * 3)
                ocr_done = idx != len(case_rows) - 2
                doc = await _ensure_document(
                    session,
                    firm_id=firm.id,
                    case_id=case.id,
                    user_id=jane.id,
                    title=title,
                    doc_index=doc_count,
                    ocr_done=ocr_done,
                    when=when,
                )
                if doc:
                    doc_count += 1

        john_doe_case = next((c for c in case_rows if c.title == "Motor Vehicle Claim"), None)

        for i, case in enumerate(case_rows[:18]):
            existing_summary = (
                await session.execute(
                    select(AISummary).where(
                        AISummary.case_id == case.id,
                        AISummary.summary_type == SummaryType.CASE_OVERVIEW.value,
                    )
                )
            ).scalar_one_or_none()
            if existing_summary:
                continue
            approved = i < 12
            draft = 12 <= i < 15
            status = (
                SummaryStatus.APPROVED
                if approved
                else SummaryStatus.DRAFT
                if draft
                else SummaryStatus.GENERATING
            )
            summary = AISummary(
                case_id=case.id,
                firm_id=firm.id,
                summary_type=SummaryType.CASE_OVERVIEW.value,
                content=(
                    f"## Case overview — {case.title}\n\n"
                    f"Key facts extracted from {2 + (i % 3)} documents. "
                    "Liability appears favorable; recommend demand letter within 30 days."
                ),
                model="stub-gpt-4o",
                prompt_version="document-summary-v1",
                status=status.value,
                requested_by=jane.id,
                approved_by=partner.id if approved and partner else None,
                approved_at=now - timedelta(days=5, hours=i) if approved and partner else None,
                token_count=850 + i * 12,
                created_at=now - timedelta(days=7, hours=i),
            )
            session.add(summary)
            print(f"OK  AI summary for {case.case_number}")

        if john_doe_case:
            existing_wf = (
                await session.execute(
                    select(WorkflowExecution).where(
                        WorkflowExecution.case_id == john_doe_case.id,
                        WorkflowExecution.idempotency_key == "demo-john-doe-wf",
                    )
                )
            ).scalar_one_or_none()
            if not existing_wf:
                started = now - timedelta(days=2)
                session.add(
                    WorkflowExecution(
                        workflow_definition_id=wf_def.id,
                        case_id=john_doe_case.id,
                        firm_id=firm.id,
                        triggered_by=jane.id,
                        status=ExecutionStatus.COMPLETED.value,
                        input_payload={"caseId": str(john_doe_case.id), "demo": True},
                        output_payload={"notified": True},
                        correlation_id=uuid4(),
                        idempotency_key="demo-john-doe-wf",
                        n8n_execution_id="demo-exec-001",
                        started_at=started,
                        completed_at=started + timedelta(minutes=2),
                        created_at=started,
                    )
                )
                print("OK  John Doe workflow execution (completed)")

        failed_case = case_rows[-2] if len(case_rows) >= 2 else None
        if failed_case:
            existing_failed = (
                await session.execute(
                    select(WorkflowExecution).where(
                        WorkflowExecution.case_id == failed_case.id,
                        WorkflowExecution.idempotency_key == "demo-failed-wf",
                    )
                )
            ).scalar_one_or_none()
            if not existing_failed:
                started = now - timedelta(hours=6)
                session.add(
                    WorkflowExecution(
                        workflow_definition_id=wf_def.id,
                        case_id=failed_case.id,
                        firm_id=firm.id,
                        triggered_by=jane.id,
                        status=ExecutionStatus.FAILED.value,
                        input_payload={"caseId": str(failed_case.id)},
                        correlation_id=uuid4(),
                        idempotency_key="demo-failed-wf",
                        error_message="n8n webhook timeout after 30s",
                        started_at=started,
                        completed_at=started + timedelta(seconds=45),
                        created_at=started,
                    )
                )
                print("OK  Failed workflow execution (demo)")

        for i, case in enumerate(case_rows[:8]):
            key = f"demo-wf-{case.id}"
            existing = (
                await session.execute(
                    select(WorkflowExecution).where(WorkflowExecution.idempotency_key == key)
                )
            ).scalar_one_or_none()
            if existing:
                continue
            started = now - timedelta(days=i + 1)
            session.add(
                WorkflowExecution(
                    workflow_definition_id=wf_def.id,
                    case_id=case.id,
                    firm_id=firm.id,
                    triggered_by=jane.id,
                    status=ExecutionStatus.COMPLETED.value,
                    input_payload={"caseId": str(case.id)},
                    output_payload={"status": "ok"},
                    correlation_id=uuid4(),
                    idempotency_key=key,
                    started_at=started,
                    completed_at=started + timedelta(minutes=1, seconds=30),
                    created_at=started,
                )
            )

        active_case = next((c for c in case_rows if c.title == "Cyber Incident Response"), case_rows[0])
        existing_job = (
            await session.execute(
                select(AsyncJob).where(
                    AsyncJob.case_id == active_case.id,
                    AsyncJob.job_type == JobType.AI_SUMMARY,
                    AsyncJob.status == JobStatus.RUNNING,
                )
            )
        ).scalar_one_or_none()
        if not existing_job:
            session.add(
                AsyncJob(
                    firm_id=firm.id,
                    case_id=active_case.id,
                    user_id=jane.id,
                    job_type=JobType.AI_SUMMARY,
                    status=JobStatus.RUNNING,
                    progress=62,
                    resource_type="case",
                    resource_id=active_case.id,
                    started_at=now - timedelta(minutes=4),
                    created_at=now - timedelta(minutes=5),
                )
            )
            print("OK  Active AI job (running)")

        for i, case in enumerate(case_rows[:15]):
            existing_job = (
                await session.execute(
                    select(AsyncJob).where(
                        AsyncJob.case_id == case.id,
                        AsyncJob.job_type == JobType.AI_SUMMARY,
                        AsyncJob.status == JobStatus.COMPLETED,
                    )
                )
            ).scalar_one_or_none()
            if existing_job:
                continue
            started = now - timedelta(days=i + 2, minutes=10)
            completed = started + timedelta(minutes=2, seconds=15 + i)
            session.add(
                AsyncJob(
                    firm_id=firm.id,
                    case_id=case.id,
                    user_id=jane.id,
                    job_type=JobType.AI_SUMMARY,
                    status=JobStatus.COMPLETED,
                    progress=100,
                    resource_type="case",
                    resource_id=case.id,
                    started_at=started,
                    completed_at=completed,
                    created_at=started,
                )
            )

        audit_count = int(
            (await session.execute(select(func.count()).select_from(AuditLog).where(AuditLog.firm_id == firm.id))).scalar_one()
        )
        if audit_count < 40:
            for i in range(40 - audit_count):
                action, resource_type = AUDIT_ACTIONS[i % len(AUDIT_ACTIONS)]
                case = case_rows[i % len(case_rows)]
                session.add(
                    AuditLog(
                        firm_id=firm.id,
                        actor_id=jane.id if i % 3 else (partner.id if partner else jane.id),
                        action=action,
                        resource_type=resource_type,
                        resource_id=case.id,
                        details={"caseId": str(case.id), "seed": True},
                        created_at=now - timedelta(hours=i * 2),
                    )
                )
            print(f"OK  Audit events ({40 - audit_count} added)")

        notif_count = int(
            (
                await session.execute(
                    select(func.count()).select_from(Notification).where(Notification.firm_id == firm.id)
                )
            ).scalar_one()
        )
        if notif_count < 20:
            for i in range(20 - notif_count):
                title, body = NOTIFICATION_TITLES[i % len(NOTIFICATION_TITLES)]
                case = case_rows[i % len(case_rows)]
                recipient = partner if i % 2 == 0 and partner else jane
                session.add(
                    Notification(
                        user_id=recipient.id,
                        case_id=case.id,
                        firm_id=firm.id,
                        channel=NotificationChannel.IN_APP,
                        title=title,
                        body=body,
                        status=NotificationStatus.READ if i % 3 == 0 else NotificationStatus.SENT,
                        read_at=now - timedelta(hours=i) if i % 3 == 0 else None,
                        sent_at=now - timedelta(hours=i + 1),
                        created_at=now - timedelta(hours=i + 1),
                    )
                )
            print(f"OK  Notifications ({20 - notif_count} added)")

        if john_doe_case:
            timeline_count = int(
                (
                    await session.execute(
                        select(func.count())
                        .select_from(CaseTimelineEvent)
                        .where(CaseTimelineEvent.case_id == john_doe_case.id)
                    )
                ).scalar_one()
            )
            if timeline_count < 7:
                events = [
                    ("document.uploaded", "Document uploaded", 10),
                    ("document.virus_scan.completed", "Virus scan passed", 9),
                    ("document.ocr.completed", "OCR completed", 8),
                    ("ai.summary.ready", "AI summary generated", 7),
                    ("ai.summary.approved", "Summary approved by attorney", 6),
                    ("notification.sent", "Managing partner notified", 5),
                    ("workflow.triggered", "Workflow triggered", 4),
                ]
                for event_type, title, days_ago in events:
                    existing = (
                        await session.execute(
                            select(CaseTimelineEvent).where(
                                CaseTimelineEvent.case_id == john_doe_case.id,
                                CaseTimelineEvent.event_type == event_type,
                            )
                        )
                    ).scalar_one_or_none()
                    if existing:
                        continue
                    session.add(
                        CaseTimelineEvent(
                            case_id=john_doe_case.id,
                            firm_id=firm.id,
                            event_type=event_type,
                            title=title,
                            payload={"demo": True},
                            actor_id=jane.id,
                            occurred_at=now - timedelta(days=days_ago),
                        )
                    )
                print("OK  John Doe timeline events")

        await session.commit()

        final_clients = int(
            (await session.execute(select(func.count()).select_from(Client).where(Client.firm_id == firm.id))).scalar_one()
        )
        final_cases = int(
            (
                await session.execute(
                    select(func.count()).select_from(Case).where(
                        Case.firm_id == firm.id, Case.deleted_at.is_(None)
                    )
                )
            ).scalar_one()
        )
        final_docs = int(
            (
                await session.execute(
                    select(func.count()).select_from(Document).where(
                        Document.firm_id == firm.id, Document.deleted_at.is_(None)
                    )
                )
            ).scalar_one()
        )
        print(
            f"Demo data seed complete — {final_clients} clients, {final_cases} cases, {final_docs} documents."
        )


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
