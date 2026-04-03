"""Lead export for advisor teams.

Exports T1 + T2 leads as CSV so advisors can work them manually
(call, email, LinkedIn) using their own tools and judgment.
"""

from __future__ import annotations

import csv
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from src.models import ScoredLead
from src.settings import settings

logger = logging.getLogger(__name__)


class LeadExporter:
    """Exports scored leads to CSV and JSON for advisor teams."""

    def __init__(self, output_dir: str | None = None):
        self.output_dir = Path(output_dir or settings.export_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_csv(self, leads: list[ScoredLead], run_id: str) -> Path:
        """Export leads to CSV — the format advisors actually want."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
        filepath = self.output_dir / f"leads-{timestamp}-{run_id[:8]}.csv"

        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Tier",
                "Score",
                "Person",
                "Company",
                "Event Type",
                "Situation Brief",
                "Talking Points",
                "Filing Date",
                "SEC Filing URL",
                "Outreach Status",
            ])

            for lead in sorted(leads, key=lambda l: l.score, reverse=True):
                writer.writerow([
                    lead.tier.value,
                    lead.score,
                    lead.event.person_name,
                    lead.event.company_name,
                    lead.event.event_type.value,
                    lead.situation_brief,
                    " | ".join(lead.talking_points),
                    lead.event.filed_at.strftime("%Y-%m-%d") if lead.event.filed_at else "",
                    lead.event.url,
                    lead.outreach_status.value,
                ])

        logger.info(f"Exported {len(leads)} leads to {filepath}")
        return filepath

    def export_json(self, leads: list[ScoredLead], run_id: str) -> Path:
        """Export leads to JSON — for n8n or other automation tools."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
        filepath = self.output_dir / f"leads-{timestamp}-{run_id[:8]}.json"

        data = []
        for lead in sorted(leads, key=lambda l: l.score, reverse=True):
            data.append({
                "tier": lead.tier.value,
                "score": lead.score,
                "person_name": lead.event.person_name,
                "company_name": lead.event.company_name,
                "event_type": lead.event.event_type.value,
                "situation_brief": lead.situation_brief,
                "talking_points": lead.talking_points,
                "filed_at": lead.event.filed_at.isoformat() if lead.event.filed_at else None,
                "url": lead.event.url,
                "outreach_status": lead.outreach_status.value,
                "correlation_note": lead.event.raw_data.get("correlation_note", ""),
            })

        filepath.write_text(json.dumps(data, indent=2))
        logger.info(f"Exported {len(leads)} leads (JSON) to {filepath}")
        return filepath
