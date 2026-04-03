"""Supabase storage client with error handling.

Scenario fix #17: handles Supabase failures without losing scored data.
Scenario fix #24: uses anon key + RLS by default.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from supabase import create_client, Client

from src.models import Event, PipelineRun, ScoredLead
from src.settings import settings

logger = logging.getLogger(__name__)


class SupabaseStorage:
    """Supabase client for events, scored_leads, and pipeline_runs."""

    def __init__(self):
        if not settings.supabase_url or not settings.supabase_key:
            logger.warning("Supabase not configured — storage disabled")
            self.client = None
            return

        self.client: Client = create_client(settings.supabase_url, settings.supabase_key)

    @property
    def is_available(self) -> bool:
        return self.client is not None

    def get_known_source_ids(self) -> set[str]:
        """Fetch all existing source IDs for deduplication."""
        if not self.is_available:
            return set()

        try:
            result = self.client.table("events").select("source_id, event_type").execute()
            return {f"{row['event_type']}:{row['source_id']}" for row in result.data}
        except Exception as e:
            logger.error(f"Failed to fetch known source IDs: {e}")
            return set()

    def insert_events(self, events: list[Event]) -> int:
        """Insert events into Supabase. Returns count of successfully inserted."""
        if not self.is_available or not events:
            return 0

        inserted = 0
        for event in events:
            try:
                self.client.table("events").insert({
                    "event_id": event.event_id,
                    "event_type": event.event_type.value,
                    "source_id": event.source_id,
                    "person_name": event.person_name,
                    "company_name": event.company_name,
                    "filed_at": event.filed_at.isoformat() if event.filed_at else None,
                    "detected_at": event.detected_at.isoformat(),
                    "url": event.url,
                    "raw_data": event.raw_data,
                }).execute()
                inserted += 1
            except Exception as e:
                logger.warning(f"Failed to insert event {event.event_id}: {e}")
                continue

        return inserted

    def insert_scored_leads(self, leads: list[ScoredLead]) -> int:
        """Insert scored leads. Returns count successfully inserted."""
        if not self.is_available or not leads:
            return 0

        inserted = 0
        for lead in leads:
            try:
                self.client.table("scored_leads").insert({
                    "lead_id": lead.lead_id,
                    "event_id": lead.event.event_id,
                    "score": lead.score,
                    "tier": lead.tier.value,
                    "situation_brief": lead.situation_brief,
                    "talking_points": lead.talking_points,
                    "email": lead.enrichment.email,
                    "phone": lead.enrichment.phone,
                    "linkedin_url": lead.enrichment.linkedin_url,
                    "job_title": lead.enrichment.job_title,
                    "enrichment_status": lead.enrichment.status.value,
                    "enrichment_provider": lead.enrichment.provider,
                    "outreach_status": lead.outreach_status.value,
                    "scored_at": lead.scored_at.isoformat(),
                }).execute()
                inserted += 1
            except Exception as e:
                logger.warning(f"Failed to insert scored lead {lead.lead_id}: {e}")
                continue

        return inserted

    def insert_pipeline_run(self, run: PipelineRun) -> bool:
        """Insert or update a pipeline run record."""
        if not self.is_available:
            return False

        try:
            self.client.table("pipeline_runs").upsert({
                "run_id": run.run_id,
                "started_at": run.started_at.isoformat(),
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                "status": run.status,
                "events_detected": run.events_detected,
                "events_new": run.events_new,
                "t1_count": run.t1_count,
                "t2_count": run.t2_count,
                "t3_count": run.t3_count,
                "alerts_sent": run.alerts_sent,
                "errors": run.errors,
                "enrichment_failures": run.enrichment_failures,
                "scoring_failures": run.scoring_failures,
                "api_cost_estimate": run.api_cost_estimate,
            }).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to save pipeline run {run.run_id}: {e}")
            return False
