"""
HealthTech PHI/PII Redaction Pipeline
Service — Custom Presidio Recognizers

Provides India-specific and healthcare-specific PatternRecognizer subclasses
that are registered with the Presidio AnalyzerEngine at startup.

Recognizers
-----------
AadhaarRecognizer       : 12-digit Aadhaar (groups of 4, optional separators)
PANRecognizer           : Indian PAN card (ABCDE1234F)
PassportRecognizer      : Indian passport number (letter + 7 digits)
PatientIDRecognizer     : Patient ID codes (PID-XXXXX or PATIENT_ID-XXXXX)
HospitalIDRecognizer    : Hospital ID codes (HSP-XXXXX)
InsuranceNumberRecognizer: Health insurance / policy numbers

Medical Context
---------------
MEDICAL_DISEASE_TERMS — a frozen set of disease/condition names that must
NOT be redacted as PERSON entities.  These are injected into the spaCy
and entity-merger layers as a deny-list.
"""

from __future__ import annotations

import re
from typing import Optional

from presidio_analyzer import Pattern, PatternRecognizer


# ── Medical disease allowlist (must NOT be redacted as PERSON) ────────────────

MEDICAL_DISEASE_TERMS: frozenset[str] = frozenset(
    {
        # Named-person diseases — NEVER redact these
        "parkinson",
        "parkinson's",
        "parkinson's disease",
        "alzheimer",
        "alzheimer's",
        "alzheimer's disease",
        "hodgkin",
        "hodgkin lymphoma",
        "hodgkin's lymphoma",
        "crohn",
        "crohn's",
        "crohn's disease",
        "wilson",
        "wilson disease",
        "wilson's disease",
        "huntington",
        "huntington's disease",
        "graves",
        "graves' disease",
        "cushing",
        "cushing's disease",
        "cushing's syndrome",
        "addison",
        "addison's disease",
        "paget",
        "paget's disease",
        "lou gehrig",
        "lou gehrig's disease",
        "tourette",
        "tourette syndrome",
        "asperger",
        "asperger syndrome",
        "down",
        "down syndrome",
        "marfan",
        "marfan syndrome",
        "raynaud",
        "raynaud's phenomenon",
        "sjogren",
        "sjögren",
        "sjogren's syndrome",
        "fabry",
        "fabry disease",
        "gaucher",
        "gaucher disease",
        "niemann",
        "niemann-pick",
        "behcet",
        "behçet",
        "wegener",
        "wegener's granulomatosis",
        "burkitt",
        "burkitt lymphoma",
        # Common medical abbreviations / terms that look like names
        "diabetes mellitus",
        "hypertension",
        "tuberculosis",
        "pneumonia",
        "dengue",
        "malaria",
        "typhoid",
        "covid",
        "sars",
        "hiv",
        "aids",
        "cancer",
        "leukemia",
        "lymphoma",
    }
)


def is_medical_term(text: str) -> bool:
    """Return True if *text* (case-insensitive) is a known medical disease term."""
    return text.strip().lower() in MEDICAL_DISEASE_TERMS


# ── Helper: build a PatternRecognizer ─────────────────────────────────────────

def _make_recognizer(
    name: str,
    supported_entity: str,
    patterns: list[Pattern],
    context: Optional[list[str]] = None,
    supported_language: str = "en",
) -> PatternRecognizer:
    return PatternRecognizer(
        supported_entity=supported_entity,
        name=name,
        patterns=patterns,
        context=context or [],
        supported_language=supported_language,
    )


# ── Aadhaar Number ────────────────────────────────────────────────────────────

class AadhaarRecognizer(PatternRecognizer):
    """
    Detects Indian Aadhaar numbers.

    Format: 12 digits, optionally grouped as XXXX XXXX XXXX or XXXX-XXXX-XXXX.
    First digit must be 2–9 (to avoid overlap with credit cards starting with 4/5).
    """

    PATTERNS = [
        Pattern(
            name="aadhaar_grouped",
            regex=r"\b[23789]\d{3}[\s\-]?\d{4}[\s\-]?\d{4}\b",
            score=0.95,
        ),
    ]
    CONTEXT = ["aadhaar", "aadhar", "uid", "unique identification", "uidai"]

    def __init__(self) -> None:
        super().__init__(
            supported_entity="AADHAAR_NUMBER",
            name="AadhaarRecognizer",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language="en",
        )


# ── PAN Card ──────────────────────────────────────────────────────────────────

class PANRecognizer(PatternRecognizer):
    """
    Detects Indian PAN (Permanent Account Number) cards.

    Format: 5 uppercase letters, 4 digits, 1 uppercase letter.
    Examples: ABCDE1234F, BXMPA7788Q
    """

    PATTERNS = [
        Pattern(
            name="pan_card",
            regex=r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
            score=1.0,
        ),
    ]
    CONTEXT = ["pan", "pan card", "permanent account number", "income tax", "it pan"]

    def __init__(self) -> None:
        super().__init__(
            supported_entity="IN_PAN",
            name="PANRecognizer",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language="en",
        )


# ── Passport Number ───────────────────────────────────────────────────────────

