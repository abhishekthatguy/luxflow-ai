"""Senior QA — Ransomware Attack Investigation (Acme Corporation) API walkthrough."""

from __future__ import annotations

import sys

from qa_case_runner import CaseConfig, run_case_walkthrough

CONFIG = CaseConfig(
    name="Complex Case — Ransomware Attack Investigation",
    client_name="Acme Corporation",
    client_email="contact@acme.example",
    client_phone="+1-555-0100",
    case_title="Ransomware Attack Investigation",
    practice_area="corporate",
    priority="urgent",
    documents=[
        ("incident_report.txt", "Incident Report", "complex"),
        ("security_audit.txt", "Security Audit", "complex"),
        ("firewall_logs.txt", "Firewall Logs", "complex"),
        ("email_threads.txt", "Email Threads", "complex"),
        ("vendor_contract.txt", "Vendor Contract", "complex"),
        ("cyber_insurance_policy.txt", "Cyber Insurance Policy", "complex"),
        ("customer_complaint.txt", "Customer Complaint", "complex"),
        ("forensic_report.txt", "Forensic Report", "complex"),
    ],
    expected_sections=[
        "Incident",
        "Systems",
        "PII",
        "Insurance",
        "Regulatory",
        "Risk",
        "Executive",
        "Action",
    ],
    min_sections=5,
)

SPEC_GAPS = [
    ("Case number CYB-2026-0045", "Auto-assigned YYYY-NNNNN format instead"),
    ("Practice area 'Cyber Security'", "Portal uses 'corporate' — no cyber_security practice area"),
    ("Priority 'Critical'", "Portal uses 'urgent' priority enum"),
    ("PDF/.msg uploads", "Walkthrough uses .txt samples in documents/complex/"),
    ("Workflow 'Email Compliance Team' step", "n8n orchestration separate from this API walkthrough"),
]


def main() -> int:
    return run_case_walkthrough(
        CONFIG,
        edit_suffix="\n\n**Firm note:** Coordinate breach notification timeline with compliance counsel.",
        spec_gaps=SPEC_GAPS,
    )


if __name__ == "__main__":
    sys.exit(main())
