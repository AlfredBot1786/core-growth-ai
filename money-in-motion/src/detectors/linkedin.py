"""LinkedIn job changes detector via Apify."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

import httpx

from src.models import Event, EventType
from src.settings import settings

from .base import BaseDetector

logger = logging.getLogger(__name__)

APIFY_BASE_URL = "https://api.apify.com/v2"


class LinkedInDetector(BaseDetector):
    """Detects LinkedIn job changes using Apify actor runs.

    Scenario fix #13: includes timeout on polling to prevent indefinite hangs.
    """

    def __init__(self):
        if not settings.apify_token:
            logger.info("LinkedIn detector disabled: APIFY_TOKEN not set")

    def detect(self, lookback_hours: int = 168) -> list[Event]:
        if not settings.has_linkedin:
            logger.info("LinkedIn detection skipped: not configured")
            return []

        events = []
        for company_url in settings.target_company_urls:
            try:
                company_events = self._detect_for_company(company_url)
                events.extend(company_events)
            except Exception as e:
                # Per-company error handling — one failure doesn't block others
                logger.warning(f"LinkedIn detection failed for {company_url}: {e}")
                continue

        return events

    def _detect_for_company(self, company_url: str) -> list[Event]:
        """Run Apify actor for a single company and parse results."""
        run_id = self._start_actor(company_url)
        if not run_id:
            return []

        # Scenario fix #13: poll with timeout
        dataset = self._poll_for_completion(run_id)
        if dataset is None:
            logger.warning(f"Apify run {run_id} timed out for {company_url}")
            return []

        return self._parse_results(dataset, company_url)

    def _start_actor(self, company_url: str) -> str | None:
        """Start an Apify actor run for LinkedIn company scraping."""
        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(
                    f"{APIFY_BASE_URL}/acts/anchor~linkedin-company-employees/runs",
                    params={"token": settings.apify_token},
                    json={
                        "startUrls": [{"url": company_url}],
                        "maxItems": 100,
                    },
                )
                response.raise_for_status()
                data = response.json()
                run_id = data.get("data", {}).get("id")
                logger.info(f"Started Apify run {run_id} for {company_url}")
                return run_id
        except Exception as e:
            logger.error(f"Failed to start Apify actor for {company_url}: {e}")
            return None

    def _poll_for_completion(self, run_id: str) -> list[dict] | None:
        """Poll Apify for run completion with timeout.

        Scenario fix #13: prevents indefinite hang if actor gets stuck.
        """
        timeout = settings.apify_timeout_seconds
        poll_interval = 10  # seconds
        elapsed = 0

        while elapsed < timeout:
            try:
                with httpx.Client(timeout=30) as client:
                    response = client.get(
                        f"{APIFY_BASE_URL}/actor-runs/{run_id}",
                        params={"token": settings.apify_token},
                    )
                    response.raise_for_status()
                    data = response.json()

                    status = data.get("data", {}).get("status")
                    if status == "SUCCEEDED":
                        return self._fetch_dataset(run_id)
                    elif status in ("FAILED", "ABORTED", "TIMED-OUT"):
                        logger.error(f"Apify run {run_id} ended with status: {status}")
                        return None

            except Exception as e:
                logger.warning(f"Error polling Apify run {run_id}: {e}")

            time.sleep(poll_interval)
            elapsed += poll_interval

        logger.error(f"Apify run {run_id} timed out after {timeout}s")
        return None

    def _fetch_dataset(self, run_id: str) -> list[dict]:
        """Fetch the dataset from a completed Apify run."""
        try:
            with httpx.Client(timeout=30) as client:
                response = client.get(
                    f"{APIFY_BASE_URL}/actor-runs/{run_id}/dataset/items",
                    params={"token": settings.apify_token},
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch Apify dataset for run {run_id}: {e}")
            return []

    def _parse_results(self, items: list[dict], company_url: str) -> list[Event]:
        """Parse Apify results for job change signals."""
        events = []

        for item in items:
            # Look for recent job changes
            current_title = item.get("title", "")
            name = item.get("name", "") or item.get("fullName", "")
            profile_url = item.get("url", "") or item.get("profileUrl", "")

            if not name:
                continue

            # Check if this person recently changed jobs (new to the company)
            start_date = item.get("startDate", "") or item.get("dateRange", "")
            is_recent = "2026" in str(start_date) or "present" in str(start_date).lower()

            if is_recent:
                company_name = company_url.split("/company/")[-1].rstrip("/")
                events.append(
                    Event(
                        event_type=EventType.LINKEDIN,
                        source_id=f"li-{company_name}-{name[:30]}",
                        person_name=name,
                        company_name=company_name,
                        url=profile_url,
                        raw_data={
                            "job_title": current_title,
                            "linkedin_url": profile_url,
                            "company_url": company_url,
                            "signal_type": "job_change",
                        },
                    )
                )

        return events
