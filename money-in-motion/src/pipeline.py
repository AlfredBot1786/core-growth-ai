"""Main pipeline orchestrator — detect → dedup → score → route → alert + export.

No enrichment during pipeline runs. Contact lookup is deferred to
post-scoring for T1/T2 leads only, right before LinkedIn outreach.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from src.dedup import Deduplicator
from src.detectors import LinkedInDetector, Sec8KDetector, SecForm4Detector, WarnActDetector
from src.export import LeadExporter
from src.models import CostTracker, PipelineRun, Tier
from src.routing import EmailAlerter, LeadRouter
from src.scoring import ClaudeScorer
from src.settings import settings
from src.storage import LocalCache, SupabaseStorage

logger = logging.getLogger(__name__)


class Pipeline:
    """Orchestrates the full Money in Motion pipeline."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.cost_tracker = CostTracker()
        self.storage = SupabaseStorage()
        self.cache = LocalCache()
        self.router = LeadRouter()
        self.alerter = EmailAlerter()
        self.exporter = LeadExporter()
        self.scorer = ClaudeScorer(self.cost_tracker)

    def run(
        self,
        lookback_hours: int | None = None,
        detectors: list[str] | None = None,
    ) -> PipelineRun:
        """Execute a single pipeline run."""
        lookback = lookback_hours or settings.default_lookback_hours
        pipeline_run = PipelineRun()

        logger.info(f"Pipeline run {pipeline_run.run_id} starting (lookback={lookback}h, dry_run={self.dry_run})")

        try:
            # Step 1: Detect events
            events = self._detect(lookback, detectors)
            pipeline_run.events_detected = len(events)
            logger.info(f"Detected {len(events)} total events")

            if not events:
                pipeline_run.status = "completed"
                pipeline_run.completed_at = datetime.now(timezone.utc)
                self._save_run(pipeline_run)
                return pipeline_run

            # Step 2: Deduplicate
            known_ids = self.storage.get_known_source_ids()
            deduplicator = Deduplicator(known_ids)
            new_events = deduplicator.deduplicate(events)
            pipeline_run.events_new = len(new_events)
            logger.info(f"After dedup: {len(new_events)} new events")

            if not new_events:
                pipeline_run.status = "completed"
                pipeline_run.completed_at = datetime.now(timezone.utc)
                self._save_run(pipeline_run)
                return pipeline_run

            # Cap events per run
            if len(new_events) > settings.max_events_per_run:
                logger.warning(
                    f"Event cap: {len(new_events)} exceeds max {settings.max_events_per_run}. "
                    f"Processing first {settings.max_events_per_run}."
                )
                new_events = new_events[:settings.max_events_per_run]

            # Step 3: Dry run — just print events
            if self.dry_run:
                logger.info("DRY RUN: skipping scoring, storage, and alerts")
                for event in new_events:
                    logger.info(f"  [{event.event_type.value}] {event.person_name} @ {event.company_name}")
                pipeline_run.status = "completed (dry run)"
                pipeline_run.completed_at = datetime.now(timezone.utc)
                return pipeline_run

            # Step 4: Score with Claude
            scored_leads = self.scorer.score_batch(new_events)
            pipeline_run.scoring_failures = len(new_events) - len(scored_leads)

            # Step 5: Route
            routed = self.router.route(scored_leads)
            pipeline_run.t1_count = len(routed[Tier.T1])
            pipeline_run.t2_count = len(routed[Tier.T2])
            pipeline_run.t3_count = len(routed[Tier.T3])

            # Step 6: Cache locally before Supabase
            self.cache.cache_scored_leads(scored_leads, pipeline_run.run_id)

            # Step 7: Write to Supabase
            events_inserted = self.storage.insert_events(new_events)
            leads_inserted = self.storage.insert_scored_leads(scored_leads)

            if leads_inserted == len(scored_leads):
                self.cache.mark_synced(pipeline_run.run_id)
            else:
                pipeline_run.errors.append(
                    f"Supabase partial write: {leads_inserted}/{len(scored_leads)} leads saved"
                )

            # Step 8: Send T1 alerts
            alerts_sent = self.alerter.send_t1_alerts(routed[Tier.T1])
            pipeline_run.alerts_sent = alerts_sent

            # Step 9: Export lead list for advisor teams (T1 + T2)
            actionable = routed[Tier.T1] + routed[Tier.T2]
            if actionable:
                export_path = self.exporter.export_csv(actionable, pipeline_run.run_id)
                logger.info(f"Exported {len(actionable)} actionable leads to {export_path}")

            # Final
            pipeline_run.status = "completed"
            pipeline_run.completed_at = datetime.now(timezone.utc)
            pipeline_run.api_cost_estimate = self.cost_tracker.estimated_total

            logger.info(
                f"Pipeline complete: "
                f"{pipeline_run.events_new} new, "
                f"T1={pipeline_run.t1_count}, T2={pipeline_run.t2_count}, T3={pipeline_run.t3_count}, "
                f"alerts={pipeline_run.alerts_sent}, "
                f"cost=${pipeline_run.api_cost_estimate:.4f}"
            )

        except Exception as e:
            pipeline_run.status = "failed"
            pipeline_run.errors.append(str(e))
            pipeline_run.completed_at = datetime.now(timezone.utc)
            logger.error(f"Pipeline run failed: {e}", exc_info=True)

        self._save_run(pipeline_run)
        return pipeline_run

    def _detect(self, lookback_hours: int, detector_names: list[str] | None) -> list:
        """Run selected detectors. Per-detector error handling."""
        all_detectors = {
            "sec_form4": SecForm4Detector,
            "sec_8k": Sec8KDetector,
            "warn_act": WarnActDetector,
            "linkedin": LinkedInDetector,
        }

        if detector_names is None or "all" in detector_names:
            selected = list(all_detectors.keys())
        else:
            selected = detector_names

        events = []
        for name in selected:
            detector_cls = all_detectors.get(name)
            if not detector_cls:
                logger.warning(f"Unknown detector: {name}")
                continue

            try:
                detector = detector_cls()
                lb = lookback_hours
                if name == "warn_act" and lookback_hours < 168:
                    lb = 168
                detected = detector.detect(lookback_hours=lb)
                events.extend(detected)
            except Exception as e:
                logger.error(f"Detector {name} failed: {e}")
                continue

        return events

    def _save_run(self, run: PipelineRun) -> None:
        if not self.dry_run:
            self.storage.insert_pipeline_run(run)
