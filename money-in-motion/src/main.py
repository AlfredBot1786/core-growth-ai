"""CLI entry point for the Money in Motion pipeline.

Scenario fix #6: cost circuit breakers with configurable limits.
"""

from __future__ import annotations

import argparse
import logging
import sys

from src.pipeline import Pipeline
from src.settings import settings


def main():
    parser = argparse.ArgumentParser(description="Money in Motion — Opportunity Generator")
    parser.add_argument("--run-once", action="store_true", help="Run pipeline once and exit")
    parser.add_argument("--dry-run", action="store_true", help="Detect and score without writing to DB or sending alerts")
    parser.add_argument("--lookback", type=int, default=None, help="Hours to look back for filings")
    parser.add_argument(
        "--detector",
        type=str,
        default="all",
        help="Detector to run: all, sec_form4, sec_8k, warn_act, linkedin",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Validate settings
    errors = settings.validate()
    if errors:
        for error in errors:
            logging.error(f"Config error: {error}")
        if not args.dry_run:
            logging.error("Fix config errors above or use --dry-run to test without API keys")
            sys.exit(1)

    if args.run_once:
        detectors = args.detector.split(",") if args.detector != "all" else None
        pipeline = Pipeline(dry_run=args.dry_run)
        result = pipeline.run(
            lookback_hours=args.lookback,
            detectors=detectors,
        )

        # Print summary
        print(f"\n{'='*60}")
        print(f"Pipeline Run: {result.run_id}")
        print(f"Status: {result.status}")
        print(f"Events detected: {result.events_detected}")
        print(f"Events new: {result.events_new}")
        print(f"T1 (immediate): {result.t1_count}")
        print(f"T2 (sequence): {result.t2_count}")
        print(f"T3 (stored): {result.t3_count}")
        print(f"Alerts sent: {result.alerts_sent}")
        print(f"Est. API cost: ${result.api_cost_estimate:.4f}")
        if result.errors:
            print(f"Errors: {', '.join(result.errors)}")
        if result.enrichment_failures > 0:
            print(f"Enrichment failures: {result.enrichment_failures}")
        if result.scoring_failures > 0:
            print(f"Scoring failures: {result.scoring_failures}")
        print(f"{'='*60}\n")

        sys.exit(0 if result.status.startswith("completed") else 1)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
