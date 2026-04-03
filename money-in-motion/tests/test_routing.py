"""Tests for lead routing."""

import pytest
from src.routing.router import LeadRouter
from src.models import ScoredLead, Tier, Event


class TestLeadRouter:
    def test_routes_by_tier(self):
        router = LeadRouter()
        leads = [
            ScoredLead(score=85, tier=Tier.T1),
            ScoredLead(score=55, tier=Tier.T2),
            ScoredLead(score=20, tier=Tier.T3),
            ScoredLead(score=90, tier=Tier.T1),
        ]
        routed = router.route(leads)
        assert len(routed[Tier.T1]) == 2
        assert len(routed[Tier.T2]) == 1
        assert len(routed[Tier.T3]) == 1

    def test_empty_leads(self):
        router = LeadRouter()
        routed = router.route([])
        assert len(routed[Tier.T1]) == 0
        assert len(routed[Tier.T2]) == 0
        assert len(routed[Tier.T3]) == 0
