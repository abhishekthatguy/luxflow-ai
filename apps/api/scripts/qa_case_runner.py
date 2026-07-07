"""Shared QA utilities for LexFlow API case walkthrough scripts."""

from __future__ import annotations

import hashlib
import mimetypes
import time
from collections.abc import Callable

from dataclasses import dataclass
from pathlib import Path

import httpx

BASE = "http://localhost:8000"
DOCS_ROOT = Path(__file__).resolve().parents[3] / "docs" / "sample-cases-test" / "documents"

PASS: list[tuple[str, str]] = []
FAIL: list[tuple[str, str]] = []
WARN: list[tuple[str, str]] = []

PIPELINE_STAGES = [
    "Uploaded",
    "Virus Scan",
    "OCR",
    "AI Summary",
    "Human Approval",
    "Workflow Triggered",
    "Completed",
]

ATTORNEY_EMAIL = "jane@example.com"
ATTORNEY_PASSWORD = "password123"
PARTNER_EMAIL = "partner@example.com"
PARTNER_PASSWORD = "password123"

AUTHORITY_EVENT_TYPES = {
    "authority.police.notified",
    "authority.insurance.notified",
    "authority.medical.notified",
    "authority.dmv.notified",
    "authority.photos.notified",
}


@dataclass
class CaseConfig:
    name: str
    client_name: str
    client_email: str
    client_phone: str
    case_title: str
    practice_area: str
    documents: list[tuple[str, str, str]]
    expected_sections: list[str]
    min_sections: int
    priority: str | None = None

    @property
    def document_count(self) -> int:
        return len(self.documents)


def reset_report() -> None:
    PASS.clear()
    FAIL.clear()
    WARN.clear()


def ok(step: str, detail: str = "") -> None:
    PASS.append((step, detail))
    print(f"  PASS  {step}" + (f" — {detail}" if detail else ""))


def bad(step: str, detail: str) -> None:
    FAIL.append((step, detail))
    print(f"  FAIL  {step} — {detail}")


def warn(step: str, detail: str) -> None:
    WARN.append((step, detail))
    print(f"  WARN  {step} — {detail}")


def login(email: str, password: str, *, max_attempts: int = 8) -> str:
    last_response: httpx.Response | None = None
    for attempt in range(max_attempts):
        response = httpx.post(
            f"{BASE}/api/v1/auth/login",
            json={"email": email, "password": password},
            timeout=30,
        )
        last_response = response
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", min(65, 5 * (attempt + 1))))
            time.sleep(retry_after)
            continue
        response.raise_for_status()
        return response.json()["data"]["accessToken"]
    if last_response is not None:
        last_response.raise_for_status()
    raise RuntimeError("login failed without a response")


def headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def doc_path(filename: str, subdir: str) -> Path:
    if subdir:
        return DOCS_ROOT / subdir / filename
    return DOCS_ROOT / filename


def _mime_type(path: Path) -> str:
    if path.suffix.lower() == ".zip":
        return "application/zip"
    guessed, _ = mimetypes.guess_type(path.name)
    return guessed or "application/octet-stream"


def upload_document(
    case_id: str,
    token: str,
    filepath: Path,
    title: str,
    *,
    step: str | None = None,
) -> str | None:
    label = step or f"4. Upload {filepath.name}"
    if not filepath.exists():
        bad(label, f"Missing {filepath}")
        return None

    content = filepath.read_bytes()
    checksum = hashlib.sha256(content).hexdigest()
    mime_type = _mime_type(filepath)
    request_headers = headers(token)

    init = httpx.post(
        f"{BASE}/api/v1/cases/{case_id}/documents",
        headers=request_headers,
        json={
            "title": title,
            "filename": filepath.name,
            "mimeType": mime_type,
            "fileSizeBytes": len(content),
            "checksumSha256": checksum,
            "documentType": "evidence",
        },
        timeout=30,
    )
    if init.status_code not in (200, 201):
        bad(f"{label} init", init.text[:200])
        return None

    doc = init.json()["data"]
    doc_id = doc["id"]
    upload_url = doc.get("uploadUrl")
    if upload_url:
        put = httpx.put(
            upload_url,
            content=content,
            headers={"Content-Type": mime_type},
            timeout=30,
        )
        if put.status_code not in (200, 204):
            bad(f"{label} PUT", f"HTTP {put.status_code}")
            return None

    confirm = httpx.post(
        f"{BASE}/api/v1/documents/{doc_id}/confirm",
        headers=request_headers,
        json={"checksumSha256": checksum},
        timeout=30,
    )
    if confirm.status_code != 200:
        bad(f"{label} confirm", confirm.text[:200])
        return None

    ok(label, doc_id[:8])
    return doc_id