class PassportRecognizer(PatternRecognizer):
    """
    Detects Indian passport numbers.

    Format: 1 letter (A-PR-WY) followed by 7 digits.
    Examples: A1234567, J9876543
    """

    PATTERNS = [
        Pattern(
            name="in_passport",
            regex=r"\b[A-PR-WY][1-9]\d{6}\b",
            score=0.90,
        ),
    ]
    CONTEXT = [
        "passport",
        "passport number",
        "passport no",
        "travel document",
        "ppn",
    ]

    def __init__(self) -> None:
        super().__init__(
            supported_entity="IN_PASSPORT",
            name="PassportRecognizer",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language="en",
        )


# ── Patient ID ────────────────────────────────────────────────────────────────

class PatientIDRecognizer(PatternRecognizer):
    """
    Detects clinical patient identifier codes.

    Matches prefixes like PID, PATIENT_ID, PT-ID followed by alphanumeric codes.
    Examples: PID-A987654, PATIENT_ID-20240001, PT-ID:XYZ123
    """

    PATTERNS = [
        Pattern(
            name="patient_id_prefixed",
            regex=(
                r"\b(?:Patient[\s\-]?ID|PID|Pt[\s\-]?ID|PATIENT_ID)"
                r"[\s:\-#]*([A-Z0-9]{4,20})\b"
            ),
            score=0.95,
        ),
    ]
    CONTEXT = ["patient", "patient id", "pid", "patient identifier", "pt id"]

    def __init__(self) -> None:
        super().__init__(
            supported_entity="PATIENT",
            name="PatientIDRecognizer",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language="en",
        )


# ── Hospital ID ───────────────────────────────────────────────────────────────

class HospitalIDRecognizer(PatternRecognizer):
    """
    Detects hospital / facility identifier codes.

    Examples: HSP-001234, HOSP_ID-XYZ9, HID:A123456
    """

    PATTERNS = [
        Pattern(
            name="hospital_id_prefixed",
            regex=(
                r"\b(?:HSP|HOSP(?:ITAL)?(?:_ID)?|HID|Hosp[\s\-]?ID)"
                r"[\s:\-#]*([A-Z0-9]{4,20})\b"
            ),
            score=0.90,
        ),
    ]
    CONTEXT = [
        "hospital",
        "hospital id",
        "facility id",
        "hosp",
        "hid",
        "hsp",
    ]

    def __init__(self) -> None:
        super().__init__(
            supported_entity="HOSPITAL",
            name="HospitalIDRecognizer",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language="en",
        )


# ── Insurance / Policy Number ─────────────────────────────────────────────────

class InsuranceNumberRecognizer(PatternRecognizer):
    """
    Detects health insurance and policy number codes.

    Examples:
        Health Insurance No: HIN-POL-234567
        Policy No: POL987654
        Ins. No: ABC-INS-001
    """

    PATTERNS = [
        Pattern(
            name="insurance_number_prefixed",
            regex=(
                r"\b(?:Health[\s\-]?Ins(?:urance)?[\s\-]?(?:No|No\.|Num|Number|Policy|ID)?|"
                r"Policy[\s\-]?No|Ins\.?[\s\-]?No|Insurance[\s\-]?Policy)"
                r"[\s:\-#]*([A-Z0-9\-]{6,25})\b"
            ),
            score=0.90,
        ),
    ]
    CONTEXT = [
        "insurance",
        "policy",
        "health insurance",
        "ins no",
        "ins number",
        "policy number",
        "policy no",
    ]

    def __init__(self) -> None:
        super().__init__(
            supported_entity="MEDICAL_LICENSE",
            name="InsuranceNumberRecognizer",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language="en",
        )


# ── Medical Record Number (enhanced) ─────────────────────────────────────────

class MedicalRecordNumberRecognizer(PatternRecognizer):
    """
    Detects Medical Record Numbers (MRN).

    Examples:
        MRN: MRN-REF-20240115
        Medical Record No: 12345678
        MR: ABC001
    """

    PATTERNS = [
        Pattern(
            name="mrn_prefixed",
            regex=(
                r"\b(?:MRN|MR|Med(?:ical)?[\s\-]?Rec(?:ord)?[\s\-]?"
                r"(?:No|Num|Number|#)?)"
                r"[\s:\-#]*([A-Z0-9\-]{4,20})\b"
            ),
            score=0.95,
        ),
    ]
    CONTEXT = ["mrn", "medical record", "mr number", "record number"]

    def __init__(self) -> None:
        super().__init__(
            supported_entity="MEDICAL_RECORD_NUMBER",
            name="MedicalRecordNumberRecognizer",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language="en",
        )


# ── Registry: all custom recognizers ─────────────────────────────────────────

def get_all_custom_recognizers() -> list[PatternRecognizer]:
    """Return instances of all custom recognizers for registration with Presidio."""
    return [
        AadhaarRecognizer(),
        PANRecognizer(),
        PassportRecognizer(),
        PatientIDRecognizer(),
        HospitalIDRecognizer(),
        InsuranceNumberRecognizer(),
        MedicalRecordNumberRecognizer(),
    ]
