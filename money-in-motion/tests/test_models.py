"""Tests for core data models."""

import pytest
from src.models import Event, EventType, ScoredLead, Tier, CostTracker, EnrichmentData, EnrichmentStatus


class TestEvent:
    def test_dedup_key(self):
        event = Event(event_type=EventType.SEC_FORM4, source_id="0001234567-26-000042")
        assert event.dedup_key == "sec_form4:0001234567-26-000042"

    def test_dedup_key_8k(self):
        event = Event(event_type=EventType.SEC_8K, source_id="8k-5.02-0001234567-26-000042")
        assert event.dedup_key == "sec_8k:8k-5.02-0001234567-26-000042"

    def test_default_values(self):
        event = Event()
        assert event.event_type == EventType.SEC_FORM4
        assert event.person_name == ""
        assert event.raw_data == {}
        assert event.event_id  # should be auto-generated


class TestScoredLead:
    def test_tier_assignment_t1(self):
        assert ScoredLead.assign_tier(70) == Tier.T1
        assert ScoredLead.assign_tier(100) == Tier.T1
        assert ScoredLead.assign_tier(85) == Tier.T1

    def test_tier_assignment_t2(self):
        assert ScoredLead.assign_tier(40) == Tier.T2
        assert ScoredLead.assign_tier(69) == Tier.T2

    def test_tier_assignment_t3(self):
        assert ScoredLead.assign_tier(0) == Tier.T3
        assert ScoredLead.assign_tier(39) == Tier.T3

    def test_boundary_values(self):
        assert ScoredLead.assign_tier(70) == Tier.T1
        assert ScoredLead.assign_tier(69) == Tier.T2
        assert ScoredLead.assign_tier(40) == Tier.T2
        assert ScoredLead.assign_tier(39) == Tier.T3


class TestCostTracker:
    def test_budget_check_ok(self):
        tracker = CostTracker(claude_calls=5)
        assert tracker.check_budget(200, 500) is None

    def test_budget_check_claude_exceeded(self):
        tracker = CostTracker(claude_calls=200)
        result = tracker.check_budget(200, 500)
        assert "Claude call budget exceeded" in result

    def test_budget_check_enrichment_exceeded(self):
        tracker = CostTracker(apollo_calls=300, prospeo_calls=200)
        result = tracker.check_budget(200, 500)
        assert "Enrichment call budget exceeded" in result

    def test_cost_estimation(self):
        tracker = CostTracker(claude_tokens=10000)
        assert tracker.estimated_claude_cost > 0
