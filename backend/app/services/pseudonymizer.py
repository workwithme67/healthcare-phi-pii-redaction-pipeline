"""
Pseudonymizer Service
======================
Replaces detected PHI/PII with deterministic, session-scoped tokens and
stores the forward + reverse mapping in Redis.

Token format: <ENTITY_TYPE>_<ZERO_PADDED_COUNTER>
Example: PATIENT_001, EMAIL_002, HOSPITAL_001

Security guarantees
-------------------
- Mappings are keyed by a UUID session ID; different sessions never share
  tokens even if the same PHI value appears.
- Redis TTL defaults to 1 hour (REDIS_SESSION_TTL). After expiry, data
  is permanently lost from the cache.
- Mapping values are JSON-serialised and stored at:
    phi:session:<session_id>:forward  →  { "John Smith": "PATIENT_001", … }
    phi:session:<session_id>:reverse  →  { "PATIENT_001": "John Smith", … }
- If Redis is unavailable the service falls back to an in-memory dict so
  the pipeline still works in development without Redis.
"""

from __future__ import annotations

import json
import logging
import uuid
from collections import defaultdict
from typing import Dict, Optional, Tuple

from app.services.phi_detector import DetectionResult, PHIEntity

logger = logging.getLogger("soar.pseudonymizer")

# Entity-type abbreviation for cleaner tokens
_TYPE_ABBREV: Dict[str, str] = {
    "PATIENT_NAME": "PATIENT",
    "DOCTOR_NAME":  "DOCTOR",
    "EMAIL":        "EMAIL",
    "PHONE":        "PHONE",
    "ADDRESS":      "ADDRESS",
    "HOSPITAL":     "HOSPITAL",
    "DOB":          "DOB",
    "SSN":          "SSN",
    "MRN":          "MRN",
    "DATE":         "DATE",
}


def _get_redis():
    """Return a Redis client or None if Redis is not available."""
    try:
        import redis  # type: ignore
        from app.config import settings
        client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        client.ping()
        return client
    except Exception:  # noqa: BLE001
        logger.warning(
            "Redis not available – falling back to in-memory session store. "
            "PHI mappings will NOT persist across processes."
        )
        return None


class PseudonymizationResult:
    """
    Holds the pseudonymized text plus the session ID needed to restore it.
    """

    __slots__ = ("session_id", "pseudonymized_text", "entity_count", "mapping_ttl")

    def __init__(
        self,
        session_id: str,
        pseudonymized_text: str,
        entity_count: int,
        mapping_ttl: int,
    ) -> None:
        self.session_id = session_id
        self.pseudonymized_text = pseudonymized_text
        self.entity_count = entity_count
        self.mapping_ttl = mapping_ttl


class RestorationResult:
    """Holds the restored text (PHI re-inserted)."""

    __slots__ = ("restored_text", "restored_count")

    def __init__(self, restored_text: str, restored_count: int) -> None:
        self.restored_text = restored_text
        self.restored_count = restored_count


