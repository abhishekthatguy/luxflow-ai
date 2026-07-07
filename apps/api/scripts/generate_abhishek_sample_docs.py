"""Generate sample PDFs and zip for Abhishek S motor vehicle insurance claim."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import fitz

CLIENT = {
    "name": "Abhishek S",
    "phone": "+91-9621482434",
    "email": "kashyapabhi688@gmail.com",
}
INCIDENT_DATE = "March 15, 2026"
LOCATION = "Koramangala 5th Block Junction, Bengaluru, Karnataka"
VEHICLE = "Honda City — KA-03-AB-4521"


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "docs" / "sample-cases-test").is_dir():
            return parent
    return here.parents[3]


OUT_DIR = _repo_root() / "docs" / "sample-cases-test" / "documents" / "abhishek"


def _write_pdf(path: Path, title: str, body: str) -> None:
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    text = f"{title}\n\n{body.strip()}\n"
    page.insert_textbox(
        fitz.Rect(50, 50, 545, 792),
        text,
        fontsize=11,
        fontname="helv",
    )
    doc.save(path)
    doc.close()


def _police_report() -> str:
    return f"""
Report No: BLR-TRAFFIC-2026-03412
Date of Incident: {INCIDENT_DATE}
Reporting Officer: SI Ramesh Kumar, Koramangala Traffic Police

COMPLAINANT
Name: {CLIENT["name"]}
Phone: {CLIENT["phone"]}
Email: {CLIENT["email"]}

INCIDENT SUMMARY
At approximately 18:45 IST, complainant was proceeding northbound on 80 Feet Road when a
commercial truck (KA-01-HD-8892) failed to yield at the signal and struck the front-left
quarter panel of the Honda City ({VEHICLE}).

WITNESSES
1. Priya Nair — +91-9845012345
2. Auto driver Ravi — present at scene

INJURIES
Complainant reported neck stiffness and left shoulder pain. Ambulance declined; complainant
visited Manipal Hospital outpatient the following day.

OFFICER FINDINGS
Primary contributing factor: failure to obey traffic signal by truck driver.
Recommend insurance claim filing with FIR reference BLR-TRAFFIC-2026-03412.

Signed: SI Ramesh Kumar
Koramangala Traffic Police Station
"""


def _insurance_claim() -> str:
    return f"""
MOTOR VEHICLE INSURANCE CLAIM FORM
Policy No: HDFC-ERGO-MV-2024-77821
Insured: {CLIENT["name"]}
Contact: {CLIENT["phone"]} / {CLIENT["email"]}

VEHICLE
Make/Model: Honda City
Registration: KA-03-AB-4521
Coverage: Comprehensive — deductible INR 5,000

LOSS DETAILS
Date of loss: {INCIDENT_DATE}
Location: {LOCATION}
Nature of loss: Collision — third-party truck at signalised intersection
Police report: BLR-TRAFFIC-2026-03412

ESTIMATED DAMAGES
Front bumper, left headlamp, fender, alignment — approx INR 1,85,000

MEDICAL
Outpatient treatment — neck/shoulder strain — bills attached separately.

DECLARATION
I declare the above information is true. I authorise LexFlow Legal to pursue claim recovery.

Signature: {CLIENT["name"]}
Date: March 18, 2026
"""


def _medical_report() -> str:
    return f"""
MANIPAL HOSPITAL — OUTPATIENT DEPARTMENT
Patient: {CLIENT["name"]}
DOB: 14-Aug-1992
Visit Date: March 16, 2026

CHIEF COMPLAINT
Neck pain and left shoulder discomfort following motor vehicle accident on {INCIDENT_DATE}.

EXAMINATION
Cervical spine tenderness. ROM mildly restricted. No neurological deficit.
Left shoulder soft-tissue tenderness. X-ray cervical spine: no fracture.

DIAGNOSIS
Whiplash-associated disorder, cervical strain; left shoulder contusion.

TREATMENT PLAN
Analgesics 5 days, physiotherapy referral, follow-up in 2 weeks if symptoms persist.

Treating Physician: Dr. Ananya Mehta, MBBS, MD (Ortho)
Contact: records@manipalhospital.com
"""


def _driver_license() -> str:
    return f"""
KARNATAKA TRANSPORT DEPARTMENT — DRIVING LICENCE (COPY)
Licence No: KA01 20200123456
Name: {CLIENT["name"]}
Date of Birth: 14-Aug-1992
Address: HSR Layout, Bengaluru, Karnataka
Valid Until: 13-Aug-2030
Categories: LMV-NT

This copy submitted for motor insurance claim file {INCIDENT_DATE}.
Issuing RTO: Bengaluru South (KA-01)
"""


def _vehicle_photos_zip(path: Path) -> None:
    manifest = f"""
Vehicle Damage Photo Manifest — {CLIENT["name"]}
Incident: {INCIDENT_DATE}
Vehicle: {VEHICLE}

Files in this archive (placeholders for QA):
- front_damage.jpg — crushed front bumper, broken left headlamp
- left_fender.jpg — dented left fender and wheel arch
- rear_context.jpg — scene context showing intersection
- dashboard_odometer.jpg — odometer reading 42,318 km

Damage consistent with side-impact at low speed. Repair estimate requested.
"""
    notes = f"""
Photographer notes (LexFlow field intake)
Client: {CLIENT["name"]} ({CLIENT["email"]})
All photos taken March 16, 2026 at insured vehicle storage yard.
"""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("photo_manifest.txt", manifest.strip())
        archive.writestr("damage_notes.txt", notes.strip())
        archive.writestr("front_damage.jpg.txt", "Placeholder: front bumper damage photo")
        archive.writestr("left_fender.jpg.txt", "Placeholder: left fender dent photo")
    path.write_bytes(buffer.getvalue())


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    files = {
        "Police_Report.pdf": ("POLICE TRAFFIC INCIDENT REPORT", _police_report()),
        "Insurance_Claim_Form.pdf": ("INSURANCE CLAIM FORM", _insurance_claim()),
        "Medical_Report.pdf": ("MEDICAL REPORT", _medical_report()),
        "Driver_License.pdf": ("DRIVING LICENCE COPY", _driver_license()),
    }
    for filename, (title, body) in files.items():
        target = OUT_DIR / filename
        _write_pdf(target, title, body)
        print(f"OK  {target}")

    zip_path = OUT_DIR / "Vehicle_Photos.zip"
    _vehicle_photos_zip(zip_path)
    print(f"OK  {zip_path}")


if __name__ == "__main__":
    main()
