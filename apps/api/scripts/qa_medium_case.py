"""Senior QA — Wrongful Termination (Sarah Johnson) API walkthrough."""

from __future__ import annotations

import sys

from qa_case_runner import CaseConfig, run_case_walkthrough

CONFIG = CaseConfig(
    name="Medium Case — Wrongful Termination",
    client_name="Sarah Johnson",
    client_email="sarah.j@example.com",
    client_phone="+1-404-555-0102",
    case_title="Wrongful Termination",
    practice_area="employment",
    documents=[
        ("employment_contract.txt", "Employment Contract", "medium"),
        ("termination_letter.txt", "Termination Letter", "medium"),
        ("email_conversation.txt", "Email Conversation", "medium"),
        ("salary_slips.txt", "Salary Slips", "medium"),
        ("employee_handbook.txt", "Employee Handbook", "medium"),
    ],
    expected_sections=[
        "Employer",
        "Employee",
        "Termination",
        "Notice",
        "Violation",
        "Risk",
    ],
    min_sections=4,
)

SPEC_GAPS = [
    ("Case number EMP-2026-0007", "Auto-assigned YYYY-NNNNN format instead"),
    ("PDF uploads (Employment Contract.pdf)", "Walkthrough uses .txt samples in documents/medium/"),
    ("Workflow 'Client Notification' step", "Notification on approve exists; n8n step separate"),
]


def main() -> int:
    return run_case_walkthrough(
        CONFIG,
        edit_suffix="\n\n**Firm note:** Confirm notice-period compliance before demand letter.",
        spec_gaps=SPEC_GAPS,
    )


if __name__ == "__main__":
    sys.exit(main())
