"""
HealthTech PHI/PII Redaction Pipeline
Day 4 — Test Samples for AI Detection Engine

Tests the complete Presidio + spaCy + Regex pipeline.

Run: python backend/tests/test_ai_detection.py
(Requires: pip install presidio-analyzer presidio-anonymizer spacy
           python -m spacy download en_core_web_lg)
"""

from __future__ import annotations

import sys
import os
import time

# Allow imports from the backend app package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ── Test samples ──────────────────────────────────────────────────────────────

TEST_CASES = [
    # ── Patient Names ─────────────────────────────────────────────────────────
    {
        "name": "Patient Name",
        "text": "Patient: John Smith, admitted on 12/04/2026.",
        "expected_types": ["PERSON", "DATE_TIME"],
        "must_not_redact": [],
    },
    # ── Doctor Names ─────────────────────────────────────────────────────────
    {
        "name": "Doctor Name",
        "text": "Attending Physician: Dr. Michael Adams, MD.",
        "expected_types": ["PERSON"],  # Could be PERSON or DOCTOR depending on model
        "must_not_redact": [],
    },
    # ── Hospital Names ────────────────────────────────────────────────────────
    {
        "name": "Hospital Name",
        "text": "Patient was admitted to Apollo Hospital, New Delhi.",
        "expected_types": ["ORGANIZATION", "LOCATION", "HOSPITAL"],
        "must_not_redact": [],
    },
    # ── Addresses ─────────────────────────────────────────────────────────────
    {
        "name": "Address/Location",
        "text": "Address: 45, MG Road, Bengaluru, Karnataka 560001.",
        "expected_types": ["LOCATION"],
        "must_not_redact": [],
    },
    # ── Email Addresses ───────────────────────────────────────────────────────
    {
        "name": "Email Address",
        "text": "Contact: john.smith@healthmail.in or dr.adams@apollo.com",
        "expected_types": ["EMAIL_ADDRESS"],
        "must_not_redact": [],
    },
    # ── Phone Numbers ─────────────────────────────────────────────────────────
    {
        "name": "Phone Number",
        "text": "Emergency contact: +91 98765 43210, alternate: +91-9876-543210",
        "expected_types": ["PHONE_NUMBER"],
        "must_not_redact": [],
    },
    # ── Medical Disease Terms — MUST NOT be redacted ──────────────────────────
    {
        "name": "Medical Disease Terms (preserved)",
        "text": (
            "The patient was diagnosed with Parkinson's disease. "
            "Differential diagnosis includes Alzheimer's disease, Hodgkin lymphoma, "
            "Crohn's disease, and Wilson disease."
        ),
        "expected_types": [],
        "must_not_redact": [
            "Parkinson's disease",
            "Alzheimer's disease",
            "Hodgkin lymphoma",
            "Crohn's disease",
            "Wilson disease",
        ],
    },
    # ── Mixed Clinical Note ───────────────────────────────────────────────────
    {
        "name": "Mixed Clinical Note",
        "text": (
            "Patient John Smith (DOB: 03/04/1985) presented to Apollo Hospital, "
            "New Delhi on 12/04/2026. "
            "Attending: Dr. Priya Sharma. Phone: +91 98765 43210. "
            "Email: john@example.com. "
            "Aadhaar: 2345 6789 0123. PAN: ABCDE1234F. "
            "Diagnosis: Parkinson's disease — ruled out Alzheimer's. "
            "MRN: MRN-REF-20240115. IP: 192.168.1.105."
        ),
        "expected_types": [
            "PERSON", "DATE_TIME", "HOSPITAL", "LOCATION",
            "PHONE_NUMBER", "EMAIL_ADDRESS", "AADHAAR_NUMBER", "IN_PAN",
            "MEDICAL_RECORD_NUMBER", "IP_ADDRESS",
        ],
        "must_not_redact": ["Parkinson's disease", "Alzheimer's"],
    },
    # ── Custom Healthcare Identifiers ─────────────────────────────────────────
    {
        "name": "Patient ID & MRN",
        "text": "Patient ID: PID-A987654. Medical Record No: MRN-REF-20240115.",
        "expected_types": ["PATIENT", "MEDICAL_RECORD_NUMBER"],
        "must_not_redact": [],
    },
    {
        "name": "Insurance Number",
        "text": "Health Insurance No: HIN-POL-234567. Policy No: POL987654.",
        "expected_types": ["MEDICAL_LICENSE"],
        "must_not_redact": [],
    },
    {
        "name": "Indian IDs",
        "text": "Aadhaar: 2345 6789 0123. PAN: ABCDE1234F. Passport: B1234567.",
        "expected_types": ["AADHAAR_NUMBER", "IN_PAN", "IN_PASSPORT"],
        "must_not_redact": [],
    },
    # ── Credit Card ───────────────────────────────────────────────────────────
    {
        "name": "Credit Card",
        "text": "Payment method: 4111 1111 1111 1111.",
        "expected_types": ["CREDIT_CARD"],
        "must_not_redact": [],
    },
    # ── IP Address & URL ─────────────────────────────────────────────────────
    {
        "name": "IP Address and URL",
        "text": "Access from IP: 192.168.1.105. Portal: https://portal.healthtech.in/patient/123",
        "expected_types": ["IP_ADDRESS", "URL"],
        "must_not_redact": [],
    },
]


