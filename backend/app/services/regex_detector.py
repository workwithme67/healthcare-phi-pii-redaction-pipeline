"""
HealthTech PHI/PII Redaction Pipeline
Service — Regex-Based PHI/PII Detector

Implements pure Python regex detection for 13 entity types.
No third-party NLP dependencies — only the stdlib `re` module.

Detected entity types
---------------------
EMAIL           : Standard email addresses
PHONE           : Indian / international phone numbers (10–13 digits)
DATE            : DD/MM/YYYY | MM/DD/YYYY | YYYY-MM-DD
AADHAAR         : 12-digit Aadhaar number (with optional spaces/hyphens)
PAN             : Indian PAN card (ABCDE1234F pattern)
PASSPORT        : Indian passport (A1234567 pattern)
CREDIT_CARD     : 13–19 digit card numbers (Luhn-shaped, with separators)
IP_ADDRESS      : IPv4 addresses
PIN_CODE        : Indian 6-digit PIN codes
URL             : HTTP / HTTPS URLs
MRN             : Medical Record Number
PATIENT_ID      : Patient ID codes
HEALTH_INSURANCE: Generic health insurance policy numbers
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Final

logger = logging.getLogger(__name__)


# ── Entity Result ─────────────────────────────────────────────────────────────

@dataclass
class EntityResult:
    """Represents a single detected PHI/PII entity."""

    type: str
    value: str
    start: int
    end: int
    confidence: float = 1.0

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "value": self.value,
            "start": self.start,
            "end": self.end,
            "confidence": self.confidence,
        }


# ── Detection Result ──────────────────────────────────────────────────────────

@dataclass
class DetectionResult:
    """Aggregated result of a detection run."""

    entities: list[EntityResult] = field(default_factory=list)
    processing_time_ms: float = 0.0
    text_length: int = 0

    @property
    def entity_count(self) -> int:
        return len(self.entities)

    @property
    def entity_types(self) -> list[str]:
        return sorted({e.type for e in self.entities})


# ── Pattern Definitions ───────────────────────────────────────────────────────

# Each tuple: (entity_type, compiled_pattern, confidence_score)
_PATTERNS: Final[list[tuple[str, re.Pattern, float]]] = [
    # ── Email ─────────────────────────────────────────────────────────────────
    (
        "EMAIL",
        re.compile(
            r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
            re.IGNORECASE,
        ),
        1.0,
    ),

    # ── URL (must come before phone/IP to avoid partial matches) ──────────────
    (
        "URL",
        re.compile(
            r"https?://(?:[A-Za-z0-9\-._~:/?#\[\]@!$&'()*+,;=%]+)",
            re.IGNORECASE,
        ),
        1.0,
    ),

    # ── IPv4 Address ──────────────────────────────────────────────────────────
    (
        "IP_ADDRESS",
        re.compile(
            r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
            r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
        ),
        1.0,
    ),

    # ── Credit Card (13–19 digits, optional space/hyphen separators) ──────────
    (
        "CREDIT_CARD",
        re.compile(
            r"\b(?:4[0-9]{3}|5[1-5][0-9]{2}|3[47][0-9]{2}|6(?:011|5[0-9]{2}))"
            r"(?:[\ \-]?[0-9]{4}){2,3}[\ \-]?[0-9]{1,4}\b"
        ),
        0.95,
    ),

    # ── Aadhaar: 12 digits (groups of 4 separated by space or hyphen) ─────────
    # Must start 2-9 but NOT 4/5/6 (avoids credit card overlap)
    (
        "AADHAAR",
        re.compile(
            r"\b[23789]\d{3}[\s\-]?\d{4}[\s\-]?\d{4}\b"
        ),
        0.95,
    ),

    # ── PAN Card: 5 letters, 4 digits, 1 letter ───────────────────────────────
    (
        "PAN",
        re.compile(
            r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"
        ),
        1.0,
    ),

    # ── Passport (Indian): 1 letter + 7 digits ────────────────────────────────
    (
        "PASSPORT",
        re.compile(
            r"\b[A-PR-WY][1-9]\d{6}\b"
        ),
        0.9,
    ),

    # ── Date: DD/MM/YYYY | MM/DD/YYYY | YYYY-MM-DD ────────────────────────────
    (
        "DATE",
        re.compile(
            r"\b(?:"
            r"\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])"  # YYYY-MM-DD
            r"|(?:0[1-9]|[12]\d|3[01])[/\-](?:0[1-9]|1[0-2])[/\-]\d{4}"  # DD/MM/YYYY
            r"|(?:0[1-9]|1[0-2])[/\-](?:0[1-9]|[12]\d|3[01])[/\-]\d{4}"  # MM/DD/YYYY
            r")\b"
        ),
        1.0,
    ),

    # ── Phone: Indian (10 digits, optional +91/0 prefix) ─────────────────────
    (
        "PHONE",
        re.compile(
            r"\b(?:\+?91[\s\-]?)?[6-9]\d{4}[\s\-]?\d{5}\b"
        ),
        0.95,
    ),

    # ── Indian PIN Code: 6 digits starting with 1–9 ──────────────────────────
    (
        "PIN_CODE",
        re.compile(
            r"\b(?:PIN[\s:]*)?[1-9][0-9]{5}\b"
        ),
        0.85,
    ),

    # ── Medical Record Number ─────────────────────────────────────────────────
    (
        "MRN",
        re.compile(
            r"\b(?:MRN|MR|Med(?:ical)?[\s\-]?Rec(?:ord)?[\s\-]?(?:No|Num|Number|#)?)"
            r"[\s:\-#]*([A-Z0-9]{4,20})\b",
            re.IGNORECASE,
        ),
        0.95,
    ),

    # ── Patient ID ────────────────────────────────────────────────────────────
    (
        "PATIENT_ID",
        re.compile(
            r"\b(?:Patient[\s\-]?ID|PID|Pt[\s\-]?ID)"
            r"[\s:\-#]*([A-Z0-9]{4,20})\b",
            re.IGNORECASE,
        ),
        0.95,
    ),

    # ── Health Insurance Number (generic) ────────────────────────────────────
    (
        "HEALTH_INSURANCE",
        re.compile(
            r"\b(?:Health[\s\-]?Ins(?:urance)?[\s\-]?(?:No|No\.|Num|Number|Policy|ID)?|"
            r"Policy[\s\-]?No|Ins\.?[\s\-]?No)"
            r"[\s:\-#]*([A-Z0-9]{6,20})\b",
            re.IGNORECASE,
        ),
        0.9,
    ),
]


# ── Helper ────────────────────────────────────────────────────────────────────

def _overlaps(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    """Return True if two character spans overlap."""
    return a_start < b_end and b_start < a_end


def _deduplicate(entities: list[EntityResult]) -> list[EntityResult]:
    """
    Remove overlapping entities, keeping the one with higher confidence.
    Entities are expected to be sorted by start position.
    """
    kept: list[EntityResult] = []
    for entity in entities:
        dominated = False
        new_kept: list[EntityResult] = []
        for existing in kept:
            if _overlaps(entity.start, entity.end, existing.start, existing.end):
                # Keep whichever has higher confidence (or longer match on tie)
                if entity.confidence > existing.confidence or (
                    entity.confidence == existing.confidence
                    and (entity.end - entity.start) > (existing.end - existing.start)
                ):
                    # entity wins — drop existing, add entity below
                    dominated = False
                else:
                    dominated = True
                    new_kept.append(existing)
            else:
                new_kept.append(existing)
        kept = new_kept
        if not dominated:
            kept.append(entity)
    # Sort again after dedup
    kept.sort(key=lambda e: e.start)
    return kept


# ── Main Detector ─────────────────────────────────────────────────────────────

class RegexDetector:
    """
    Pure-regex PHI/PII entity detector.

    Usage
    -----
    >>> detector = RegexDetector()
    >>> result = detector.detect("Call me at 9876543210 or email me at john@example.com")
    >>> result.entity_count
    2
    """

    def detect(self, text: str) -> DetectionResult:
        """
        Run all regex patterns over *text* and return deduplicated entities.

        Parameters
        ----------
        text : str
            Raw clinical / freeform text to scan.

        Returns
        -------
        DetectionResult
            Contains `entities` list and timing metadata.
        """
        if not text or not text.strip():
            return DetectionResult(text_length=len(text))

        t0 = time.perf_counter()
        raw_entities: list[EntityResult] = []

        for entity_type, pattern, confidence in _PATTERNS:
            for match in pattern.finditer(text):
                # For patterns with a capture group (MRN, Patient ID, Insurance)
                # use the group(1) value but keep full-match span for highlighting.
                value = match.group(1) if match.lastindex else match.group(0)
                raw_entities.append(
                    EntityResult(
                        type=entity_type,
                        value=value.strip(),
                        start=match.start(),
                        end=match.end(),
                        confidence=confidence,
                    )
                )

        # Sort by position, then deduplicate overlapping spans
        raw_entities.sort(key=lambda e: e.start)
        entities = _deduplicate(raw_entities)

        elapsed_ms = (time.perf_counter() - t0) * 1000
        logger.debug(
            "Regex detection completed: %d entities in %.2f ms",
            len(entities),
            elapsed_ms,
        )

        return DetectionResult(
            entities=entities,
            processing_time_ms=round(elapsed_ms, 3),
            text_length=len(text),
        )

    def redact(
        self,
        text: str,
        placeholder_template: str = "[{type}_{index:03d}]",
    ) -> tuple[str, list[EntityResult]]:
        """
        Detect entities and replace them with numbered placeholders.

        Parameters
        ----------
        text : str
            Raw text to redact.
        placeholder_template : str
            Python format string. Available keys: ``type``, ``index``.

        Returns
        -------
        (redacted_text, entities)
        """
        result = self.detect(text)
        if not result.entities:
            return text, []

        # Build redacted string by replacing spans from right to left
        # so that earlier indices remain valid.
        type_counters: dict[str, int] = {}
        # Assign placeholders first (left to right for consistent numbering)
        assignments: list[tuple[EntityResult, str]] = []
        for entity in result.entities:
            idx = type_counters.get(entity.type, 0) + 1
            type_counters[entity.type] = idx
            placeholder = placeholder_template.format(
                type=entity.type, index=idx
            )
            assignments.append((entity, placeholder))

        # Replace right-to-left to preserve offsets
        redacted = text
        for entity, placeholder in reversed(assignments):
            redacted = redacted[: entity.start] + placeholder + redacted[entity.end :]

        return redacted, result.entities


# ── Module-level singleton ────────────────────────────────────────────────────

detector = RegexDetector()