def upload_documents(case_id: str, token: str, config: CaseConfig) -> list[str]:
    uploaded: list[str] = []
    for filename, title, subdir in config.documents:
        doc_id = upload_document(
            case_id,
            token,
            doc_path(filename, subdir),
            title,
            step=f"4. Upload {filename}",
        )
        if doc_id:
            uploaded.append(doc_id)
    return uploaded


def wait_for_ocr(
    case_id: str,
    token: str,
    count: int,
    timeout: int | None = None,
    *,
    poll_interval: int = 5,
) -> bool:
    if timeout is None:
        timeout = max(120, count * 30)
    request_headers = headers(token)
    deadline = time.time() + timeout
    ocr_done: list[dict] = []

    while time.time() < deadline:
        docs = httpx.get(
            f"{BASE}/api/v1/cases/{case_id}/documents",
            headers=request_headers,
            timeout=30,
        ).json()["data"]
        ocr_done = [doc for doc in docs if doc.get("ocrStatus") in ("completed", "skipped")]
        if len(ocr_done) >= count:
            ok("4b. OCR completed", f"{len(ocr_done)} documents ready")
            return True
        time.sleep(poll_interval)

    bad("4b. OCR completed", f"Only {len(ocr_done)}/{count} after {timeout}s")
    return False


def request_and_wait_summary(
    case_id: str,
    token: str,
    timeout: int | None = None,
    *,
    poll_interval: int = 3,
    document_count: int = 3,
) -> dict | None:
    if timeout is None:
        timeout = max(90, document_count * 25)
    request_headers = headers(token)
    summaries = httpx.get(
        f"{BASE}/api/v1/cases/{case_id}/ai/summaries",
        headers=request_headers,
        timeout=30,
    ).json()["data"]
    summary = next((item for item in summaries if item.get("status") == "draft"), None)
    if summary:
        return summary

    summarize = httpx.post(
        f"{BASE}/api/v1/cases/{case_id}/ai/summarize",
        headers=request_headers,
        json={"summaryType": "case_overview"},
        timeout=30,
    )
    if summarize.status_code not in (200, 202):
        bad("5. Request AI summary", summarize.text[:200])
        return None

    job_id = summarize.json()["data"].get("jobId")
    ok("5. AI summary requested", f"job={job_id}")

    deadline = time.time() + timeout
    while time.time() < deadline:
        summaries = httpx.get(
            f"{BASE}/api/v1/cases/{case_id}/ai/summaries",
            headers=request_headers,
            timeout=30,
        ).json()["data"]
        draft = next((item for item in summaries if item.get("status") == "draft"), None)
        if draft:
            return draft
        time.sleep(poll_interval)

    bad("5b. AI draft generated", f"No draft after {timeout}s")
    return None


def check_summary_sections(summary: dict, config: CaseConfig) -> None:
    content = summary.get("content") or ""
    found = sum(1 for section in config.expected_sections if section.lower() in content.lower())
    total = len(config.expected_sections)
    if found >= config.min_sections:
        ok("5b. AI structured content", f"{found}/{total} expected sections present")
    else:
        warn(
            "5b. AI structured content",
            f"only {found}/{total} sections; content preview: {content[:120]}…",
        )


def edit_summary(
    summary: dict,
    token: str,
    *,
    suffix: str = "\n\n**Firm note:** Review denial basis with coverage counsel.",
) -> bool:
    patch = httpx.patch(
        f"{BASE}/api/v1/ai/summaries/{summary['id']}",
        headers=headers(token),
        json={"content": (summary.get("content") or "") + suffix},
        timeout=30,
    )
    if patch.status_code == 200:
        ok("6. Edit draft summary", "PATCH saved")
        return True
    bad("6. Edit draft summary", patch.text[:200])
    return False


def approve_summary(summary_id: str, token: str) -> bool:
    approve = httpx.post(
        f"{BASE}/api/v1/ai/summaries/{summary_id}/approve",
        headers=headers(token),
        timeout=30,
    )
    if approve.status_code == 200 and approve.json()["data"].get("status") == "approved":
        ok("7. Approve summary", "status=approved")
        return True
    bad("7. Approve summary", approve.text[:200])
    return False


def check_pipeline(case_id: str, token: str) -> None:
    pipeline_resp = httpx.get(
        f"{BASE}/api/v1/operations/cases/{case_id}/pipeline",
        headers=headers(token),
        timeout=30,
    )
    if pipeline_resp.status_code != 200:
        bad("4c. Processing timeline", f"HTTP {pipeline_resp.status_code}")
        return

    pipeline = pipeline_resp.json()["data"]
    labels = [stage["label"] for stage in pipeline.get("stages", [])]
    if labels == PIPELINE_STAGES:
        ok("4c. Processing timeline stages", f"{len(PIPELINE_STAGES)} stages match spec")
    else:
        bad("4c. Processing timeline", f"got {labels}")


