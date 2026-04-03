"""Tests for deduplication and entity resolution."""

import pytest
from src.dedup import Deduplicator
from src.models import Event, EventType


class TestDeduplicator:
    def test_filters_known_ids(self):
        known = {"sec_form4:ACC-001"}
        dedup = Deduplicator(known)
        events = [
            Event(event_type=EventType.SEC_FORM4, source_id="ACC-001"),
            Event(event_type=EventType.SEC_FORM4, source_id="ACC-002"),
        ]
        result = dedup.deduplicate(events)
        assert len(result) == 1
        assert result[0].source_id == "ACC-002"

    def test_in_run_dedup(self):
        dedup = Deduplicator()
        events = [
            Event(event_type=EventType.SEC_FORM4, source_id="ACC-001"),
            Event(event_type=EventType.SEC_FORM4, source_id="ACC-001"),  # duplicate
        ]
        result = dedup.deduplicate(events)
        assert len(result) == 1

    def test_cross_detector_correlation(self):
        dedup = Deduplicator()
        events = [
            Event(
                event_type=EventType.SEC_FORM4,
                source_id="form4-001",
                person_name="John Smith",
                company_name="Acme Corp",
            ),
            Event(
                event_type=EventType.SEC_8K,
                source_id="8k-001",
                person_name="John Smith",
                company_name="Acme Corp",
            ),
        ]
        result = dedup.deduplicate(events)
        assert len(result) == 2
        # Both should have correlation notes
        assert result[0].raw_data.get("correlated_events")
        assert result[1].raw_data.get("correlated_events")

    def test_no_false_correlation(self):
        dedup = Deduplicator()
        events = [
            Event(event_type=EventType.SEC_FORM4, source_id="001", person_name="John Smith", company_name="Acme"),
            Event(event_type=EventType.SEC_8K, source_id="002", person_name="Jane Doe", company_name="BigCo"),
        ]
        result = dedup.deduplicate(events)
        assert not result[0].raw_data.get("correlated_events")
        assert not result[1].raw_data.get("correlated_events")

    def test_normalize_name(self):
        dedup = Deduplicator()
        assert dedup._normalize_name("JOHN SMITH") == "john smith"
        assert dedup._normalize_name("John  Smith") == "john smith"
        assert dedup._normalize_name("Smith, John") == "smith john"


class TestAmendmentDetection:
    def test_amendment_flag(self):
        dedup = Deduplicator()
        event = Event(event_type=EventType.SEC_FORM4, source_id="ACC-001/A")
        assert dedup._is_amendment(event)

    def test_non_amendment(self):
        dedup = Deduplicator()
        event = Event(event_type=EventType.SEC_FORM4, source_id="ACC-001")
        assert not dedup._is_amendment(event)
