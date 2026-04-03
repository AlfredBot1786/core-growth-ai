"""WARN Act detector — searches EDGAR 8-K filings and state databases for layoff signals."""

from __future__ import annotations

import logging
import re
import time
from datetime import datetime, timedelta, timezone

import httpx

from src.models import Event, EventType
from src.settings import settings

from .base import BaseDetector

logger = logging.getLogger(__name__)


class WarnActDetector(BaseDetector):
    """Detects WARN Act layoff notices from EDGAR and state databases."""

    def __init__(self):
        self.headers = {
            "User-Agent": f"MoneyInMotion/1.0 ({settings.contact_email})",
            "Accept": "application/json",
        }
        self.rate_limit_delay = 1.0 / settings.sec_rate_limit

    def detect(self, lookback_hours: int = 168) -> list[Event]:
        events = []

        # Approach 1: Search EDGAR 8-K filings for workforce reduction language
        try:
            edgar_events = self._search_edgar_warn(lookback_hours)
            events.extend(edgar_events)
            logger.info(f"Found {len(edgar_events)} WARN-related 8-K filings")
        except Exception as e:
            logger.error(f"EDGAR WARN search failed: {e}")

        # Approach 2: Scrape state WARN databases (if target states configured)
        if settings.target_states:
            for state in settings.target_states:
                try:
                    state_events = self._search_state_database(state, lookback_hours)
                    events.extend(state_events)
                    logger.info(f"Found {len(state_events)} WARN notices for {state}")
                except Exception as e:
                    logger.warning(f"State WARN database scrape failed for {state}: {e}")
                    continue

        return events

    def _search_edgar_warn(self, lookback_hours: int) -> list[Event]:
        since = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        date_str = since.strftime("%Y-%m-%d")

        search_terms = [
            '"workforce reduction"',
            '"WARN Act"',
            '"plant closing"',
            '"mass layoff"',
        ]

        all_events = []
        seen_accessions = set()

        for term in search_terms:
            try:
                filings = self._search_edgar(date_str, term)
                for filing in filings:
                    event = self._parse_edgar_filing(filing)
                    if event and event.source_id not in seen_accessions:
                        seen_accessions.add(event.source_id)
                        all_events.append(event)
            except Exception as e:
                logger.warning(f"EDGAR WARN search for '{term}' failed: {e}")
                continue

        return all_events

    def _search_edgar(self, date_from: str, query: str) -> list[dict]:
        def _do_search():
            with httpx.Client(timeout=30) as client:
                response = client.get(
                    "https://efts.sec.gov/LATEST/search-index",
                    params={
                        "q": query,
                        "dateRange": "custom",
                        "startdt": date_from,
                        "forms": "8-K",
                    },
                    headers=self.headers,
                )
                response.raise_for_status()
                data = response.json()
                return data.get("hits", {}).get("hits", [])

        time.sleep(self.rate_limit_delay)
        return self._retry_request(
            _do_search,
            max_attempts=settings.sec_retry_attempts,
            backoff=settings.sec_retry_backoff,
            description=f"EDGAR WARN search: {query}",
        )

    def _parse_edgar_filing(self, filing: dict) -> Event | None:
        source = filing.get("_source", filing)
        accession = source.get("accession_no", "") or source.get("file_num", "")
        if not accession:
            return None

        company_name = source.get("entity_name", "") or source.get("company_name", "")
        filed_str = source.get("file_date", "")
        filed_at = None
        if filed_str:
            try:
                filed_at = datetime.strptime(filed_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                pass

        raw_data = {**source, "signal_type": "workforce_reduction"}

        # Try to extract employee count from filing text
        filing_text = source.get("text", "")
        if filing_text:
            count = self._extract_employee_count(filing_text)
            if count:
                raw_data["affected_employees"] = count

        return Event(
            event_type=EventType.WARN_ACT,
            source_id=f"warn-{accession}",
            company_name=company_name,
            filed_at=filed_at,
            url=source.get("file_url", ""),
            raw_data=raw_data,
        )

    def _extract_employee_count(self, text: str) -> int | None:
        """Extract affected employee count from text using regex patterns."""
        patterns = [
            r"approximately\s+([\d,]+)\s+employees",
            r"([\d,]+)\s+employees?\s+(?:will be|were|are)\s+(?:affected|impacted|terminated|laid off)",
            r"workforce\s+reduction\s+of\s+(?:approximately\s+)?([\d,]+)",
            r"(?:layoff|terminate|reduce)\s+(?:approximately\s+)?([\d,]+)\s+(?:employees|workers|positions)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text[:10000], re.IGNORECASE)
            if match:
                count_str = match.group(1).replace(",", "")
                try:
                    return int(count_str)
                except ValueError:
                    continue
        return None

    def _search_state_database(self, state: str, lookback_hours: int) -> list[Event]:
        """Scrape state WARN Act database.

        State databases have highly variable HTML structures.
        This uses heuristic parsing — may need per-state customization.
        """
        # State WARN database URLs (subset — expand as needed)
        state_urls = {
            "CA": "https://edd.ca.gov/en/jobs_and_training/Layoff_Services_WARN",
            "NY": "https://dol.ny.gov/warn-notices",
            "TX": "https://www.twc.texas.gov/businesses/worker-adjustment-and-retraining-notification-warn-notices",
            "CO": "https://cdle.colorado.gov/employers/layoff-separations/warn-list",
            "FL": "https://floridajobs.org/office-directory/division-of-workforce-services/workforce-programs/reemployment-and-emergency-assistance-coordination-team-react/warn-notices",
        }

        url = state_urls.get(state)
        if not url:
            logger.debug(f"No known WARN database URL for state {state}")
            return []

        try:

            def _fetch():
                with httpx.Client(timeout=30, follow_redirects=True) as client:
                    resp = client.get(url)
                    resp.raise_for_status()
                    return resp.text

            html = self._retry_request(_fetch, max_attempts=2, description=f"State WARN {state}")
            return self._parse_state_html(html, state)

        except Exception as e:
            logger.warning(f"State WARN scrape failed for {state}: {e}")
            return []

    def _parse_state_html(self, html: str, state: str) -> list[Event]:
        """Heuristic HTML parsing for state WARN databases.

        This is intentionally simple — state sites change frequently.
        """
        events = []

        # Look for table rows with company names and dates
        # This is a basic heuristic — production would need per-state parsers
        company_patterns = [
            r"<td[^>]*>([A-Z][^<]{3,60})</td>\s*<td[^>]*>(\d{1,2}/\d{1,2}/\d{2,4})</td>",
            r"<td[^>]*>([A-Z][^<]{3,60})</td>\s*<td[^>]*>([\d,]+)</td>",
        ]

        for pattern in company_patterns:
            for match in re.finditer(pattern, html[:50000]):
                company = match.group(1).strip()
                if len(company) > 3:
                    events.append(
                        Event(
                            event_type=EventType.WARN_ACT,
                            source_id=f"warn-state-{state}-{company[:30]}",
                            company_name=company,
                            raw_data={
                                "signal_type": "state_warn_notice",
                                "state": state,
                            },
                        )
                    )

        return events