def check_audit(partner_token: str) -> None:
    audit = httpx.get(
        f"{BASE}/api/v1/audit/logs?pageSize=50",
        headers=headers(partner_token),
        timeout=30,
    )
    if audit.status_code == 403:
        bad("8. Partner audit access", "403 Forbidden")
    elif audit.status_code == 200:
        actions = {log["action"] for log in audit.json()["data"]}
        needed = {"case.created", "document.upload.confirmed", "ai.summary.approved"}
        found = needed & actions
        if len(found) >= 2:
            ok("8. Audit trail", f"found: {', '.join(sorted(found))}")
        else:
            warn("8. Audit trail", f"expected subset of {needed}, got recent: {sorted(actions)[:8]}")
    else:
        bad("8. Partner audit", f"HTTP {audit.status_code}")


def check_notification(partner_token: str) -> None:
    notifs = httpx.get(
        f"{BASE}/api/v1/notifications",
        headers=headers(partner_token),
        timeout=30,
    ).json()["data"]
    approval_notif = next(
        (
            item
            for item in notifs
            if "summary" in item.get("title", "").lower() or "approv" in item.get("title", "").lower()
        ),
        None,
    )
    if approval_notif:
        ok("9. Partner notification", approval_notif.get("title"))
    else:
        warn("9. Partner notification", f"No approval notification; {len(notifs)} total notifications")


def check_workflow_executions(
    case_id: str,
    token: str,
    *,
    min_count: int = 1,
    timeout: int = 120,
    poll_interval: int = 5,
) -> bool:
    """Wait for WF-02 document-upload workflow runs after OCR."""
    request_headers = headers(token)
    deadline = time.time() + timeout
    completed: list[dict] = []

    while time.time() < deadline:
        response = httpx.get(
            f"{BASE}/api/v1/cases/{case_id}/workflows",
            headers=request_headers,
            timeout=30,
        )
        if response.status_code != 200:
            bad("4d. WF-02 executions", f"HTTP {response.status_code}")
            return False

        executions = response.json()["data"]
        completed = [
            item
            for item in executions
            if item.get("status") in ("completed", "running", "pending")
            and (item.get("workflowSlug") == "document-upload-v1" or "upload" in (item.get("workflowName") or "").lower())
        ]
        failed = [
            item
            for item in executions
            if item.get("status") == "failed"
            and (item.get("workflowSlug") == "document-upload-v1" or "upload" in (item.get("workflowName") or "").lower())
        ]
        if failed:
            err = failed[0].get("errorMessage") or "unknown"
            bad("4d. WF-02 executions", f"failed: {err[:120]}")
            return False
        if len(completed) >= min_count:
            ok("4d. WF-02 executions", f"{len(completed)} document-upload runs recorded")
            return True
        time.sleep(poll_interval)

    bad("4d. WF-02 executions", f"Only {len(completed)}/{min_count} after {timeout}s")
    return False


def check_authority_timeline(
    case_id: str,
    token: str,
    expected_types: set[str],
) -> None:
    response = httpx.get(
        f"{BASE}/api/v1/cases/{case_id}/timeline?pageSize=100",
        headers=headers(token),
        timeout=30,
    )
    if response.status_code != 200:
        bad("4e. Authority routing", f"HTTP {response.status_code}")
        return

    found = {event.get("eventType") for event in response.json()["data"]}
    matched = expected_types & found
    if len(matched) >= 3:
        ok("4e. Authority routing", f"{len(matched)} authority events: {', '.join(sorted(matched))}")
    else:
        warn(
            "4e. Authority routing",
            f"expected several of {sorted(expected_types)}, found {sorted(matched)}",
        )


def check_document_storage_keys(case_id: str, token: str, count: int) -> None:
    """Confirm uploads received S3 keys (MinIO lexflow-local-documents)."""
    docs = httpx.get(
        f"{BASE}/api/v1/cases/{case_id}/documents",
        headers=headers(token),
        timeout=30,
    ).json()["data"]
    with_keys = [doc for doc in docs if doc.get("id")]
    if len(with_keys) >= count:
        ok(
            "4f. Document storage",
            f"{len(with_keys)} docs in API — objects land in MinIO bucket lexflow-local-documents",
        )
    else:
        bad("4f. Document storage", f"only {len(with_keys)}/{count} documents")


