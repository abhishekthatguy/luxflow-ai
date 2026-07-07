"""Senior QA — Abhishek S motor vehicle claim with real PDF + zip uploads."""

from __future__ import annotations

import sys

from qa_case_runner import (
    AUTHORITY_EVENT_TYPES,
    CaseConfig,
    check_authority_timeline,
    check_document_storage_keys,
    check_workflow_executions,
    run_case_walkthrough,
)

CONFIG = CaseConfig(
    name="Abhishek S — Motor Vehicle Insurance (PDF + ZIP)",
    client_name="Abhishek S",
    client_email="kashyapabhi688@gmail.com",
    client_phone="+91-9621482434",
    case_title="Motor Vehicle Insurance Claim — Abhishek S",
    practice_area="litigation",
    documents=[
        ("Police_Report.pdf", "Police Report", "abhishek"),
        ("Insurance_Claim_Form.pdf", "Insurance Claim Form", "abhishek"),
        ("Vehicle_Photos.zip", "Vehicle Photos", "abhishek"),
        ("Medical_Report.pdf", "Medical Report", "abhishek"),
        ("Driver_License.pdf", "Driver License", "abhishek"),
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
    (
        "Authority SMS/email to police/insurance",
        "Timeline events + internal logs only — no external authority API",
    ),
]


def main() -> int:
    return run_case_walkthrough(
        CONFIG,
        spec_gaps=SPEC_GAPS,
        extra_checks=_abhishek_checks,
        edit_suffix="\n\n**Firm note:** Coordinate with HDFC ERGO adjuster on denial basis.",
        summary_timeout=180,
    )


def _abhishek_checks(case_id: str, token: str, config: CaseConfig) -> None:
    check_document_storage_keys(case_id, token, config.document_count)
    check_workflow_executions(case_id, token, min_count=config.document_count)
    check_authority_timeline(case_id, token, AUTHORITY_EVENT_TYPES)


if __name__ == "__main__":
    sys.exit(main())
