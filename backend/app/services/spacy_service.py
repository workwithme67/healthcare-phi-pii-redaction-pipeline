"""
HealthTech PHI/PII Redaction Pipeline
Service — spaCy Named Entity Recognition

Provides direct NER-based PHI/PII detection using a spaCy pipeline.
Complements Presidio by adding NER-level entity detection for:
  PERSON, ORG → ORGANIZATION, GPE/LOC → LOCATION, DATE, HOSPITAL, COUNTRY

The same spaCy model used by Presidio is reused here (singleton) to avoid
loading the model twice.

Usage
-----
>>> from app.services.spacy_service import spacy_service
>>> entities, ms = spacy_service.analyze("Dr. Adams visited Apollo Hospital")
"""

from __future__ import annotations

import logging
import time

from app.services.presidio_service import AIEntityResult

logger = logging.getLogger(__name__)


# ── spaCy label → project entity type mapping ─────────────────────────────────

SPACY_LABEL_MAP: dict[str, str] = {
    "PERSON":   "PERSON",
    "ORG":      "ORGANIZATION",
    "GPE":      "LOCATION",       # Geo-Political Entity (cities, countries, states)
    "LOC":      "LOCATION",       # Non-GPE locations (rivers, mountains, etc.)
    "FAC":      "HOSPITAL",       # Facilities (airports, hospitals, etc.)
    "DATE":     "DATE_TIME",
    "TIME":     "DATE_TIME",
    "CARDINAL": None,             # Skip pure numbers
    "MONEY":    None,
    "NORP":     "ORGANIZATION",   # Nationalities, religious/political groups
}

# Hospital-related keywords to promote ORG → HOSPITAL
HOSPITAL_KEYWORDS: frozenset[str] = frozenset(
    {
        "hospital",
        "clinic",
        "medical center",
        "healthcare",
        "health center",
        "infirmary",
        "sanatorium",
        "dispensary",
        "nursing home",
        "polyclinic",
        "health institute",
        "apollo",
        "aiims",
        "fortis",
        "medanta",
        "narayana",
        "manipal",
        "max hospital",
        "kims",
        "lilavati",
        "wockhardt",
        "columbia asia",
        "aster",
        "care hospital",
    }
)

# Doctor title prefixes to promote PERSON → DOCTOR
DOCTOR_PREFIXES: frozenset[str] = frozenset(
    {"dr", "dr.", "doctor", "prof", "prof.", "professor", "md", "phd"}
)


# ── spaCy Service ─────────────────────────────────────────────────────────────

class SpacyService:
    """
    Singleton spaCy NER service.

    The model is loaded lazily on the first call to ``analyze()``.
    If Presidio has already loaded the model, it is reused via the
    Presidio NLP engine rather than loading a second copy.
    """

    def __init__(self) -> None:
        self._nlp = None
        self._initialized: bool = False

    # ── Initialization ────────────────────────────────────────────────────────

    def _initialize(self) -> None:
        """Load the spaCy NLP pipeline (called once, lazily)."""
        if self._initialized:
            return

        try:
            import spacy

            for model_name in ("en_core_web_lg", "en_core_web_sm"):
                if spacy.util.is_package(model_name):
                    self._nlp = spacy.load(model_name, disable=["parser", "lemmatizer"])
                    logger.info("spaCy model loaded: %s", model_name)
                    self._initialized = True
                    return

            raise RuntimeError(
                "No spaCy model found. "
                "Run: python -m spacy download en_core_web_lg"
            )

        except ImportError as exc:
            raise RuntimeError(
                "spaCy is not installed. Run: pip install spacy"
            ) from exc

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _classify_entity(label: str, span_text: str) -> str | None:
        """Map a raw spaCy label to our project entity type."""
        entity_type = SPACY_LABEL_MAP.get(label)
        if entity_type is None:
            return None

        text_lower = span_text.strip().lower()

        # Promote facility/org to HOSPITAL if it contains hospital keywords
        if entity_type in ("ORGANIZATION", "HOSPITAL"):
            if any(kw in text_lower for kw in HOSPITAL_KEYWORDS):
                return "HOSPITAL"

        return entity_type

    @staticmethod
    def _detect_doctor(span_text: str, entity_type: str) -> str:
        """Promote PERSON → DOCTOR if prefixed by a medical title."""
        if entity_type != "PERSON":
            return entity_type
        first_token = span_text.strip().lower().split()[0] if span_text.strip() else ""
        if first_token in DOCTOR_PREFIXES:
            return "DOCTOR"
        return entity_type

    # ── Public API ────────────────────────────────────────────────────────────

    def analyze(self, text: str) -> tuple[list[AIEntityResult], float]:
        """
        Run spaCy NER on *text*.

        Returns
        -------
        (entities, processing_time_ms)
        """
        self._initialize()

        if not text or not text.strip():
            return [], 0.0

        t0 = time.perf_counter()

        from app.services.custom_recognizers import is_medical_term

        doc = self._nlp(text)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        entities: list[AIEntityResult] = []
        for ent in doc.ents:
            label = ent.label_
            span_text = ent.text.strip()

            entity_type = self._classify_entity(label, span_text)
            if entity_type is None:
                continue

            # Skip medical disease names
            if entity_type == "PERSON" and is_medical_term(span_text):
                logger.debug(
                    "spaCy: suppressed false-positive PERSON: %r", span_text
                )
                continue

            # Promote PERSON → DOCTOR if preceded by Dr./Doctor etc.
            entity_type = self._detect_doctor(span_text, entity_type)

            # Check preceding context for doctor detection
            if entity_type == "PERSON" and ent.start > 0:
                prev_token = doc[ent.start - 1].text.lower().rstrip(".")
                if prev_token in {"dr", "doctor", "prof", "professor"}:
                    entity_type = "DOCTOR"

            entities.append(
                AIEntityResult(
                    type=entity_type,
                    value=span_text,
                    start=ent.start_char,
                    end=ent.end_char,
                    confidence=0.85,  # spaCy NER does not provide per-entity scores
                    source="spaCy",
                )
            )

        entities.sort(key=lambda e: e.start)

        logger.debug(
            "spaCy NER detected %d entities in %.2f ms",
            len(entities),
            elapsed_ms,
        )

        return entities, round(elapsed_ms, 3)

    def warm_up(self) -> None:
        """Force initialization of the NLP pipeline (call at startup)."""
        try:
            self._initialize()
        except RuntimeError as exc:
            logger.warning("spaCy warm-up skipped: %s", exc)


# ── Module-level singleton ────────────────────────────────────────────────────

spacy_service = SpacyService()