def check_operations_dashboard(token: str) -> None:
    dash = httpx.get(f"{BASE}/api/v1/operations/dashboard", headers=headers(token), timeout=30)
    if dash.status_code != 200:
        bad("10. Operations dashboard", f"HTTP {dash.status_code}")
        return

    data = dash.json()["data"]
    celery = next((item for item in data.get("health", []) if item.get("name") == "Celery"), None)
    if celery and celery.get("status") == "healthy":
        ok("10. Operations dashboard", f"Celery {celery.get('detail')}")
    elif celery:
        bad("10. Celery worker health", celery.get("detail") or celery.get("status"))
    else:
        ok("10. Operations dashboard", f"health={len(data.get('health', []))} components")


def find_client(token: str, config: CaseConfig) -> dict | None:
    clients = httpx.get(f"{BASE}/api/v1/clients", headers=headers(token), timeout=30).json()["data"]
    client = next((item for item in clients if item.get("name") == config.client_name), None)
    if client:
        ok("2. Client exists", f"{config.client_name} id={client['id'][:8]}…")
        if client.get("email") == config.client_email and client.get("phone"):
            ok("2b. Client contact fields", f"{client['email']} / {client.get('phone')}")
        else:
            warn(
                "2b. Client contact fields",
                f"email={client.get('email')} phone={client.get('phone')}",
            )
        return client

    bad(
        "2. Client lookup",
        f"{config.client_name} not found — run make seed-demo-data or seed-simple-case",
    )
    return None


def create_case(token: str, client_id: str, config: CaseConfig) -> dict | None:
    me = httpx.get(f"{BASE}/api/v1/auth/me", headers=headers(token), timeout=30).json()["data"]
    qa_title = f"{config.case_title} QA-{int(time.time())}"
    payload: dict[str, str] = {
        "clientId": client_id,
        "title": qa_title,
        "practiceArea": config.practice_area,
        "leadAttorneyId": me["id"],
    }
    if config.priority:
        payload["priority"] = config.priority

    create = httpx.post(
        f"{BASE}/api/v1/cases",
        headers=headers(token),
        json=payload,
        timeout=30,
    )
    if create.status_code != 201:
        bad("3. Create case", create.text[:200])
        return None

    case = create.json()["data"]
    ok("3. Case created", f"{case.get('caseNumber')} — {case.get('title')}")
    if case.get("practiceArea") == config.practice_area:
        ok("3b. Practice area", config.practice_area)
    else:
        warn("3b. Practice area", f"expected {config.practice_area}, got {case.get('practiceArea')}")
    return case


def run_case_walkthrough(
    config: CaseConfig,
    *,
    edit_suffix: str = "\n\n**Firm note:** Review denial basis with coverage counsel.",
    spec_gaps: list[tuple[str, str]] | None = None,
    extra_checks: Callable[[str, str, CaseConfig], None] | None = None,
    summary_timeout: int | None = None,
) -> int:
    """Execute the standard QA flow for a configured case."""
    reset_report()
    print(f"\n=== QA: {config.name} ===\n")

    try:
        attorney_token = login(ATTORNEY_EMAIL, ATTORNEY_PASSWORD)
        ok("1. Attorney login", ATTORNEY_EMAIL)
    except Exception as exc:
        bad("1. Attorney login", str(exc))
        return print_report(spec_gaps=spec_gaps)

    client = find_client(attorney_token, config)
    if not client:
        return print_report(spec_gaps=spec_gaps)

    case = create_case(attorney_token, client["id"], config)
    if not case:
        return print_report(spec_gaps=spec_gaps)

    case_id = case["id"]
    upload_documents(case_id, attorney_token, config)
    wait_for_ocr(case_id, attorney_token, config.document_count)
    check_pipeline(case_id, attorney_token)
    if extra_checks is not None:
        extra_checks(case_id, attorney_token, config)

    summary = request_and_wait_summary(
        case_id,
        attorney_token,
        timeout=summary_timeout,
        document_count=config.document_count,
    )
    if summary:
        check_summary_sections(summary, config)
        edit_summary(summary, attorney_token, suffix=edit_suffix)
        approve_summary(summary["id"], attorney_token)

    partner_token = login(PARTNER_EMAIL, PARTNER_PASSWORD)
    check_audit(partner_token)
    check_notification(partner_token)
    check_operations_dashboard(attorney_token)

    return print_report(spec_gaps=spec_gaps)


def print_report(*, spec_gaps: list[tuple[str, str]] | None = None) -> int:
    print("\n=== QA SUMMARY ===")
    print(f"PASS: {len(PASS)}  WARN: {len(WARN)}  FAIL: {len(FAIL)}")
    for step, detail in FAIL:
        print(f"  FAIL  {step}: {detail}")
    for step, detail in WARN:
        print(f"  WARN  {step}: {detail}")

    if spec_gaps:
        print("\n=== SPEC vs PORTAL ===")
        for spec, actual in spec_gaps:
            print(f"  GAP  {spec} → {actual}")

    return 1 if FAIL else 0
