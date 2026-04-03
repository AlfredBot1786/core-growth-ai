"""Enrichment waterfall — tries providers in order until one succeeds.

Scenario fix #3, #21: tracks enrichment failures per-lead for re-scoring.
"""

from __future__ import annotations

import logging

from src.models import CostTracker, EnrichmentData, EnrichmentStatus

from .base import BaseEnrichmentProvider

logger = logging.getLogger(__name__)


class EnrichmentWaterfall:
    """Tries enrichment providers in order: Apollo → Prospeo → (extensible)."""

    def __init__(self, providers: list[BaseEnrichmentProvider], cost_tracker: CostTracker | None = None):
        self.providers = providers
        self.cost_tracker = cost_tracker
        self._consecutive_failures = 0
        self._total_attempts = 0
        self._total_failures = 0

    def enrich(self, person_name: str, company_name: str) -> EnrichmentData:
        """Run waterfall enrichment. Always returns an EnrichmentData (never None).

        Scenario fix #21: tracks failure rate and warns on cascade failure.
        """
        self._total_attempts += 1

        for provider in self.providers:
            # Cost tracking
            if self.cost_tracker:
                if provider.provider_name == "apollo":
                    self.cost_tracker.apollo_calls += 1
                elif provider.provider_name == "prospeo":
                    self.cost_tracker.prospeo_calls += 1

            result = provider.enrich(person_name, company_name)

            if result and result.status in (EnrichmentStatus.SUCCESS, EnrichmentStatus.PARTIAL):
                self._consecutive_failures = 0
                return result

            # If provider returned explicit failure (credits exhausted), log it
            if result and result.status == EnrichmentStatus.FAILED:
                logger.warning(f"{provider.provider_name} failed for {person_name} @ {company_name}")
                continue

        # All providers failed
        self._consecutive_failures += 1
        self._total_failures += 1

        # Scenario fix #21: warn on cascade failure pattern
        if self._consecutive_failures >= 5:
            logger.error(
                f"ENRICHMENT CASCADE FAILURE: {self._consecutive_failures} consecutive failures. "
                f"All providers may be down. Total failure rate: "
                f"{self._total_failures}/{self._total_attempts} "
                f"({self._total_failures/max(self._total_attempts, 1)*100:.0f}%)"
            )

        return EnrichmentData(status=EnrichmentStatus.FAILED)

    @property
    def failure_rate(self) -> float:
        if self._total_attempts == 0:
            return 0.0
        return self._total_failures / self._total_attempts

    @property
    def is_cascade_failure(self) -> bool:
        """True if all recent enrichment attempts are failing."""
        return self._consecutive_failures >= 5