class Pseudonymizer:
    """
    Stateless service that pseudonymizes and restores PHI/PII.

    Uses Redis for session-scoped mapping persistence. Falls back to
    in-memory storage when Redis is unavailable.
    """

    # In-memory fallback store  {session_id: {"forward": {}, "reverse": {}}}
    _mem_store: Dict[str, Dict[str, Dict[str, str]]] = {}

    # ── Public API ────────────────────────────────────────────────────────────

    def pseudonymize(
        self,
        detection_result: DetectionResult,
        session_id: Optional[str] = None,
    ) -> PseudonymizationResult:
        """
        Replace all detected PHI entities with pseudonymous tokens.

        Parameters
        ----------
        detection_result:
            Output from ``phi_detector.detect()``.
        session_id:
            Optional existing session ID. A new UUID is generated when omitted.

        Returns
        -------
        PseudonymizationResult
            Pseudonymized text and the session ID used for later restoration.
        """
        from app.config import settings  # lazy import avoids circular deps

        if session_id is None:
            session_id = str(uuid.uuid4())

        # Load or create per-session counters and maps
        forward_map, reverse_map = self._load_maps(session_id)

        # Per-type counters seeded from existing map size
        type_counters: Dict[str, int] = defaultdict(int)
        for token in reverse_map:
            parts = token.rsplit("_", 1)
            if len(parts) == 2 and parts[1].isdigit():
                abbrev = parts[0]
                type_counters[abbrev] = max(
                    type_counters[abbrev], int(parts[1])
                )

        text = detection_result.original_text
        # Process entities in reverse order so offsets remain valid
        entities_reversed = sorted(
            detection_result.entities, key=lambda e: e.start, reverse=True
        )

        for entity in entities_reversed:
            phi_value = entity.value
            abbrev = _TYPE_ABBREV.get(entity.entity_type, entity.entity_type)

            if phi_value in forward_map:
                token = forward_map[phi_value]
            else:
                type_counters[abbrev] += 1
                token = f"{abbrev}_{type_counters[abbrev]:03d}"
                forward_map[phi_value] = token
                reverse_map[token] = phi_value

            text = text[: entity.start] + token + text[entity.end :]

        # Persist updated maps
        self._save_maps(session_id, forward_map, reverse_map, settings.REDIS_SESSION_TTL)

        return PseudonymizationResult(
            session_id=session_id,
            pseudonymized_text=text,
            entity_count=len(detection_result.entities),
            mapping_ttl=settings.REDIS_SESSION_TTL,
        )

    def restore(
        self,
        session_id: str,
        pseudonymized_text: str,
    ) -> RestorationResult:
        """
        Replace pseudonymous tokens with their original PHI values.

        Parameters
        ----------
        session_id:
            The session ID returned during pseudonymization.
        pseudonymized_text:
            Text containing ``PATIENT_001``-style tokens.

        Returns
        -------
        RestorationResult
            Text with PHI restored and count of substitutions made.
        """
        _, reverse_map = self._load_maps(session_id)

        if not reverse_map:
            logger.warning(
                "No reverse map found for session_id=%s. "
                "Response returned without PHI restoration.",
                session_id,
            )
            return RestorationResult(
                restored_text=pseudonymized_text, restored_count=0
            )

        restored_text = pseudonymized_text
        count = 0
        # Sort by token length descending to avoid partial replacements
        for token, original in sorted(
            reverse_map.items(), key=lambda kv: len(kv[0]), reverse=True
        ):
            if token in restored_text:
                restored_text = restored_text.replace(token, original)
                count += 1

        return RestorationResult(restored_text=restored_text, restored_count=count)

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _load_maps(
        self, session_id: str
    ) -> Tuple[Dict[str, str], Dict[str, str]]:
        """Load forward and reverse maps from Redis or memory fallback."""
        redis_client = _get_redis()
        if redis_client is not None:
            fwd_key = f"phi:session:{session_id}:forward"
            rev_key = f"phi:session:{session_id}:reverse"
            fwd_raw = redis_client.get(fwd_key)
            rev_raw = redis_client.get(rev_key)
            forward_map: Dict[str, str] = json.loads(fwd_raw) if fwd_raw else {}
            reverse_map: Dict[str, str] = json.loads(rev_raw) if rev_raw else {}
        else:
            session_data = self._mem_store.get(session_id, {})
            forward_map = session_data.get("forward", {})
            reverse_map = session_data.get("reverse", {})

        return forward_map, reverse_map

    def _save_maps(
        self,
        session_id: str,
        forward_map: Dict[str, str],
        reverse_map: Dict[str, str],
        ttl: int,
    ) -> None:
        """Persist forward and reverse maps to Redis or memory fallback."""
        redis_client = _get_redis()
        if redis_client is not None:
            fwd_key = f"phi:session:{session_id}:forward"
            rev_key = f"phi:session:{session_id}:reverse"
            redis_client.setex(fwd_key, ttl, json.dumps(forward_map))
            redis_client.setex(rev_key, ttl, json.dumps(reverse_map))
        else:
            self._mem_store[session_id] = {
                "forward": forward_map,
                "reverse": reverse_map,
            }


# Module-level singleton
pseudonymizer = Pseudonymizer()
