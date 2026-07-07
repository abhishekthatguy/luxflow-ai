"""Structured motor-vehicle / insurance claim summary for demo (stub LLM path)."""

from __future__ import annotations

import re
from typing import Any

from lexflow_api.services.llm.types import LLMResult


def is_insurance_mva_context(*, case_title: str, context: str) -> bool:
    """Detect insurance accident demo from case title and uploaded document text."""
    combined = f"{case_title}\n{context}".lower()
    signals = (
        "motor vehicle",
        "accident",
        "insurance",
        "police",
        "claim",
        "policy",
        "john doe",
        "statefarm",
    )
    return sum(1 for s in signals if s in combined) >= 3


def _find(pattern: str, text: str, default: str = "See documents") -> str:
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    if match:
        for group in match.groups():
            if group:
                return group.strip()
    return default


def build_insurance_mva_summary(*, case_title: str, context: str) -> LLMResult:
    """Produce attorney-review draft with sections expected in the simple demo."""
    incident_date = _find(
        r"Date of Incident:\s*(.+)|Date of Exam:\s*(.+)|Date of loss:\s*(.+)|Date:\s*(March \d+, \d{4})",
        context,
        "March 15, 2026",
    )
    location = _find(
        r"Location:\s*(.+)",
        context,
        "Peachtree Street NE & 10th Street NE, Atlanta, GA",
    )
    claimant = _find(
        r"Driver:\s*(.+)|Patient:\s*(.+)|Insured:\s*(.+)|Name:\s*(.+)",
        context,
        "Claimant",
    )
    policy = _find(r"Policy(?: Number)?:\s*(POL-[\d]+)", context, "POL-8844221")
    claim_no = _find(r"Claim Number:\s*(CLM-[\d-]+)", context, "CLM-2026-8891")
    amount = _find(r"Total amount claimed:\s*\$?([\d,]+)", context, "24,500")
    denial = _find(
        r"denying coverage for (.+?)(?:\.|\n)",
        context,
        "medical expenses citing pre-existing condition",
    )

    content = f"""## Motor Vehicle Insurance Claim — Draft Summary

**Case:** {case_title}

### Incident Overview
- **Incident date:** {incident_date}
- **Location:** {location}
- **Claimant / client:** {claimant}

### People Involved
- **Claimant driver:** {claimant}
- **At-fault party:** Unknown driver, 2019 Honda Civic (fled scene)
- **Witness:** Maria Chen
- **Officer:** Officer James Martinez, Badge #4421

### Injuries & Medical
- Cervical strain (whiplash) and lumbar sprain
- EMS transport to Atlanta Medical Center; exam March 16, 2026
- Estimated medical costs to date: $8,200
- Treatment: rest, anti-inflammatories, PT referral, 2-week work restriction

### Insurance & Claim
- **Carrier / policy:** StateFarm Mutual — {policy}
- **Claim number:** {claim_no}
- **Amount claimed:** ${amount} (medical + vehicle repair + rental)
- **Coverage determination:** Denial of medical expenses — {denial}
- Vehicle damage liability under investigation

### Potential Liability
- Third party ran red light; police report attributes failure to yield / reckless driving
- Insurer dispute on medical coverage may not bar third-party tort recovery

### Recommended Next Actions
1. Obtain certified police report and preserve EMS/hospital records
2. File appeal of coverage denial within 30-day window
3. Request independent medical examination if carrier maintains pre-existing defense
4. Document vehicle repair estimates and rental receipts
5. Evaluate uninsured motorist / liability claim against at-fault driver when identified

---
_This draft was generated from uploaded police, medical, and insurance documents. Attorney review and edits required before sharing with the team or client._"""

    return LLMResult(
        content=content,
        input_tokens=max(len(context) // 4, 200),
        output_tokens=max(len(content) // 4, 400),
        model="stub-insurance-mva-v1",
        provider="stub",
    )


def maybe_insurance_summary(
    *, case_title: str, context: str, llm_config: dict[str, Any]
) -> LLMResult | None:
    """Explicit demo scenario only — normal path uses Ollama via complete_with_fallback."""
    if llm_config.get("scenario") == "insurance_mva":
        return build_insurance_mva_summary(case_title=case_title, context=context)
    return None
