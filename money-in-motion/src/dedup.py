"""Deduplication with cross-detector entity resolution.

Scenario fix #5: uses Supabase to check across runs (not just in-memory).
Scenario fix #14: detects filing amendments and links to originals.
Scenario fix #19: correlates events across detectors for the same person/company.
"""

from __future__ import annotations

import logging
import re

from src.models import Event

logger = logging.getLogger(__name__)


class Deduplicator:
    """Deduplicates events using source IDs and entity resolution."""

    def __init__(self, known_source_ids: set[str] | None = None):
        self.known_source_ids = known_source_ids or set()
        self._entity_map: dict[str, list[Event]] = {}  # normalized_key → events

    def deduplicate(self, events: list[Event]) -> list[Event]:
        """Filter out already-seen events and correlate cross-detector matches.

        Returns only new events, with cross-detector correlations noted in raw_data.
        """
        new_events = []

        for event in events:
            # Check against known source IDs (from Supabase)
            if event.dedup_key in self.known_source_ids:
                logger.debug(f"Skipping duplicate: {event.dedup_key}")
                continue

            # Check for amendments (scenario fix #14)
            if self._is_amendment(event):
                original = self._find_original(event, events + new_events)
                if original:
                    event.raw_data["amends"] = original.source_id
                    event.raw_data["is_amendment"] = True
                    logger.info(
                        f"Amendment detected: {event.source_id} amends {original.source_id}"
                    )

            # Track for in-run dedup
            self.known_source_ids.add(event.dedup_key)
            new_events.append(event)

            # Build entity map for cross-detector correlation
            entity_key = self._normalize_entity(event.person_name, event.company_name)
            if entity_key:
                self._entity_map.setdefault(entity_key, []).append(event)

        # Scenario fix #19: annotate cross-detector correlations
        self._annotate_correlations(new_events)

        return new_events

    def _is_amendment(self, event: Event) -> bool:
        """Check if this event is a filing amendment (Form 4/A, 8-K/A)."""
        source_id = event.source_id.lower()
        return "/a" in source_id or "amendment" in event.raw_data.get("form_type", "").lower()

    def _find_original(self, amendment: Event, all_events: list[Event]) -> Event | None:
        """Find the original filing that this amendment supersedes."""
        # Match by company name + person name + close filing date
        for event in all_events:
            if event.source_id == amendment.source_id:
                continue
            if (
                event.event_type == amendment.event_type
                and self._normalize_name(event.company_name) == self._normalize_name(amendment.company_name)
                and self._normalize_name(event.person_name) == self._normalize_name(amendment.person_name)
                and not event.raw_data.get("is_amendment")
            ):
                return event
        return None

    def _normalize_entity(self, person_name: str, company_name: str) -> str:
        """Create a normalized key for entity matching across detectors."""
        person = self._normalize_name(person_name)
        company = self._normalize_name(company_name)
        if not person and not company:
            return ""
        return f"{person}@{company}"

    def _normalize_name(self, name: str) -> str:
        """Normalize a name for fuzzy matching."""
        if not name:
            return ""
        # Lowercase, remove punctuation, collapse whitespace
        name = name.lower().strip()
        name = re.sub(r"[^\w\s]", "", name)
        name = re.sub(r"\s+", " ", name)
        return name

    def _annotate_correlations(self, events: list[Event]) -> None:
        """Mark events that correlate across detectors.

        Scenario fix #19: if the same person appears in both Form 4 and 8-K,
        note the correlation so the scorer gets full context.
        """
        for entity_key, entity_events in self._entity_map.items():
            if len(entity_events) <= 1:
                continue

            # Multiple events for the same entity
            event_types = {e.event_type for e in entity_events}
            if len(event_types) > 1:
                # Cross-detector match!
                correlated_ids = [e.source_id for e in entity_events]
                for event in entity_events:
                    event.raw_data["correlated_events"] = [
                        sid for sid in correlated_ids if sid != event.source_id
                    ]
                    event.raw_data["correlation_note"] = (
                        f"This person/company also appears in: "
                        f"{', '.join(et.value for et in event_types if et != event.event_type)}"
                    )
                logger.info(
                    f"Cross-detector correlation: {entity_key} appears in "
                    f"{', '.join(et.value for et in event_types)}"
                )
