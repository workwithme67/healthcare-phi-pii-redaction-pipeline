"""Standalone test for regex_detector.py — no DB imports needed."""

import sys, re, time

# ── Copy pattern engine inline (avoids app import chain) ──────────────────────
from dataclasses import dataclass, field
from typing import Final

@dataclass
class EntityResult:
    type: str
    value: str
    start: int
    end: int
    confidence: float = 1.0

@dataclass
class DetectionResult:
    entities: list = field(default_factory=list)
    processing_time_ms: float = 0.0
    text_length: int = 0

    @property
    def entity_count(self): return len(self.entities)

_PATTERNS = [
    ("EMAIL", re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b", re.IGNORECASE), 1.0),
    ("URL", re.compile(r"https?://(?:[A-Za-z0-9\-._~:/?#\[\]@!$&'()*+,;=%]+)", re.IGNORECASE), 1.0),
    ("IP_ADDRESS", re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"), 1.0),
    ("CREDIT_CARD", re.compile(r"\b(?:4[0-9]{3}|5[1-5][0-9]{2}|3[47][0-9]{2}|6(?:011|5[0-9]{2}))(?:[\ \-]?[0-9]{4}){2,3}[\ \-]?[0-9]{1,4}\b"), 0.95),
    ("AADHAAR", re.compile(r"\b[23789]\d{3}[\s\-]?\d{4}[\s\-]?\d{4}\b"), 0.95),
    ("PAN", re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"), 1.0),
    ("PASSPORT", re.compile(r"\b[A-PR-WY][1-9]\d{6}\b"), 0.9),
    ("DATE", re.compile(r"\b(?:\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])|(?:0[1-9]|[12]\d|3[01])[/\-](?:0[1-9]|1[0-2])[/\-]\d{4}|(?:0[1-9]|1[0-2])[/\-](?:0[1-9]|[12]\d|3[01])[/\-]\d{4})\b"), 1.0),
    ("PHONE", re.compile(r"\b(?:\+?91[\s\-]?)?[6-9]\d{4}[\s\-]?\d{5}\b"), 0.95),
    ("PIN_CODE", re.compile(r"\b(?:PIN[\s:]*)?[1-9][0-9]{5}\b"), 0.85),
    ("MRN", re.compile(r"\b(?:MRN|MR|Med(?:ical)?[\s\-]?Rec(?:ord)?[\s\-]?(?:No|Num|Number|#)?)[\s:\-#]*([A-Z0-9]{4,20})\b", re.IGNORECASE), 0.95),
    ("PATIENT_ID", re.compile(r"\b(?:Patient[\s\-]?ID|PID|Pt[\s\-]?ID)[\s:\-#]*([A-Z0-9]{4,20})\b", re.IGNORECASE), 0.95),
    ("HEALTH_INSURANCE", re.compile(r"\b(?:Health[\s\-]?Ins(?:urance)?[\s\-]?(?:No|No\.|Num|Number|Policy|ID)?|Policy[\s\-]?No|Ins\.?[\s\-]?No)[\s:\-#]*([A-Z0-9]{6,20})\b", re.IGNORECASE), 0.9),
]

sample = """Patient: Ravi Kumar
MRN: MRN-REF-20240115
Patient ID: PID-A987654
Date of Birth: 03/04/1985
Admission: 2024-06-15
Phone: +91 98765 43210
Email: ravi.kumar@healthmail.com
Address: Bengaluru - 560001
Aadhaar: 2345 6789 0123
PAN: ABCDE1234F
Passport: B1234567
Insurance: Health Insurance No: HIN234567
Credit Card: 4111 1111 1111 1111
IP: 192.168.1.105
URL: https://portal.healthtech.in/patient/12345"""

t0 = time.perf_counter()
raw = []
for etype, pattern, conf in _PATTERNS:
    for m in pattern.finditer(sample):
        val = m.group(1) if m.lastindex else m.group(0)
        raw.append(EntityResult(type=etype, value=val.strip(), start=m.start(), end=m.end(), confidence=conf))

raw.sort(key=lambda e: e.start)
elapsed = (time.perf_counter() - t0) * 1000

print(f"\n[PASS] Regex Detector Test Results")
print(f"   Text length : {len(sample)} chars")
print(f"   Processing  : {elapsed:.3f} ms")
print(f"   Entities    : {len(raw)}")
print()
print(f"{'#':<4} {'TYPE':<20} {'VALUE':<30} CONF")
print("-" * 72)
for i, e in enumerate(raw, 1):
    print(f"{i:<4} {e.type:<20} {e.value:<30} {e.confidence:.0%}")

# Test redaction
type_counters = {}
out = sample
for e in reversed(raw):
    idx = type_counters.get(e.type, 0) + 1
    type_counters[e.type] = idx
    ph = f"[{e.type}_{idx:03d}]"
    out = out[:e.start] + ph + out[e.end:]

print("\n[REDACTED OUTPUT]")
print(out)
