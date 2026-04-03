"""Lead routing based on tier assignment."""

from __future__ import annotations

import logging

from src.models import ScoredLead, Tier

logger = logging.getLogger(__name__)


class LeadRouter:
    """Routes scored leads to appropriate channels based on tier."""

    def route(self, leads: list[ScoredLead]) -> dict[Tier, list[ScoredLead]]:
        """Group leads by tier for routing."""
        routed: dict[Tier, list[ScoredLead]] = {
            Tier.T1: [],
            Tier.T2: [],
            Tier.T3: [],
        }

        for lead in leads:
            routed[lead.tier].append(lead)

        logger.info(
            f"Routed {len(leads)} leads: "
            f"T1={len(routed[Tier.T1])}, "
            f"T2={len(routed[Tier.T2])}, "
            f"T3={len(routed[Tier.T3])}"
        )

        return routed
