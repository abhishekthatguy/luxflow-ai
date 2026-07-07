"""Supported practice areas — keep in sync with @lexflow/shared PRACTICE_AREAS."""

from enum import StrEnum


class PracticeArea(StrEnum):
    LITIGATION = "litigation"
    CORPORATE = "corporate"
    IP = "ip"
    REGULATORY = "regulatory"
    EMPLOYMENT = "employment"
    REAL_ESTATE = "real_estate"
    FAMILY = "family"
    IMMIGRATION = "immigration"
    CRIMINAL = "criminal"
    OTHER = "other"


PRACTICE_AREA_LABELS: dict[str, str] = {
    PracticeArea.LITIGATION: "Litigation",
    PracticeArea.CORPORATE: "Corporate & Transactional",
    PracticeArea.IP: "Intellectual Property",
    PracticeArea.REGULATORY: "Regulatory & Compliance",
    PracticeArea.EMPLOYMENT: "Employment & Labor",
    PracticeArea.REAL_ESTATE: "Real Estate",
    PracticeArea.FAMILY: "Family Law",
    PracticeArea.IMMIGRATION: "Immigration",
    PracticeArea.CRIMINAL: "Criminal Defense",
    PracticeArea.OTHER: "Other",
}

PRACTICE_AREA_VALUES: frozenset[str] = frozenset(PRACTICE_AREA_LABELS)


def is_valid_practice_area(value: str | None) -> bool:
    return value is not None and value in PRACTICE_AREA_VALUES


def practice_area_options() -> list[dict[str, str]]:
    return [{"value": key, "label": label} for key, label in PRACTICE_AREA_LABELS.items()]
