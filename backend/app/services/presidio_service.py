"""
HealthTech PHI/PII Redaction Pipeline
Service — Microsoft Presidio Detection

Wraps the Presidio AnalyzerEngine to provide AI-powered PHI/PII detection
targeting 14 healthcare entity types.  Registers all custom recognizers
(Aadhaar, PAN, Passport, PatientID, HospitalID, InsuranceNumber, MRN)
on top of the built-in Presidio recognizers.

Usage
-----
>>> from app.services.presidio_service import presidio_service
>>> entities = presidio_service.analyze("Patient John Smith at Apollo Hospital")
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


# ── Entity result shared with regex_detector ─────────────────────────────────

@dataclass
class AIEntityResult:
    """A single detected PHI/PII entity from the AI pipeline."""

    type: str
    value: str
    start: int
    end: int
    confidence: float
    source: str = "Presidio"

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "value": self.value,
            "start": self.start,
            "end": self.end,
            "confidence": round(self.confidence, 4),
            "source": self.source,
        }


# ── Entity types that Presidio must target ────────────────────────────────────

PRESIDIO_ENTITIES: list[str] = [
    "PERSON",
    "ORGANIZATION",
    "LOCATION",
    "DATE_TIME",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "CREDIT_CARD",
    "IP_ADDRESS",
    "URL",
    "MEDICAL_LICENSE",       # reused for insurance numbers
    "MEDICAL_RECORD_NUMBER", # MRN via custom recognizer
    "HOSPITAL",              # via custom recognizer
    "PATIENT",               # via custom recognizer (patient IDs)
    # Custom India-specific
    "AADHAAR_NUMBER",
    "IN_PAN",
    "IN_PASSPORT",
]


# ── Presidio Service ──────────────────────────────────────────────────────────

class PresidioService:
    """
    Singleton service wrapping Microsoft Presidio AnalyzerEngine.

    Initialization is lazy — the heavy spaCy model and Presidio registry
    are loaded on the first call to ``analyze()``.
    """

    def __init__(self) -> None:
        self._analyzer = None       # Lazy-loaded
        self._anonymizer = None     # Lazy-loaded
        self._initialized: bool = False

    # ── Initialization ────────────────────────────────────────────────────────

    def _initialize(self) -> None:
        """Load Presidio engines (called once, lazily)."""
        if self._initialized:
            return

        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_analyzer.nlp_engine import NlpEngineProvider
            from presidio_anonymizer import AnonymizerEngine

            from app.services.custom_recognizers import get_all_custom_recognizers

            logger.info("Initializing Presidio AnalyzerEngine with spaCy NLP backend…")

            # ── Try lg model first, fall back to sm ──────────────────────────
            spacy_model = self._resolve_spacy_model()

            # Build NLP engine backed by spaCy
            provider = NlpEngineProvider(
                nlp_configuration={
                    "nlp_engine_name": "spacy",
                    "models": [{"lang_code": "en", "model_name": spacy_model}],
                }
            )
            nlp_engine = provider.create_engine()

            # Build analyzer with our custom recognizers
            self._analyzer = AnalyzerEngine(
                nlp_engine=nlp_engine,
                supported_languages=["en"],
            )

            # Register custom recognizers
            for recognizer in get_all_custom_recognizers():
                self._analyzer.registry.add_recognizer(recognizer)
                logger.debug("Registered recognizer: %s", recognizer.name)

            # Anonymizer (for future redaction; not used in detect-only mode)
            self._anonymizer = AnonymizerEngine()

            self._initialized = True
            logger.info(
                "Presidio initialized successfully with model '%s'. "
                "Custom recognizers: %d",
                spacy_model,
                len(get_all_custom_recognizers()),
            )

        except ImportError as exc:
            logger.error(
                "Presidio / spaCy not installed. Run: "
                "pip install presidio-analyzer presidio-anonymizer spacy "
                "&& python -m spacy download en_core_web_lg\n"
                "Error: %s",
                exc,
            )
            raise RuntimeError(
                "Presidio libraries not found. Install them and download a spaCy model."
            ) from exc

    @staticmethod
    def _resolve_spacy_model() -> str:
        """Return the best available spaCy model name."""
        import spacy

        for model in ("en_core_web_lg", "en_core_web_sm"):
            if spacy.util.is_package(model):
                logger.info("Using spaCy model: %s", model)
                return model

        # Neither installed — attempt to download sm as last resort
        logger.warning(
            "Neither en_core_web_lg nor en_core_web_sm found. "
            "Attempting to download en_core_web_sm…"
        )
        import subprocess, sys  # noqa: E401
        subprocess.run(
            [sys.executable, "-m", "spacy", "download", "en_core_web_sm"],
            check=True,
        )
        return "en_core_web_sm"

    # ── Public API ────────────────────────────────────────────────────────────

    def analyze(
        self,
        text: str,
        entities: Optional[list[str]] = None,
        language: str = "en",
    ) -> tuple[list[AIEntityResult], float]:
        """
        Run Presidio entity detection on *text*.

        Parameters
        ----------
        text : str
            Raw clinical / freeform text.
        entities : list[str], optional
            Subset of entity types to detect.  Defaults to ``PRESIDIO_ENTITIES``.
        language : str
            Language code (default ``"en"``).

        Returns
        -------
        (entities, processing_time_ms)
        """
        self._initialize()

        if not text or not text.strip():
            return [], 0.0

        t0 = time.perf_counter()

        target_entities = entities or PRESIDIO_ENTITIES

        try:
            results = self._analyzer.analyze(
                text=text,
                entities=target_entities,
                language=language,
            )
        except Exception as exc:
            logger.error("Presidio analysis failed: %s", exc)
            return [], 0.0

        elapsed_ms = (time.perf_counter() - t0) * 1000

        from app.services.custom_recognizers import is_medical_term

        ai_entities: list[AIEntityResult] = []
        for result in results:
            span_text = text[result.start: result.end]

            # Medical disease filter: skip if the matched text is a known disease name
            if result.entity_type == "PERSON" and is_medical_term(span_text):
                logger.debug(
                    "Suppressed false-positive PERSON: %r (medical term)", span_text
                )
                continue

            ai_entities.append(
                AIEntityResult(
                    type=result.entity_type,
                    value=span_text,
                    start=result.start,
                    end=result.end,
                    confidence=round(result.score, 4),
                    source="Presidio",
                )
            )

        ai_entities.sort(key=lambda e: e.start)

        logger.debug(
            "Presidio detected %d entities in %.2f ms",
            len(ai_entities),
            elapsed_ms,
        )

        return ai_entities, round(elapsed_ms, 3)

    def warm_up(self) -> None:
        """Force initialization of the NLP engine (call at startup)."""
        try:
            self._initialize()
        except RuntimeError as exc:
            logger.warning("Presidio warm-up skipped: %s", exc)


# ── Module-level singleton ────────────────────────────────────────────────────

presidio_service = PresidioService()
