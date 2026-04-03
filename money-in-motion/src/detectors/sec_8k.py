"""SEC 8-K detector for executive departures, restructurings, and M&A events."""

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

# 8-K item types we care about
SIGNAL_ITEMS = {
    "5.02": "executive_departure",
    "2.05": "restructuring",
    "1.01": "merger_acquisition",
    "2.01": "merger_acquisition",
}


class Sec8KDetector(BaseDetector):
    """Detects SEC 8-K filings for executive changes, layoffs, and M&A."""

    def __init__(self):
        self.headers = {
            "User-Agent": f"MoneyInMotion/1.0 ({settings.contact_email})",
            "Accept": "application/json",
        }
        self.rate_limit_delay = 1.0 / settings.sec_rate_limit

    def detect(self, lookback_hours: int = 48) -> list[Event]:
        since = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        date_str = since.strftime("%Y-%m-%d")

        events = []
        for item_code, signal_type in SIGNAL_ITEMS.items():
            try:
                filings = self._search_8k(date_str, item_code)
                logger.info(f"Found {len(filings)} 8-K filings for Item {item_code}")
            except Exception as e:
                logger.error(f"8-K search failed for Item {item_code}: {e}")
                continue

            for filing in filings:
                try:
                    event = self._parse_filing(filing, signal_type, item_code)
                    if event:
                        self._extract_details(event)
                        events.append(event)
                except Exception as e:
                    logger.warning(f"Failed to parse 8-K filing: {e}")
                    continue

        return events

    def _search_8k(self, date_from: str, item_code: str) -> list[dict]:
        def _do_search():
            with httpx.Client(timeout=30) as client:
                response = client.get(
                    "https://efts.sec.gov/LATEST/search-index",
                    params={
                        "q": f'"Item {item_code}"',
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
            description=f"8-K search Item {item_code}",
        )

    def _parse_filing(self, filing: dict, signal_type: str, item_code: str) -> Event | None:
        source = filing.get("_source", filing)
        accession = source.get("accession_no", "") or source.get("file_num", "")
        if not accession:
            return None

        entity_name = source.get("entity_name", "")
        company_name = source.get("company_name", entity_name)
        filed_str = source.get("file_date", "")
        filed_at = None
        if filed_str:
            try:
                filed_at = datetime.strptime(filed_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                pass

        return Event(
            event_type=EventType.SEC_8K,
            source_id=f"8k-{item_code}-{accession}",
            person_name="",  # extracted in _extract_details
            company_name=company_name,
            filed_at=filed_at,
            url=source.get("file_url", ""),
            raw_data={
                **source,
                "signal_type": signal_type,
                "item_code": item_code,
            },
        )

    def _extract_details(self, event: Event) -> None:
        """Extract executive names and employee counts from filing HTML.

        Scenario fix #15: handles unextractable filings gracefully.
        Only uses structured data, not freeform text for scoring.
        """
        filing_url = event.url
        if not filing_url:
            return

        time.sleep(self.rate_limit_delay)

        try:

            def _fetch():
                with httpx.Client(timeout=30) as client:
                    resp = client.get(filing_url, headers=self.headers)
                    resp.raise_for_status()
                    return resp.text

            html = self._retry_request(_fetch, max_attempts=2, description="8-K HTML fetch")

            signal_type = event.raw_data.get("signal_type", "")

            if signal_type == "executive_departure":
                self._extract_executive_names(html, event)
            elif signal_type == "restructuring":
                self._extract_employee_count(html, event)

        except Exception as e:
            logger.debug(f"8-K detail extraction skipped for {event.source_id}: {e}")
            event.raw_data["extraction_failed"] = True

    def _extract_executive_names(self, html: str, event: Event) -> None:
        """Extract executive names from 8-K HTML."""
        # Scenario fix #23: sanitize extracted text — use only structured name patterns
        patterns = [
            r"(?:Mr\.|Ms\.|Mrs\.|Dr\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})",
            r"(?:CEO|CFO|CTO|COO|President|Chairman|Vice President|VP)\s*,?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})",
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})(?:\s*,\s*(?:CEO|CFO|CTO|COO|President|Chairman))",
        ]

        names = set()
        for pattern in patterns:
            for match in re.finditer(pattern, html[:10000]):  # limit scan to first 10k chars
                name = match.group(1).strip()
                if len(name) > 3 and len(name) < 60:  # basic sanity check
                    names.add(name)

        if names:
            event.person_name = list(names)[0]
            event.raw_data["extracted_names"] = list(names)

    def _extract_employee_count(self, html: str, event: Event) -> None:
        """Extract affected employee count from restructuring filings."""
        patterns = [
            r"approximately\s+([\d,]+)\s+employees",
            r"([\d,]+)\s+employees?\s+(?:will be|were|are)\s+(?:affected|impacted|terminated|laid off)",
            r"workforce\s+reduction\s+of\s+(?:approximately\s+)?([\d,]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, html[:10000], re.IGNORECASE)
            if match:
                count_str = match.group(1).replace(",", "")
                try:
                    event.raw_data["affected_employees"] = int(count_str)
                    break
                except ValueError:
                    continue
