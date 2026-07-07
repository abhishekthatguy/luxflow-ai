"""Tests for case number generation and practice area validation."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from lexflow_api.domain.practice_areas import is_valid_practice_area, practice_area_options
from lexflow_api.schemas.cases import CaseCreate


def test_practice_area_options_not_empty() -> None:
    options = practice_area_options()
    assert len(options) >= 7
    assert options[0]["value"]
    assert options[0]["label"]


def test_is_valid_practice_area() -> None:
    assert is_valid_practice_area("litigation") is True
    assert is_valid_practice_area("corporate") is True
    assert is_valid_practice_area("not-a-real-area") is False


def test_case_create_omits_case_number() -> None:
    payload = CaseCreate(
        client_id=uuid4(),
        title="Test matter",
        lead_attorney_id=uuid4(),
    )
    assert payload.case_number is None
    assert payload.practice_area == "litigation"


def test_case_create_rejects_invalid_practice_area() -> None:
    with pytest.raises(ValidationError):
        CaseCreate(
            client_id=uuid4(),
            title="Test matter",
            practice_area="unknown-area",
            lead_attorney_id=uuid4(),
        )


def test_case_create_accepts_explicit_case_number() -> None:
    payload = CaseCreate(
        client_id=uuid4(),
        case_number="2026-99999",
        title="Legacy import",
        lead_attorney_id=uuid4(),
    )
    assert payload.case_number == "2026-99999"
