"""
HealthTech PHI/PII Redaction Pipeline
Service — Entity Merger & Deduplicator

Combines entity lists from multiple detection sources (Presidio, spaCy, Regex)
into a single deduplicated, position-sorted list.

Algorithm
---------
1.  Collect all entities from all sources into one pool.
2.  Sort by start position.
3.  For overlapping spans, keep the entity with the highest confidence.
    Tie-break by source priority: Presidio > spaCy > Regex.
4.  Track which sources contributed to the final merged set.

Usage
-----
>>> from app.services.entity_merger import EntityMerger
>>> merged = EntityMerger.merge(presidio_entities, spacy_entities, regex_entities)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from app.services.presidio_service import AIEntityResult

logger = logging.getLogger(__name__)

# Source priority (lower number = higher priority when resolving ties)
_SOURCE_PRIORITY: dict[str, int] = {
    "Presidio": 0,
    "spaCy":    1,
    "Regex":    2,
}


@dataclass
class MergedEntityResult:
    """A deduplicated entity result with provenance tracking."""

    type: str
    value: str
    start: int
    end: int
    confidence: float
    source: str
    all_sources: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "type":        self.type,
            "value":       self.value,
            "start":       self.start,
            "end":         self.end,
            "confidence":  round(self.confidence, 4),
            "source":      self.source,
            "all_sources": self.all_sources,
        }


class EntityMerger:
    """Stateless utility for merging PHI/PII entity lists from multiple sources."""

    @staticmethod
    def merge(
        *entity_lists: list[AIEntityResult],
        regex_entities: list | None = None,
    ) -> list[MergedEntityResult]:
        """
        Merge entities from Presidio, spaCy, and (optionally) Regex into a
        single deduplicated list sorted by character position.

        Parameters
        ----------
        *entity_lists : list[AIEntityResult]
            Variable-length positional arguments of AI entity lists
            (e.g., presidio_entities, spacy_entities).
        regex_entities : list, optional
            Entities from the regex detector (``EntityResult`` objects).
            These are adapted to ``AIEntityResult`` internally.

        Returns
        -------
        list[MergedEntityResult]
            Deduplicated, position-sorted merged entity list.
        """
        pool: list[AIEntityResult] = []

        # Add AI entity lists
        for entity_list in entity_lists:
            pool.extend(entity_list)

        # Adapt regex entities (different dataclass shape)
        if regex_entities:
            for re_ent in regex_entities:
                pool.append(
                    AIEntityResult(
                        type=re_ent.type,
                        value=re_ent.value,
                        start=re_ent.start,
                        end=re_ent.end,
                        confidence=re_ent.confidence,
                        source="Regex",
                    )
                )

        if not pool:
            return []

        # Sort by start position; resolve ties by descending confidence,
        # then by source priority.
        pool.sort(
            key=lambda e: (
                e.start,
                -e.confidence,
                _SOURCE_PRIORITY.get(e.source, 99),
            )
        )

        # Deduplicate overlapping spans
        kept: list[MergedEntityResult] = []
        for entity in pool:
            winner = EntityMerger._try_insert(entity, kept)
            if winner is not None:
                kept = winner

        # Final sort by position
        kept.sort(key=lambda e: e.start)

        logger.debug(
            "Entity merger: %d raw → %d merged (from %d sources)",
            len(pool),
            len(kept),
            len({e.source for e in pool}),
        )

        return kept

    @staticmethod
    def _overlaps(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
        """Return True if two spans overlap (not just touch)."""
        return a_start < b_end and b_start < a_end

    @staticmethod
    def _try_insert(
        candidate: AIEntityResult,
        kept: list[MergedEntityResult],
    ) -> list[MergedEntityResult] | None:
        """
        Attempt to insert *candidate* into *kept*.

        - If no overlap: append and return new list.
        - If overlap with lower-confidence existing: replace, add source tag.
        - If overlap with higher-confidence existing: merge sources, discard candidate.

        Returns the updated kept list, or None if candidate was discarded.
        """
        new_kept: list[MergedEntityResult] = []
        inserted = False
        candidate_wins = True

        for existing in kept:
            if not EntityMerger._overlaps(
                candidate.start, candidate.end,
                existing.start, existing.end,
            ):
                new_kept.append(existing)
                continue

            # Overlapping span — decide winner
            cand_priority = _SOURCE_PRIORITY.get(candidate.source, 99)
            exist_priority = _SOURCE_PRIORITY.get(existing.source, 99)

            cand_wins = (
                candidate.confidence > existing.confidence
                or (
                    candidate.confidence == existing.confidence
                    and cand_priority < exist_priority
                )
                or (
                    candidate.confidence == existing.confidence
                    and cand_priority == exist_priority
                    and (candidate.end - candidate.start)
                    > (existing.end - existing.start)
                )
            )

            if cand_wins:
                # Replace existing with candidate (merge sources)
                merged_sources = list(
                    dict.fromkeys(
                        [candidate.source] + existing.all_sources + [existing.source]
                    )
                )
                new_entry = MergedEntityResult(
                    type=candidate.type,
                    value=candidate.value,
                    start=candidate.start,
                    end=candidate.end,
                    confidence=candidate.confidence,
                    source=candidate.source,
                    all_sources=merged_sources,
                )
                new_kept.append(new_entry)
                inserted = True
            else:
                # Existing wins — absorb candidate's source into existing
                if candidate.source not in existing.all_sources:
                    existing.all_sources.append(candidate.source)
                new_kept.append(existing)
                candidate_wins = False

        if not inserted and candidate_wins:
            new_kept.append(
                MergedEntityResult(
                    type=candidate.type,
                    value=candidate.value,
                    start=candidate.start,
                    end=candidate.end,
                    confidence=candidate.confidence,
                    source=candidate.source,
                    all_sources=[candidate.source],
                )
            )

        return new_kept

    @staticmethod
    def count_duplicates(
        *entity_lists: list[AIEntityResult],
        regex_entities: list | None = None,
    ) -> int:
        """
        Return the number of entities removed during merging (duplicate count).
        """
        total_raw = sum(len(lst) for lst in entity_lists)
        if regex_entities:
            total_raw += len(regex_entities)
        merged = EntityMerger.merge(*entity_lists, regex_entities=regex_entities)
        return max(0, total_raw - len(merged))