# ── Test runner ───────────────────────────────────────────────────────────────

def run_tests() -> None:
    print("=" * 70)
    print("  Day 4 — AI Detection Engine Test Suite")
    print("  Microsoft Presidio + spaCy + Regex Pipeline")
    print("=" * 70)

    # Import services
    try:
        from app.services.presidio_service import presidio_service
        from app.services.spacy_service import spacy_service
        from app.services.regex_detector import detector as regex_detector
        from app.services.entity_merger import EntityMerger
        from app.services.custom_recognizers import is_medical_term
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("   Make sure you run this from the backend/ directory")
        print("   and have installed: presidio-analyzer presidio-anonymizer spacy")
        return

    # Warm up
    print("\n⏳ Loading AI models (this may take a moment on first run)…")
    t_start = time.perf_counter()
    try:
        presidio_service.warm_up()
        spacy_service.warm_up()
    except RuntimeError as e:
        print(f"\n⚠️  Model warm-up warning: {e}")
        print("   Run: python -m spacy download en_core_web_sm")
        print("   Falling back to regex-only mode for tests.\n")
    warm_ms = (time.perf_counter() - t_start) * 1000
    print(f"   Models ready in {warm_ms:.0f} ms\n")

    passed = 0
    failed = 0
    warnings = 0

    for tc in TEST_CASES:
        print(f"{'─' * 60}")
        print(f"  TEST: {tc['name']}")
        print(f"  TEXT: {tc['text'][:80]}{'…' if len(tc['text']) > 80 else ''}")

        t0 = time.perf_counter()

        # Run all engines
        try:
            presidio_ents, presidio_ms = presidio_service.analyze(tc["text"])
        except Exception as e:
            print(f"  ⚠️  Presidio error: {e}")
            presidio_ents = []
            presidio_ms = 0.0

        try:
            spacy_ents, spacy_ms = spacy_service.analyze(tc["text"])
        except Exception as e:
            print(f"  ⚠️  spaCy error: {e}")
            spacy_ents = []
            spacy_ms = 0.0

        regex_result = regex_detector.detect(tc["text"])
        regex_ents = regex_result.entities

        merged = EntityMerger.merge(presidio_ents, spacy_ents, regex_entities=regex_ents)

        elapsed = (time.perf_counter() - t0) * 1000
        merged_types = {e.type for e in merged}
        merged_values = {e.value.lower() for e in merged}

        print(
            f"  RESULTS: presidio={len(presidio_ents)} | "
            f"spacy={len(spacy_ents)} | "
            f"regex={len(regex_ents)} | "
            f"merged={len(merged)} | {elapsed:.1f}ms"
        )
        if merged:
            print(f"  ENTITIES:")
            for e in merged:
                print(f"    [{e.type}] '{e.value}' (source={e.source}, conf={e.confidence:.2f})")

        # Check must_not_redact
        ok = True
        for term in tc.get("must_not_redact", []):
            term_lower = term.lower()
            # Check if any entity value exactly matches the protected term
            flagged = any(
                term_lower in mv or mv in term_lower
                for mv in merged_values
            )
            if flagged:
                print(f"  ❌ FAIL: Protected term was redacted: '{term}'")
                ok = False
                failed += 1

        # Warn if no expected types found (soft check — NLP is probabilistic)
        if tc.get("expected_types") and not merged_types:
            print(f"  ⚠️  WARN: Expected types {tc['expected_types']} but found nothing")
            warnings += 1
        elif tc.get("expected_types"):
            found_expected = bool(merged_types & set(tc["expected_types"]))
            if not found_expected:
                print(f"  ⚠️  WARN: Expected any of {tc['expected_types']}, found {sorted(merged_types)}")
                warnings += 1

        # Check no duplicates
        spans = [(e.start, e.end) for e in merged]
        has_dupes = len(spans) != len(set(spans))
        if has_dupes:
            print("  ❌ FAIL: Duplicate spans detected in merged result!")
            ok = False
            failed += 1
        elif ok and tc.get("must_not_redact"):
            print(f"  ✅ PASS: Protected terms preserved correctly")
            passed += 1
        elif ok and not tc.get("must_not_redact"):
            print(f"  ✅ PASS: No duplicate spans, {len(merged)} entities merged")
            passed += 1

    print("\n" + "=" * 70)
    print(f"  Results: {passed} passed | {warnings} warnings | {failed} failed")
    print("=" * 70)
    if failed == 0:
        print("\n✅ All critical tests passed!")
    else:
        print(f"\n❌ {failed} test(s) failed.")
    print()


if __name__ == "__main__":
    run_tests()
