"""
PHI / PII Detector Service
============================
Detects sensitive healthcare entities using pattern matching.

We intentionally use regex + rule-based detection (not a remote AI
call) so no PHI is ever externalised during the detection phase.

Detected Entity Types
---------------------
  PATIENT_NAME   – Person names
  EMAIL          – Email addresses
  PHONE          – Phone / fax numbers
  ADDRESS        – Street addresses
  HOSPITAL       – Hospital / clinic names
  DOB            – Dates of birth
  SSN            – Social Security Numbers
  MRN            – Medical Record Numbers
  DATE           – General dates (non-DOB context)
  DOCTOR_NAME    – Physician names (Dr. prefix)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class PHIEntity:
    """A single detected PHI/PII span."""
    entity_type: str   # e.g. "PATIENT_NAME", "EMAIL"
    value: str         # The exact matched text
    start: int         # Start character offset
    end: int           # End character offset
    confidence: float = 1.0


@dataclass
class DetectionResult:
    """Result of running PHI detection on a text."""
    original_text: str
    entities: List[PHIEntity] = field(default_factory=list)

    @property
    def has_phi(self) -> bool:
        return bool(self.entities)

    @property
    def entity_count(self) -> int:
        return len(self.entities)

    @property
    def entity_types(self) -> List[str]:
        return list({e.entity_type for e in self.entities})


# ---------------------------------------------------------------------------
# Compiled Regex Patterns
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
)

_PHONE_RE = re.compile(
    r"""
    (?:
        \+?1[\s.\-]?       # optional country code
    )?
    (?:
        \(\d{3}\)[\s.\-]?  # (xxx)
        | \d{3}[\s.\-]     # xxx-
    )
    \d{3}[\s.\-]\d{4}      # xxx-xxxx
    """,
    re.VERBOSE,
)

_SSN_RE = re.compile(
    r"\b\d{3}[-\s]\d{2}[-\s]\d{4}\b"
)

_MRN_RE = re.compile(
    r"\bMRN[:\s#]*\d{4,12}\b",
    re.IGNORECASE,
)

_DATE_RE = re.compile(
    r"""
    \b(?:
        \d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}   # 01/01/2024
        | (?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|
              Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|
              Nov(?:ember)?|Dec(?:ember)?)
          \s+\d{1,2},?\s+\d{4}                   # January 1, 2024
        | \d{4}-\d{2}-\d{2}                       # 2024-01-01 (ISO)
    )\b
    """,
    re.VERBOSE | re.IGNORECASE,
)

_DOB_RE = re.compile(
    r"""
    (?:DOB|date\s+of\s+birth|born(?:\s+on)?)
    \s*:?\s*
    (?:
        \d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}
        | \d{4}-\d{2}-\d{2}
        | (?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|
              Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|
              Nov(?:ember)?|Dec(?:ember)?)
          \s+\d{1,2},?\s+\d{4}
    )
    """,
    re.VERBOSE | re.IGNORECASE,
)

_ADDRESS_RE = re.compile(
    r"""
    \b\d{1,5}\s+
    [A-Za-z0-9\s,.'-]{5,40}
    (?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|
       Drive|Dr|Lane|Ln|Court|Ct|Way|Place|Pl|Circle|Cir)\b
    """,
    re.VERBOSE | re.IGNORECASE,
)

_HOSPITAL_RE = re.compile(
    r"""
    \b[A-Z][a-zA-Z\s'-]{2,40}
    (?:Hospital|Medical\s+Center|Clinic|Health\s+System|
       Healthcare|Infirmary|Medical\s+Group|Health\s+Center)\b
    """,
    re.VERBOSE,
)

# Names: "Dr. Firstname Lastname" or "Firstname Lastname" when preceded by
# patient-context keywords
_DOCTOR_RE = re.compile(
    r"\bDr\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\b"
)

_PATIENT_CONTEXT_RE = re.compile(
    r"""
    (?:
        patient\s+|
        client\s+|
        subject\s+|
        admitted\s+|
        referred\s+to\s+as\s+
    )
    ([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})
    """,
    re.VERBOSE | re.IGNORECASE,
)

# Fallback: Capitalised proper-noun pairs not already captured
_PROPER_NAME_RE = re.compile(
    r"\b([A-Z][a-z]{1,20})\s+([A-Z][a-z]{1,20})\b"
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class PHIDetector:
    """
    Stateless PHI/PII detector.

    Uses compiled regex patterns to identify sensitive spans in text.
    Patterns are checked in priority order; overlapping spans are
    de-duplicated so each character offset is claimed at most once.
    """

    def detect(self, text: str) -> DetectionResult:
        """
        Detect all PHI/PII entities in *text*.

        Parameters
        ----------
        text:
            Raw clinical note or free-form text.

        Returns
        -------
        DetectionResult
            Container with the original text and a list of PHIEntity objects
            sorted by start offset.
        """
        entities: List[PHIEntity] = []
        occupied: set[int] = set()   # character indices already claimed

        def _add(entity_type: str, m: re.Match, confidence: float = 1.0) -> None:
            start, end = m.start(), m.end()
            if any(i in occupied for i in range(start, end)):
                return  # skip overlapping spans
            occupied.update(range(start, end))
            entities.append(
                PHIEntity(
                    entity_type=entity_type,
                    value=m.group().strip(),
                    start=start,
                    end=end,
                    confidence=confidence,
                )
            )

        # Priority 1 – DOB (before generic DATE)
        for m in _DOB_RE.finditer(text):
            _add("DOB", m)

        # Priority 2 – SSN
        for m in _SSN_RE.finditer(text):
            _add("SSN", m)

        # Priority 3 – MRN
        for m in _MRN_RE.finditer(text):
            _add("MRN", m)

        # Priority 4 – Email
        for m in _EMAIL_RE.finditer(text):
            _add("EMAIL", m)

        # Priority 5 – Phone
        for m in _PHONE_RE.finditer(text):
            v = m.group().strip()
            if len(re.sub(r"\D", "", v)) >= 10:
                _add("PHONE", m)

        # Priority 6 – Hospital names
        for m in _HOSPITAL_RE.finditer(text):
            _add("HOSPITAL", m, confidence=0.9)

        # Priority 7 – Doctor names
        for m in _DOCTOR_RE.finditer(text):
            _add("DOCTOR_NAME", m)

        # Priority 8 – Patient names (contextual)
        for m in _PATIENT_CONTEXT_RE.finditer(text):
            # The captured group (1) is the name
            name_start = m.start(1)
            name_end = m.end(1)
            if any(i in occupied for i in range(name_start, name_end)):
                continue
            occupied.update(range(name_start, name_end))
            entities.append(
                PHIEntity(
                    entity_type="PATIENT_NAME",
                    value=m.group(1),
                    start=name_start,
                    end=name_end,
                    confidence=0.95,
                )
            )

        # Priority 9 – Address
        for m in _ADDRESS_RE.finditer(text):
            _add("ADDRESS", m, confidence=0.85)

        # Priority 10 – General dates
        for m in _DATE_RE.finditer(text):
            _add("DATE", m, confidence=0.8)

        # Priority 11 – Proper name pairs (low-confidence fallback)
        common_non_names = {
            "Clinical Note", "Medical Record", "Health Center", "Blood Pressure",
            "Heart Rate", "Body Temperature", "Blood Type", "Physical Therapy",
        }
        for m in _PROPER_NAME_RE.finditer(text):
            full = m.group()
            if full in common_non_names:
                continue
            _add("PATIENT_NAME", m, confidence=0.6)

        entities.sort(key=lambda e: e.start)
        return DetectionResult(original_text=text, entities=entities)


# Module-level singleton
phi_detector = PHIDetector()
