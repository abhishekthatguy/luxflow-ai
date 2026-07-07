"""Tests for insurance MVA demo summary builder."""

from lexflow_api.services.llm.insurance_mva import (
    build_insurance_mva_summary,
    is_insurance_mva_context,
    maybe_insurance_summary,
)

SAMPLE_CONTEXT = """
Case title: Motor Vehicle Accident Claim
--- police_report.txt ---
Date of Incident: March 15, 2026
Location: Peachtree Street NE & 10th Street NE, Atlanta, GA
Driver: John Doe
Policy: POL-8844221
--- medical_report.txt ---
Patient: John Doe
Estimated medical costs: $8,200
--- insurance_letter.txt ---
Claim Number: CLM-2026-8891
Total amount claimed: $24,500
denying coverage for medical expenses citing pre-existing condition
StateFarm Mutual
"""


def test_detects_insurance_context() -> None:
    assert is_insurance_mva_context(
        case_title="Motor Vehicle Accident Claim",
        context=SAMPLE_CONTEXT,
    )


def test_builds_structured_sections() -> None:
    result = build_insurance_mva_summary(
        case_title="Motor Vehicle Accident Claim",
        context=SAMPLE_CONTEXT,
    )
    assert "Incident Overview" in result.content
    assert "Injuries & Medical" in result.content
    assert "Insurance & Claim" in result.content
    assert "Recommended Next Actions" in result.content
    assert "CLM-2026-8891" in result.content
    assert result.provider == "stub"


def test_maybe_insurance_returns_none_for_unrelated() -> None:
    assert (
        maybe_insurance_summary(
            case_title="Unrelated matter",
            context="Generic contract text without insurance keywords.",
            llm_config={},
        )
        is None
    )
