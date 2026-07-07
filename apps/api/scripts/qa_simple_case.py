"""Senior QA — Motor Vehicle Insurance Claim (John Doe) API walkthrough."""

from __future__ import annotations

import sys

from qa_case_runner import CaseConfig, run_case_walkthrough

CONFIG = CaseConfig(
    name="Simple Case — Motor Vehicle Insurance Claim",
    client_name="John Doe",
    client_email="john.doe@gmail.com",
    client_phone="+1-404-555-0101",
    case_title="Motor Vehicle Accident Claim",
    practice_area="litigation",
    documents=[
        ("police_report.txt", "Police Report", ""),
        ("medical_report.txt", "Medical Report", ""),
        ("insurance_letter.txt", "Insurance Letter", ""),
    ],
    expected_sections=[
        "Incident",
        "People",
        "Injuries",
        "Insurance",
        "Liability",
        "Next",
    ],
    min_sections=4,
)

SPEC_GAPS = [
    ("Practice area 'Insurance Defense'", "Portal uses 'Litigation' — no insurance_defense practice area"),
    ("Case number AUTO-2026-0001", "Auto-assigned YYYY-NNNNN format instead"),
    ("PDF uploads (Police_Report.pdf)", "Walkthrough uses .txt samples — PDF OCR path not validated here"),
    ("Vehicle_Photos.zip", "No zip upload in this run"),
    ("Workflow 'Notify Attorney' step", "Notification on approve exists; n8n step separate"),
]


def main() -> int:
    return run_case_walkthrough(CONFIG, spec_gaps=SPEC_GAPS)


if __name__ == "__main__":
    sys.exit(main())
