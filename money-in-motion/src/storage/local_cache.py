"""Local file cache for resilience when Supabase is down.

Scenario fix #9, #17: caches scored leads locally before Supabase write,
so data isn't lost if the database is unavailable.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from src.models import ScoredLead
from src.settings import settings

logger = logging.getLogger(__name__)


class LocalCache:
    """File-based cache for scored leads and pipeline state."""

    def __init__(self, cache_dir: str | None = None):
        self.cache_dir = Path(cache_dir or settings.local_cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def cache_scored_leads(self, leads: list[ScoredLead], run_id: str) -> bool:
        """Cache scored leads to local JSON file before Supabase write."""
        if not leads:
            return True

        cache_file = self.cache_dir / f"scored_leads_{run_id}.json"
        try:
            data = []
            for lead in leads:
                data.append({
                    "lead_id": lead.lead_id,
                    "event_id": lead.event.event_id,
                    "event_type": lead.event.event_type.value,
                    "person_name": lead.event.person_name,
                    "company_name": lead.event.company_name,
                    "score": lead.score,
                    "tier": lead.tier.value,
                    "situation_brief": lead.situation_brief,
                    "talking_points": lead.talking_points,
                    "email": lead.enrichment.email,
                    "phone": lead.enrichment.phone,
                    "linkedin_url": lead.enrichment.linkedin_url,
                    "enrichment_status": lead.enrichment.status.value,
                    "scored_at": lead.scored_at.isoformat(),
                })

            cache_file.write_text(json.dumps(data, indent=2))
            logger.info(f"Cached {len(leads)} scored leads to {cache_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to cache scored leads: {e}")
            return False

    def get_pending_leads(self) -> list[dict]:
        """Retrieve cached leads that haven't been written to Supabase yet."""
        pending = []
        for cache_file in self.cache_dir.glob("scored_leads_*.json"):
            try:
                data = json.loads(cache_file.read_text())
                pending.extend(data)
            except Exception as e:
                logger.warning(f"Failed to read cache file {cache_file}: {e}")
        return pending

    def mark_synced(self, run_id: str) -> None:
        """Remove cache file after successful Supabase sync."""
        cache_file = self.cache_dir / f"scored_leads_{run_id}.json"
        if cache_file.exists():
            cache_file.unlink()
            logger.debug(f"Cleared cache for run {run_id}")
