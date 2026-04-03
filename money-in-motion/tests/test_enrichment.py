"""Tests for enrichment waterfall logic."""

import pytest
from src.enrichment.waterfall import EnrichmentWaterfall
from src.enrichment.base import BaseEnrichmentProvider
from src.models import EnrichmentData, EnrichmentStatus, CostTracker


class MockSuccessProvider(BaseEnrichmentProvider):
    provider_name = "mock_success"

    def enrich(self, person_name, company_name):
        return EnrichmentData(
            email="test@example.com",
            job_title="CEO",
            provider="mock_success",
            status=EnrichmentStatus.SUCCESS,
        )


class MockFailProvider(BaseEnrichmentProvider):
    provider_name = "mock_fail"

    def enrich(self, person_name, company_name):
        return EnrichmentData(status=EnrichmentStatus.FAILED, provider="mock_fail")


class MockNoneProvider(BaseEnrichmentProvider):
    provider_name = "mock_none"

    def enrich(self, person_name, company_name):
        return None


class TestEnrichmentWaterfall:
    def test_first_provider_succeeds(self):
        waterfall = EnrichmentWaterfall([MockSuccessProvider()])
        result = waterfall.enrich("John", "Acme")
        assert result.status == EnrichmentStatus.SUCCESS
        assert result.email == "test@example.com"

    def test_fallback_to_second_provider(self):
        waterfall = EnrichmentWaterfall([MockFailProvider(), MockSuccessProvider()])
        result = waterfall.enrich("John", "Acme")
        assert result.status == EnrichmentStatus.SUCCESS

    def test_all_providers_fail(self):
        waterfall = EnrichmentWaterfall([MockFailProvider(), MockFailProvider()])
        result = waterfall.enrich("John", "Acme")
        assert result.status == EnrichmentStatus.FAILED

    def test_cascade_failure_detection(self):
        waterfall = EnrichmentWaterfall([MockFailProvider()])
        for _ in range(5):
            waterfall.enrich("John", "Acme")
        assert waterfall.is_cascade_failure

    def test_no_cascade_with_successes(self):
        waterfall = EnrichmentWaterfall([MockSuccessProvider()])
        for _ in range(10):
            waterfall.enrich("John", "Acme")
        assert not waterfall.is_cascade_failure

    def test_failure_rate_tracking(self):
        waterfall = EnrichmentWaterfall([MockFailProvider()])
        waterfall.enrich("A", "B")
        waterfall.enrich("C", "D")
        assert waterfall.failure_rate == 1.0

    def test_cost_tracking(self):
        tracker = CostTracker()
        waterfall = EnrichmentWaterfall([MockSuccessProvider()], cost_tracker=tracker)
        # MockSuccessProvider doesn't match apollo/prospeo, so no cost tracked
        waterfall.enrich("John", "Acme")
        assert tracker.apollo_calls == 0

    def test_none_provider_fallback(self):
        waterfall = EnrichmentWaterfall([MockNoneProvider(), MockSuccessProvider()])
        result = waterfall.enrich("John", "Acme")
        assert result.status == EnrichmentStatus.SUCCESS
