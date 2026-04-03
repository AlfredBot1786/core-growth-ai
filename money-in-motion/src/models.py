"""Core data models for the Money in Motion pipeline."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class EventType(str, Enum):
    SEC_FORM4 = "sec_form4"
    SEC_8K = "sec_8k"
    WARN_ACT = "warn_act"
    LINKEDIN = "linkedin"


class Tier(str, Enum):
    T1 = "T1"  # Score 70+, immediate alert
    T2 = "T2"  # Score 40-69, email sequence
    T3 = "T3"  # Score <40, stored only


class OutreachStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    RESPONDED = "responded"
    MEETING_BOOKED = "meeting_booked"
    DECLINED = "declined"


class EnrichmentStatus(str, Enum):
    NOT_ATTEMPTED = "not_attempted"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass
class Event:
    """A detected money-in-motion event from any source."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.SEC_FORM4
    source_id: str = ""  # accession number, Apify run ID, etc.
    person_name: str = ""
    company_name: str = ""
    filed_at: datetime | None = None
    detected_at: datetime = field(default_factory=datetime.utcnow)
    url: str = ""
    raw_data: dict[str, Any] = field(default_factory=dict)

    @property
    def dedup_key(self) -> str:
        """Unique key for deduplication across runs."""
        return f"{self.event_type.value}:{self.source_id}"


@dataclass
class EnrichmentData:
    """Contact enrichment data from Apollo/Prospeo."""

    email: str = ""
    phone: str = ""
    linkedin_url: str = ""
    job_title: str = ""
    company_size: str = ""
    location: str = ""
    provider: str = ""  # which provider returned this data
    status: EnrichmentStatus = EnrichmentStatus.NOT_ATTEMPTED


@dataclass
class ScoredLead:
    """A scored and enriched lead ready for routing."""

    lead_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event: Event = field(default_factory=Event)
    enrichment: EnrichmentData = field(default_factory=EnrichmentData)
    score: int = 0
    tier: Tier = Tier.T3
    situation_brief: str = ""
    talking_points: list[str] = field(default_factory=list)
    outreach_status: OutreachStatus = OutreachStatus.PENDING
    scored_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def assign_tier(cls, score: int) -> Tier:
        if score >= 70:
            return Tier.T1
        elif score >= 40:
            return Tier.T2
        return Tier.T3


@dataclass
class PipelineRun:
    """Record of a single pipeline execution."""

    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    status: str = "running"
    events_detected: int = 0
    events_new: int = 0
    t1_count: int = 0
    t2_count: int = 0
    t3_count: int = 0
    alerts_sent: int = 0
    errors: list[str] = field(default_factory=list)
    enrichment_failures: int = 0
    scoring_failures: int = 0
    api_cost_estimate: float = 0.0


@dataclass
class CostTracker:
    """Tracks API costs within a single pipeline run."""

    claude_calls: int = 0
    claude_tokens: int = 0
    apollo_calls: int = 0
    prospeo_calls: int = 0
    smtp_sends: int = 0

    @property
    def estimated_claude_cost(self) -> float:
        # Sonnet pricing: ~$3/M input, ~$15/M output, ~800 tokens avg per call
        return self.claude_tokens * 0.000009  # rough average

    @property
    def estimated_total(self) -> float:
        return self.estimated_claude_cost

    def check_budget(self, max_claude_calls: int, max_enrichment_calls: int) -> str | None:
        """Returns error message if budget exceeded, None if OK."""
        if self.claude_calls >= max_claude_calls:
            return f"Claude call budget exceeded: {self.claude_calls}/{max_claude_calls}"
        if (self.apollo_calls + self.prospeo_calls) >= max_enrichment_calls:
            total = self.apollo_calls + self.prospeo_calls
            return f"Enrichment call budget exceeded: {total}/{max_enrichment_calls}"
        return None
